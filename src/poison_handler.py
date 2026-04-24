from __future__ import annotations
import asyncio
import json
import logging
import aio_pika
from src.config import Config

logger = logging.getLogger(__name__)

_spawned: set[str] = set()


def ensure_dlq_consumer(
    connection: aio_pika.abc.AbstractRobustConnection,
    queue_in_name: str,
) -> None:
    if queue_in_name in _spawned:
        return
    _spawned.add(queue_in_name)
    asyncio.create_task(_dlq_consumer(connection, queue_in_name))


async def _dlq_consumer(
    connection: aio_pika.abc.AbstractRobustConnection,
    queue_in_name: str,
) -> None:
    queue_out_name = Config.Controller.PROJECT_SOLVER_RESULT_QUEUE
    dlq_name = f"{queue_in_name}.dlq"
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)
    dlq = await channel.declare_queue(dlq_name, durable=True, arguments={"x-queue-type": "quorum"})
    logger.info(f"DLQ consumer started for {dlq_name}")

    async with dlq.iterator() as queue_iter:
        async for message in queue_iter:
            try:
                body = json.loads(message.body.decode())
                error_result = {
                    "solver_id": body["solver_id"],
                    "vcpus": -1,
                    "problem_id": body["problem_id"],
                    "instance_id": body["instance_id"],
                    "result": {
                        "kind": "error",
                        "error_message": "solver crashed (likely OOM or consumer timeout)",
                    },
                    "version": 1,
                }
                await channel.default_exchange.publish(
                    aio_pika.Message(
                        body=json.dumps(error_result).encode(),
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    ),
                    routing_key=queue_out_name,
                )
                await message.ack()
                logger.warning(
                    f"Published error result for poison message in {queue_in_name}: "
                    f"solver_id={body.get('solver_id')}, problem_id={body.get('problem_id')}, "
                    f"instance_id={body.get('instance_id')}"
                )
            except Exception:
                logger.exception(f"Failed to handle DLQ message in {dlq_name}")
                await message.nack(requeue=True)
