from datetime import date

from app.extensions import db
from app.models import Reservation, Room


def seed_rooms():
    rooms = [
        Room(room_number="101", room_type="Deluxe", is_active=True),
        Room(room_number="102", room_type="Deluxe", is_active=True),
        Room(room_number="201", room_type="Standard", is_active=True),
        Room(room_number="301", room_type="Suite", is_active=False),
    ]

    db.session.add_all(rooms)
    db.session.flush()

    reservation = Reservation(
        reference="RSV-TEST-0001",
        room_id=rooms[0].id,
        check_in=date(2030, 5, 10),
        check_out=date(2030, 5, 13),
        status="CONFIRMED",
    )

    db.session.add(reservation)
    db.session.commit()


def test_availability_returns_only_available_rooms(client, app):
    with app.app_context():
        seed_rooms()

    response = client.get(
        "/api/v1/rooms/availability",
        query_string={
            "check_in": "2030-05-11",
            "check_out": "2030-05-14",
        },
    )

    assert response.status_code == 200
    assert response.json["count"] == 2

    room_numbers = [room["room_number"] for room in response.json["rooms"]]

    assert "101" not in room_numbers
    assert "102" in room_numbers
    assert "201" in room_numbers
    assert "301" not in room_numbers


def test_availability_respects_checkout_boundary(client, app):
    with app.app_context():
        seed_rooms()

    response = client.get(
        "/api/v1/rooms/availability",
        query_string={
            "check_in": "2030-05-13",
            "check_out": "2030-05-16",
        },
    )

    assert response.status_code == 200

    room_numbers = [room["room_number"] for room in response.json["rooms"]]

    assert "101" in room_numbers


def test_availability_filters_by_room_type(client, app):
    with app.app_context():
        seed_rooms()

    response = client.get(
        "/api/v1/rooms/availability",
        query_string={
            "check_in": "2030-05-10",
            "check_out": "2030-05-12",
            "room_type": "Standard",
        },
    )

    assert response.status_code == 200
    assert response.json["count"] == 1
    assert response.json["rooms"][0]["room_type"] == "Standard"


def test_availability_requires_dates(client):
    response = client.get("/api/v1/rooms/availability")

    assert response.status_code == 400
    assert response.json["error"] == "validation_error"


def test_availability_rejects_invalid_date_range(client):
    response = client.get(
        "/api/v1/rooms/availability",
        query_string={
            "check_in": "2030-05-15",
            "check_out": "2030-05-10",
        },
    )

    assert response.status_code == 400
    assert response.json["error"] == "validation_error"


def test_availability_rejects_invalid_date_format(client):
    response = client.get(
        "/api/v1/rooms/availability",
        query_string={
            "check_in": "15-05-2030",
            "check_out": "2030-05-20",
        },
    )

    assert response.status_code == 400
    assert response.json["error"] == "validation_error"
