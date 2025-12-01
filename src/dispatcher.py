from __future__ import annotations
from dataclasses import asdict, dataclass
import json
import logging
import aio_pika
from src.config import Config
import httpx
from kubernetes import client
from kubernetes.client.rest import ApiException
from src.spawner import (
    create_solver_deployment_manifest,
    create_keda_scaled_object_manifest,
)


@dataclass
class InputSolveRequest:
    problem_id: int
    instance_id: int
    solver_id: int
    vcpus: int

    def from_dict(request: dict) -> InputSolveRequest:
        logger.info(f"request: {request}")
        return InputSolveRequest(
            problem_id=request["problem_id"],
            instance_id=request["instance_id"],
            solver_id=request["solver_id"],
            vcpus=request["vcpus"],
        )


@dataclass
class OutputSolveRequest:
    solver_id: int
    solver_name: str
    problem_id: int
    instance_id: int
    problem_url: str
    instance_url: str


logger = logging.getLogger(__name__)


async def start_dispatcher():
    controller_queue = Config.Controller.CONTROL_QUEUE

    logger.info(f"Starting dispatcher, listening to queue: {controller_queue}")

    connection = await aio_pika.connect_robust(
        host=Config.RabbitMQ.HOST,
        port=Config.RabbitMQ.PORT,
        login=Config.RabbitMQ.USER,
        password=Config.RabbitMQ.PASSWORD,
    )

    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(controller_queue, durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    logger.info("Received request message")
                    result_data = message.body.decode()
                    request = InputSolveRequest.from_dict(json.loads(result_data))
                    await process_request(channel, request)




async def process_request(
    channel: aio_pika.abc.AbstractRobustChannel, request: InputSolveRequest
):
    solver_name, solver_image_url = await get_solver_info(request.solver_id)
    solver_request = OutputSolveRequest(
        solver_id=request.solver_id,
        solver_name=solver_name,
        problem_id=request.problem_id,
        instance_id=request.instance_id,
        problem_url=problem_url(request.problem_id),
        instance_url=instance_url(request.problem_id, request.instance_id),
    )
    solver_request_body = json.dumps(asdict(solver_request)).encode()

    queue_name = solver_queue_name(request.solver_id, request.vcpus)
    await channel.declare_queue(queue_name, durable=True)
    await channel.default_exchange.publish(
        aio_pika.Message(
            body=solver_request_body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ),
        routing_key=queue_name,
    )

    logger.info(f"Routed message to {queue_name}: {solver_request_body}")
    
    deploy_solver(solver_name, solver_image_url, Config.Controller.SOLVERS_NAMESPACE, queue_name, Config.Controller.PROJECT_SOLVER_RESULT_QUEUE)
    



def deploy_solver(solver_type: str, solver_image_url: str, solvers_namespace: str, queue_in_name: str, queue_out_name: str) -> bool:

    logger.info(f"Deploying solver: {solver_type} in namespace: {solvers_namespace}")

    deployment_manifest = create_solver_deployment_manifest(
        solver_type=solver_type,
        solvers_namespace=solvers_namespace,
        solver_image=solver_image_url,
        pod_cpu_request=1,
        queue_in_name=queue_in_name,
        queue_out_name=queue_out_name,
    )

    apps_v1 = client.AppsV1Api()
    try:
        apps_v1.create_namespaced_deployment(
            namespace=solvers_namespace, body=deployment_manifest
        )
        logger.info(f"✓ Created Deployment: solver-{solver_type}")
    except ApiException as e:
        if e.status == 409:
            logger.warning(f"⚠ Deployment solver-{solver_type} already exists")
        else:
            logger.error(f"✗ Failed to create Deployment: {e}")
            return False

    scaled_object_manifest = create_keda_scaled_object_manifest(
        solver_type=solver_type,
        solvers_namespace=solvers_namespace,
        queue_name=queue_in_name,
    )

    custom_api = client.CustomObjectsApi()
    try:
        custom_api.create_namespaced_custom_object(
            group="keda.sh",
            version="v1alpha1",
            namespace=solvers_namespace,
            plural="scaledobjects",
            body=scaled_object_manifest,
        )
        logger.info(f"✓ Created ScaledObject: solver-{solver_type}-scaler")
        logger.info(f"  Queue: {queue_in_name}")
    except ApiException as e:
        if e.status == 409:
            logger.warning(f"⚠ ScaledObject solver-{solver_type}-scaler already exists")
        else:
            logger.error(f"✗ Failed to create ScaledObject: {e}")
            return False

    return True


def solver_url(solver_id: int) -> str:
    return f"{Config.SolverDirector.SOLVERS_URL}/{solver_id}"


def problem_url(problem_id: int) -> str:
    return f"{Config.SolverDirector.PROBLEMS_URL}/{problem_id}/file"


def instance_url(problem_id: int,instance_id: int) -> str:
    return f"{Config.SolverDirector.PROBLEMS_URL}/{problem_id}/instances/{instance_id}/file"


async def make_get_request(url: str) -> httpx.Response:
    timeout = httpx.Timeout(10.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        return await client.get(url)


async def get_solver_info(solver_id: int) -> tuple[str, str]:
    response = await make_get_request(solver_url(solver_id))
    response.raise_for_status()
    response = response.json()
    return response["name"], response["image_path"]


def solver_queue_name(solver_id: int, vcpus: int) -> str:
    return f"project-{Config.Controller.PROJECT_ID}-solver-{solver_id}-vcpus-{vcpus}"

