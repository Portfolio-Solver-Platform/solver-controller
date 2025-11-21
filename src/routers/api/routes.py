from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
import aio_pika
from src.config import Config

router = APIRouter()


class StatusResponse(BaseModel):
    isFinished: bool = Field(..., description="Is it finished generating data")
    messages: list[str] = Field(default_factory=list, description="Messages from queue")


@router.get("/status", response_model=StatusResponse)
async def get_status(
    queue_name: str = Query(..., description="Queue name (solver_controller_id)"),
):
    messages = []

    connection = await aio_pika.connect_robust(
        host=Config.RabbitMQ.HOST,
        port=Config.RabbitMQ.PORT,
        login=Config.RabbitMQ.USER,
        password=Config.RabbitMQ.PASSWORD,
    )

    channel = await connection.channel()
    queue = await channel.declare_queue(queue_name, durable=True)

    while True:
        message = await queue.get(no_ack=True, timeout=0.1)
        if message:
            messages.append(message.body.decode("utf-8"))
        else:
            break

    await connection.close()

    return StatusResponse(
        isFinished=len(messages) == 0,
        messages=messages,
    )
