"""Message dispatcher: consume from control queue and route to solver queues"""
import logging
import aio_pika
from src.config import Config

logger = logging.getLogger(__name__)


async def start_dispatcher():
    project_id = Config.Controller.PROJECT_ID
    control_queue = Config.Controller.CONTROL_QUEUE
    solver_types = Config.Solver.TYPES

    if not control_queue:
        raise ValueError("CONTROL_QUEUE environment variable must be set")

    logger.info(f"Starting dispatcher, listening to queue: {control_queue}")

    connection = await aio_pika.connect_robust(
        host=Config.RabbitMQ.HOST,
        port=Config.RabbitMQ.PORT,
        login=Config.RabbitMQ.USER,
        password=Config.RabbitMQ.PASSWORD,
    )

    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)

    queue = await channel.declare_queue(control_queue, durable=True)

    async def process_message(message: aio_pika.IncomingMessage):
        async with message.process():
            body = message.body.decode('utf-8')

            solver_type = solver_types[0]
            solver_queue_name = f"project-{project_id}-solver-{solver_type}"

            await channel.declare_queue(solver_queue_name, durable=True)
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=body.encode('utf-8'),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=solver_queue_name,
            )

            logger.info(f"Routed message to {solver_queue_name}: {body}")

    await queue.consume(process_message)
    logger.info("Dispatcher ready, waiting for messages")
