from flask import Flask
from .config import Config
from .blueprints.health import health_bp
from .blueprints.metrics import metrics_bp
from .blueprints.version import version_bp
from .blueprints.api import api_bp


def create_app():
    app = Flask(__name__)

    app.register_blueprint(health_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(version_bp)
    app.register_blueprint(api_bp, url_prefix=f"/{Config.Api.VERSION}")

    return app
