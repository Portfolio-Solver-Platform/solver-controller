import logging
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from src.config import Config
from src.spawner import (
    create_solver_deployment_manifest,
    create_keda_scaled_object_manifest,
)

logger = logging.getLogger(__name__)


def deploy_solver(solver_type: str, solvers_namespace: str, project_id: str) -> bool:
    queue_name = f"project-{project_id}-solver-{solver_type}"

    logger.info(f"Deploying solver: {solver_type} in namespace: {solvers_namespace}")

    deployment_manifest = create_solver_deployment_manifest(
        solver_type=solver_type,
        solvers_namespace=solvers_namespace,
        solver_image=Config.Solver.IMAGE,
        queue_name=queue_name,
    )

    apps_v1 = client.AppsV1Api()
    try:
        apps_v1.create_namespaced_deployment(
            namespace=solvers_namespace,
            body=deployment_manifest
        )
        logger.info(f"✓ Created Deployment: solver-{solver_type}")
    except ApiException as e:
        if e.status == 409:
            logger.warning(f"⚠ Deployment solver-{solver_type} already exists")
        else:
            logger.error(f"✗ Failed to create Deployment: {e}")
            return False

    scaled_object_manifest = create_keda_scaled_object_manifest(
        solver_type=solver_type,
        solvers_namespace=solvers_namespace,
        queue_name=queue_name,
    )

    custom_api = client.CustomObjectsApi()
    try:
        custom_api.create_namespaced_custom_object(
            group="keda.sh",
            version="v1alpha1",
            namespace=solvers_namespace,
            plural="scaledobjects",
            body=scaled_object_manifest
        )
        logger.info(f"✓ Created ScaledObject: solver-{solver_type}-scaler")
        logger.info(f"  Queue: {queue_name}")
    except ApiException as e:
        if e.status == 409:
            logger.warning(f"⚠ ScaledObject solver-{solver_type}-scaler already exists")
        else:
            logger.error(f"✗ Failed to create ScaledObject: {e}")
            return False

    return True


def deploy_all_solvers():
    project_id = Config.Controller.PROJECT_ID
    solvers_namespace = Config.Controller.SOLVERS_NAMESPACE
    solver_types = Config.Solver.TYPES

    logger.info(f"Initializing solver-controller for project: {project_id}")
    logger.info(f"Solver types to deploy: {solver_types}")

    config.load_incluster_config()

    success_count = 0
    for solver_type in solver_types:
        if deploy_solver(solver_type, solvers_namespace, project_id):
            success_count += 1

    logger.info(f"Deployed {success_count}/{len(solver_types)} solvers successfully")
