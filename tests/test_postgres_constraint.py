from uuid import uuid4

import pytest
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Reservation, Room


def test_database_rejects_overlapping_confirmed_reservations(
    postgres_app,
):
    with postgres_app.app_context():
        room = Room(
            room_number=f"DB-{uuid4().hex[:8]}",
            room_type="deluxe",
            is_active=True,
        )
        db.session.add(room)
        db.session.flush()
        room_id = room.id

        first = Reservation(
            id=uuid4(),
            reference=f"RSV-{uuid4().hex[:12].upper()}",
            room_id=room_id,
            check_in="2030-08-10",
            check_out="2030-08-15",
            status="CONFIRMED",
        )
        db.session.add(first)
        db.session.commit()

        second = Reservation(
            id=uuid4(),
            reference=f"RSV-{uuid4().hex[:12].upper()}",
            room_id=room_id,
            check_in="2030-08-12",
            check_out="2030-08-17",
            status="CONFIRMED",
        )
        db.session.add(second)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()

        db.session.execute(delete(Reservation).where(Reservation.room_id == room_id))
        db.session.execute(delete(Room).where(Room.id == room_id))
        db.session.commit()
