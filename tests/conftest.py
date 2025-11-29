import os
import pytest
from fastapi.testclient import TestClient

# Set environment variables for tests before importing app
os.environ.setdefault("RABBITMQ_HOST", "localhost")
os.environ.setdefault("RABBITMQ_PORT", "5672")
os.environ.setdefault("RABBITMQ_USER", "guest")
os.environ.setdefault("RABBITMQ_PASSWORD", "guest")
os.environ.setdefault("SOLVER_IMAGE", "test-solver:latest")
os.environ.setdefault("PROJECT_ID", "test-project")
os.environ.setdefault("SOLVERS_NAMESPACE", "test-namespace")
os.environ.setdefault("CONTROL_QUEUE", "test-control-queue")
os.environ.setdefault("MAX_TOTAL_SOLVER_REPLICAS", "10")

from src.main import app


@pytest.fixture
def client():
    """Test client"""
    with TestClient(app) as client:
        yield client
