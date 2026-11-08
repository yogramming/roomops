from datetime import date

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from app.extensions import db
from app.models import Reservation, Room

availability_bp = Blueprint("availability", __name__)


@availability_bp.get("/availability")
def check_availability():
    check_in_raw = request.args.get("check_in")
    check_out_raw = request.args.get("check_out")
    room_type = request.args.get("room_type")

    if not check_in_raw or not check_out_raw:
        return jsonify(
            {
                "error": "validation_error",
                "message": "check_in and check_out are required",
            }
        ), 400

    try:
        check_in = date.fromisoformat(check_in_raw)
        check_out = date.fromisoformat(check_out_raw)
    except ValueError:
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

    overlapping_reservations = select(Reservation.room_id).where(
        Reservation.status == "CONFIRMED",
        Reservation.check_in < check_out,
        Reservation.check_out > check_in,
    )

    query = select(Room).where(
        Room.is_active.is_(True),
        Room.id.not_in(overlapping_reservations),
    )

    if room_type:
        query = query.where(Room.room_type.ilike(room_type))

    rooms = db.session.scalars(query.order_by(Room.room_number)).all()

    return jsonify(
        {
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "room_type": room_type,
            "count": len(rooms),
            "rooms": [
                {
                    "room_number": room.room_number,
                    "room_type": room.room_type,
                }
                for room in rooms
            ],
        }
    ), 200
