from dataclasses import asdict, dataclass
import json
import logging
import aio_pika
from src.config import Config


@dataclass
class InputSolveRequest:
    problem_id: int
    instance_id: int
    solver_id: int
    vcpus: int


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
    project_id = Config.Controller.PROJECT_ID
    controller_queue = Config.Controller.CONTROL_QUEUE
    solver_types = Config.Solver.TYPES

    logger.info(f"Starting dispatcher, listening to queue: {controller_queue}")

    connection = await aio_pika.connect_robust(
        host=Config.RabbitMQ.HOST,
        port=Config.RabbitMQ.PORT,
        login=Config.RabbitMQ.USER,
        password=Config.RabbitMQ.PASSWORD,
    )

    async def process_message(message: aio_pika.IncomingMessage):
        async with message.process():
            body = message.body.decode("utf-8")

            solver_type = solver_types[0]
            solver_queue_name = f"project-{project_id}-solver-{solver_type}"

            await channel.declare_queue(solver_queue_name, durable=True)
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=body.encode("utf-8"),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=solver_queue_name,
            )

            logger.info(f"Routed message to {solver_queue_name}: {body}")

    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(controller_queue, durable=True)
        exchange = channel.default_exchange

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    logger.info("Received request message")
                    result_data = message.body.decode()
                    result_json = json.loads(result_data)
                    result = await process_message(result_json)
                    response = OutputSolveRequest(
                        project_id=project_id,
                        solver_id=result_json["solver_id"],
                        problem_id=result_json["problem_id"],
                        instance_id=result_json["instance_id"],
                    )
                    response = asdict(response)

                    for request in result.requests:
                        body = json.dumps(asdict(request)).encode()

                        await exchange.publish(
                            aio_pika.Message(
                                body=body,
                                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                            ),
                            routing_key=controller_queue,
                        )
