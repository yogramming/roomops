from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.extensions import db
from app.models import Reservation, Room


@pytest.fixture
def postgres_room(postgres_app):
    with postgres_app.app_context():
        room = Room(
            room_number=f"TEST-{uuid4().hex[:8]}",
            room_type="deluxe",
            is_active=True,
        )
        db.session.add(room)
        db.session.commit()

        room_number = room.room_number

        yield room_number

        db.session.execute(db.delete(Reservation).where(Reservation.room_id == room.id))
        db.session.delete(room)
        db.session.commit()


def test_concurrent_overlapping_reservations(
    postgres_app,
    postgres_room,
):
    def make_reservation():
        with postgres_app.test_client() as client:
            return client.post(
                "/api/v1/reservations",
                json={
                    "room_number": postgres_room,
                    "check_in": "2030-06-10",
                    "check_out": "2030-06-15",
                },
            )

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(make_reservation) for _ in range(2)]
        responses = [future.result() for future in futures]

    statuses = sorted(response.status_code for response in responses)

    assert statuses == [201, 409]

    with postgres_app.app_context():
        room = db.session.scalar(select(Room).where(Room.room_number == postgres_room))

        reservations = db.session.scalars(
            select(Reservation).where(
                Reservation.room_id == room.id,
                Reservation.status == "CONFIRMED",
            )
        ).all()

        assert len(reservations) == 1


def test_non_overlapping_reservations_both_succeed(
    postgres_client,
    postgres_room,
):
    first = postgres_client.post(
        "/api/v1/reservations",
        json={
            "room_number": postgres_room,
            "check_in": "2030-07-10",
            "check_out": "2030-07-15",
        },
    )

    second = postgres_client.post(
        "/api/v1/reservations",
        json={
            "room_number": postgres_room,
            "check_in": "2030-07-15",
            "check_out": "2030-07-20",
        },
    )

    assert first.status_code == 201
    assert second.status_code == 201
