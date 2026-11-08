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

    # Register API blueprints.
    from app.routes.availability import availability_bp
    from app.routes.health import health_bp
    from app.routes.reservations import reservations_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(
        availability_bp,
        url_prefix="/api/v1/rooms",
    )
    app.register_blueprint(
        reservations_bp,
        url_prefix="/api/v1/reservations",
    )
    register_error_handlers(app)
    log_level = app.config.get("LOG_LEVE", "INFO")
    app.logger.setLevel(getattr(logging, log_level, logging.INFO))

    return app
