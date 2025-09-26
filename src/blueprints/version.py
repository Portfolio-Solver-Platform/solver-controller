from flask import Blueprint, jsonify
from src.config import Config

version_bp = Blueprint("version", __name__)


@version_bp.route("/version", methods=["GET"])
def version():
    return jsonify(
        service=Config.App.NAME,
        version=Config.App.VERSION,
        api_version=Config.Api.VERSION,
    )
