from __future__ import annotations
from dataclasses import asdict, dataclass
import json
import logging
import aio_pika
from src.config import Config
import httpx


@dataclass
class InputSolveRequest:
    problem_id: int
    instance_id: int
    solver_id: int
    vcpus: int

    def from_dict(request: dict) -> InputSolveRequest:
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
    solver_request = OutputSolveRequest(
        solver_id=request.solver_id,
        solver_name=await get_solver_name(request.solver_id),
        problem_id=request.problem_id,
        instance_id=request.instance_id,
        problem_url=problem_url(request.problem_id),
        instance_url=instance_url(request.instance_id),
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


def solver_url(solver_id: int) -> str:
    return f"{Config.SolverDirector.SOLVERS_URL}/{solver_id}"


def problem_url(problem_id: int) -> str:
    return f"{Config.SolverDirector.PROBLEMS_URL}/{problem_id}"


def instance_url(instance_id: int) -> str:
    return f"{Config.SolverDirector.INSTANCES_URL}/{instance_id}"


async def make_get_request(url: str) -> httpx.Response:
    timeout = httpx.Timeout(10.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        return await client.get(url)


async def get_solver_name(solver_id: int) -> str:
    response = make_get_request(solver_url(solver_id))
    response.raise_for_status()
    return response.json()["name"]


def solver_queue_name(solver_id: int, vcpus: int) -> str:
    return f"project-{Config.Controller.PROJECT_ID}-solver-{solver_id}-vcpus-{vcpus}"
