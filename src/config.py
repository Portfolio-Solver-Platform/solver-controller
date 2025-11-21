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

    class Solver:
        POD_CPU_REQUEST = float(os.getenv("SOLVER_CPU_REQUEST", "1"))  # CPUs per pod
        POD_MEMORY_REQUEST = float(os.getenv("SOLVER_MEMORY_REQUEST", "2"))  # GB per pod
        QUEUE_LENGTH_PER_REPLICA = int(os.getenv("KEDA_QUEUE_LENGTH", "20"))  # Messages per pod
        MIN_REPLICAS = int(os.getenv("KEDA_MIN_REPLICAS", "0"))  # Scale to zero
        IMAGE = os.getenv("SOLVER_IMAGE", "harbor.local/psp/minizinc-solver:latest")
        TYPES = [s.strip() for s in os.getenv("SOLVER_TYPES", "chuffed").split(",") if s.strip()] # solver types from env vars, which is a comma-separated string

    class Controller:
        PROJECT_ID = os.getenv("PROJECT_ID")
        SOLVERS_NAMESPACE = os.getenv("SOLVERS_NAMESPACE")
        CONTROL_QUEUE = os.getenv("CONTROL_QUEUE")
        MAX_TOTAL_SOLVER_REPLICAS = int(os.getenv("MAX_TOTAL_SOLVER_REPLICAS", "10"))
