from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
import pika
from src.config import Config

router = APIRouter()


class StatusResponse(BaseModel):
    isFinished: bool = Field(..., description="Is it finished generating data")
    messages: list[str] = Field(default_factory=list, description="Messages from queue")


@router.get("/status", response_model=StatusResponse)
def get_status(queue_name: str = Query(..., description="Queue name (solver_controller_id)")):
    """Retrieve messages from RabbitMQ queue"""
    messages = []

    credentials = pika.PlainCredentials(Config.RabbitMQ.USER, Config.RabbitMQ.PASSWORD)
    parameters = pika.ConnectionParameters(
        host=Config.RabbitMQ.HOST,
        port=Config.RabbitMQ.PORT,
        credentials=credentials
    )

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # Declare queue (idempotent)
    channel.queue_declare(queue=queue_name, durable=True)

    # Get all messages from queue (non-blocking)
    while True:
        method_frame, header_frame, body = channel.basic_get(queue=queue_name, auto_ack=True)
        if method_frame:
            messages.append(body.decode('utf-8'))
        else:
            break

    connection.close()

    return StatusResponse(
        isFinished=len(messages) == 0,  # Finished if no more messages
        messages=messages
    )
