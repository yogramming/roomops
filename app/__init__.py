import logging
from importlib import import_module

from flask import Flask

from app.config import Config
from app.errors import register_error_handlers
from app.extensions import db, migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    # Register models with SQLAlchemy and Alembic.
    import_module("app.models")

    from app.metrics import metrics_bp, record_request, start_timer

    # Register API blueprints.
    from app.routes.availability import availability_bp
    from app.routes.health import health_bp
    from app.routes.reservations import reservations_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(
        availability_bp,
        url_prefix="/api/v1/rooms",
    )
    app.register_blueprint(
        reservations_bp,
        url_prefix="/api/v1/reservations",
    )
    app.before_request(start_timer)
    app.after_request(record_request)
    register_error_handlers(app)
    log_level = app.config.get("LOG_LEVEL", "INFO")
    app.logger.setLevel(getattr(logging, log_level, logging.INFO))

    return app
