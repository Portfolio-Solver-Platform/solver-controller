from flask import Blueprint, jsonify

route_bp = Blueprint("route", __name__)


@route_bp.route("/")
def test_route():
    return jsonify(status="test")
