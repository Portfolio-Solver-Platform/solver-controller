from flask import Blueprint, jsonify
from src.config import Config
import requests
from requests.exceptions import ConnectionError

health_bp = Blueprint("health", __name__)


@health_bp.route("/healthz")
def healthz():
    return jsonify(status="ok")


@health_bp.route("/readyz")
def readyz():
    status = "ready"
    return jsonify(status=status)
    # if is_keycloak_ready():
    #     status = "ready"
    # else:
    #     status = "not ready"
    # return jsonify(status=status)


# def is_keycloak_ready() -> bool:
#     response = try_get_keycloak_ready_response()
#     if response is None:
#         return False

#     data = response.json()
#     return data["status"] == "UP"


# def try_get_keycloak_ready_response() -> requests.Response | None:
#     url = f"http://{Config.Keycloak.HOST}/health/ready"
#     try:
#         return requests.get(url, timeout=Config.Keycloak.Timeout.READINESS)
#     except ConnectionError:
#         return None
