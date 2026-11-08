from flask import Blueprint, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "roomops"
    }), 200


@health_bp.get("/ready")
def readiness():
    try:
        db.session.execute(text("SELECT 1"))

        return jsonify({
            "status": "ready",
            "database": "connected"
        }), 200

    except SQLAlchemyError:
        db.session.rollback()

        return jsonify({
            "status": "not_ready",
            "database": "unavailable"
        }), 503
