from flask import Blueprint
from src.blueprints.api.route import route_bp

api_bp = Blueprint("api", __name__)

api_bp.register_blueprint(route_bp)
