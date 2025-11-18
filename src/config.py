import os


class Config:
    class App:
        NAME = "solver-controller"
        VERSION = "0.1.0"
        DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    class Api:
        TITLE = "Solver Controller API"
        DESCRIPTION = "Manages solver and instances"
        VERSION = "v1"
        ROOT_PATH = "/"

    class RabbitMQ:
        HOST = os.getenv("RABBITMQ_HOST", "rabbitmq.rabbit-mq.svc.cluster.local")
        PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
        USER = os.getenv("RABBITMQ_USER", "guest")
        PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
