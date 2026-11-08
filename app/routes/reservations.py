from datetime import date
from uuid import uuid4

from flask import Blueprint, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.extensions import db
from app.models import Reservation, Room

reservations_bp = Blueprint("reservations", __name__)


def generate_reference():
    return f"RSV-{uuid4().hex[:12].upper()}"


@reservations_bp.post("")
def create_reservation():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(
            {
                "error": "validation_error",
                "message": "A valid JSON object is required",
            }
        ), 400

    required_fields = ("room_number", "check_in", "check_out")

    missing_fields = [field for field in required_fields if not data.get(field)]

    if missing_fields:
        return jsonify(
            {
                "error": "validation_error",
                "message": "Required fields are missing",
                "fields": missing_fields,
            }
        ), 400

    try:
        check_in = date.fromisoformat(data["check_in"])
        check_out = date.fromisoformat(data["check_out"])
    except (TypeError, ValueError):
        return jsonify(
            {
                "error": "validation_error",
                "message": "Dates must use YYYY-MM-DD format",
            }
        ), 400

    if check_out <= check_in:
        return jsonify(
            {
                "error": "validation_error",
                "message": "check_out must be after check_in",
            }
        ), 400

    room = db.session.scalar(
        select(Room).where(
            Room.room_number == data["room_number"],
            Room.is_active.is_(True),
        )
    )

    if room is None:
        return jsonify(
            {
                "error": "room_not_found",
                "message": "The requested room does not exist or is inactive",
            }
        ), 404

    reservation = Reservation(
        id=uuid4(),
        reference=generate_reference(),
        room_id=room.id,
        check_in=check_in,
        check_out=check_out,
        status="CONFIRMED",
    )

    try:
        db.session.add(reservation)
        db.session.commit()

    except IntegrityError as error:
        db.session.rollback()

        original_error = error.orig
        sqlstate = getattr(original_error, "sqlstate", None)

        if sqlstate == "23P01":
            return jsonify(
                {
                    "error": "reservation_conflict",
                    "message": "The room is already reserved for these dates",
                }
            ), 409

        return jsonify(
            {
                "error": "integrity_error",
                "message": "The reservation could not be created",
            }
        ), 409

    except SQLAlchemyError:
        db.session.rollback()

        return jsonify(
            {
                "error": "database_error",
                "message": "The reservation could not be processed",
            }
        ), 500

    return jsonify(
        {
            "message": "Reservation created successfully",
            "reservation": {
                "reference": reservation.reference,
                "room_number": room.room_number,
                "check_in": reservation.check_in.isoformat(),
                "check_out": reservation.check_out.isoformat(),
                "status": reservation.status,
            },
        }
    ), 201


@reservations_bp.get("/<string:reference>")
def get_reservation(reference):
    reservation = db.session.scalar(
        select(Reservation).where(Reservation.reference == reference)
    )

    if reservation is None:
        return jsonify(
            {
                "error": "reservation_not_found",
                "message": "Reservation not found",
            }
        ), 404

    return jsonify(
        {
            "reservation": {
                "reference": reservation.reference,
                "room_number": reservation.room.room_number,
                "room_type": reservation.room.room_type,
                "check_in": reservation.check_in.isoformat(),
                "check_out": reservation.check_out.isoformat(),
                "status": reservation.status,
                "created_at": reservation.created_at.isoformat()
                if reservation.created_at
                else None,
            },
        }
    ), 200
