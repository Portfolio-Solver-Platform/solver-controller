"""Helper functions to create solver Deployments and KEDA ScaledObjects"""
from kubernetes import client
from src.config import Config


def create_solver_deployment_manifest(
    solver_type: str,
    solvers_namespace: str,
    solver_image: str,
    queue_name: str,
    pod_cpu_request: int,
) -> dict:
    deployment_name = f"solver-{solver_type}"

    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": deployment_name,
            "namespace": solvers_namespace,
            "labels": {
                "app": "minizinc-solver",
                "solver-type": solver_type,
            },
        },
        "spec": {
            "replicas": 0,  # Start with 0, pod-scheduler will scale up
            "selector": {
                "matchLabels": {
                    "app": "minizinc-solver",
                    "solver-type": solver_type,
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": "minizinc-solver",
                        "solver-type": solver_type,
                    }
                },
                "spec": {
                    "imagePullSecrets": [{"name": "harbor-creds"}],
                    "securityContext": {
                        "runAsNonRoot": True,
                        "seccompProfile": {"type": "RuntimeDefault"},
                    },
                    "containers": [
                        {
                            "name": "solver",
                            "image": solver_image,
                            "imagePullPolicy": "IfNotPresent",
                            "env": [
                                {"name": "SOLVER_TYPE", "value": solver_type},
                                {"name": "QUEUE_NAME", "value": queue_name},
                                {"name": "RABBITMQ_HOST", "value": Config.RabbitMQ.HOST},
                                {"name": "RABBITMQ_PORT", "value": str(Config.RabbitMQ.PORT)},
                                {"name": "RABBITMQ_USER", "value": Config.RabbitMQ.USER},
                                {"name": "RABBITMQ_PASSWORD", "value": Config.RabbitMQ.PASSWORD},
                            ],
                            "resources": {
                                "requests": {
                                    "cpu": str(pod_cpu_request),
                                    "memory": f"{Config.Solver.POD_MEMORY_REQUEST}Gi"
                                },
                                "limits": {
                                    "cpu": str(pod_cpu_request),
                                    "memory": f"{Config.Solver.POD_MEMORY_REQUEST}Gi"
                                },
                            },
                            "securityContext": {
                                "allowPrivilegeEscalation": False,
                                "readOnlyRootFilesystem": True,
                                "capabilities": {"drop": ["ALL"]},
                            },
                        }
                    ],
                },
            },
        },
    }


def create_keda_scaled_object_manifest(
    solver_type: str,
    solvers_namespace: str,
    queue_name: str,
) -> dict:
    deployment_name = f"solver-{solver_type}"
    scaled_object_name = f"solver-{solver_type}-scaler"
    max_replicas = Config.Controller.MAX_TOTAL_SOLVER_REPLICAS

    return {
        "apiVersion": "keda.sh/v1alpha1",
        "kind": "ScaledObject",
        "metadata": {
            "name": scaled_object_name,
            "namespace": solvers_namespace,
            "labels": {
                "app": "minizinc-solver",
                "solver-type": solver_type,
            },
        },
        "spec": {
            "scaleTargetRef": {
                "name": deployment_name,
            },
            "minReplicaCount": Config.Solver.MIN_REPLICAS,
            "maxReplicaCount": max_replicas,
            "pollingInterval": 1,
            "cooldownPeriod": 2,
            "triggers": [
                {
                    "type": "rabbitmq",
                    "metadata": {
                        "host": f"amqp://{Config.RabbitMQ.USER}:{Config.RabbitMQ.PASSWORD}@{Config.RabbitMQ.HOST}:{Config.RabbitMQ.PORT}/",
                        "queueName": queue_name,
                        "mode": "QueueLength",
                        "value": str(Config.Solver.QUEUE_LENGTH_PER_REPLICA),
                    },
                }
            ],
        },
    }
