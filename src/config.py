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
        HOST = os.getenv("RABBITMQ_HOST")
        PORT = int(os.getenv("RABBITMQ_PORT"))
        USER = os.getenv("RABBITMQ_USER")
        PASSWORD = os.getenv("RABBITMQ_PASSWORD")

    class Solver:
        POD_MEMORY_REQUEST = 2
        QUEUE_LENGTH_PER_REPLICA = int(float(os.getenv("KEDA_QUEUE_LENGTH", "1")))
        MIN_REPLICAS = 0
        IMAGE = os.getenv("SOLVER_IMAGE")
        # TYPES = [s.strip() for s in os.getenv("SOLVER_TYPES", "chuffed").split(",") if s.strip()] # solver types from env vars, which is a comma-separated string

    class Controller:
        PROJECT_ID = os.getenv("PROJECT_ID")
        SOLVERS_NAMESPACE = os.getenv("SOLVERS_NAMESPACE")
        CONTROL_QUEUE = os.getenv("CONTROL_QUEUE")
        MAX_TOTAL_SOLVER_REPLICAS = int(float(os.getenv("MAX_TOTAL_SOLVER_REPLICAS")))
