from datetime import date

from app.extensions import db
from app.models import Reservation, Room


def seed_room(room_number="101", room_type="deluxe", is_active=True):
    room = Room(
        room_number=room_number,
        room_type=room_type,
        is_active=is_active,
    )
    db.session.add(room)
    db.session.commit()
    return room


def test_create_reservation_success(client, app):
    with app.app_context():
        seed_room()

    response = client.post(
        "/api/v1/reservations",
        json={
            "room_number": "101",
            "check_in": "2030-06-10",
            "check_out": "2030-06-13",
        },
    )

    assert response.status_code == 201
    assert response.json["message"] == "Reservation created successfully"

    reservation = response.json["reservation"]

    assert reservation["room_number"] == "101"
    assert reservation["check_in"] == "2030-06-10"
    assert reservation["check_out"] == "2030-06-13"
    assert reservation["status"] == "CONFIRMED"
    assert reservation["reference"].startswith("RSV-")


def test_create_reservation_requires_json(client):
    response = client.post("/api/v1/reservations")

    assert response.status_code == 400
    assert response.json["error"] == "validation_error"


def test_create_reservation_requires_fields(client):
    response = client.post(
        "/api/v1/reservations",
        json={"room_number": "101"},
    )

    assert response.status_code == 400
    assert response.json["error"] == "validation_error"
    assert set(response.json["fields"]) == {"check_in", "check_out"}


def test_create_reservation_rejects_invalid_dates(client, app):
    with app.app_context():
        seed_room()

    response = client.post(
        "/api/v1/reservations",
        json={
            "room_number": "101",
            "check_in": "2030-06-15",
            "check_out": "2030-06-10",
        },
    )

    assert response.status_code == 400
    assert response.json["error"] == "validation_error"


def test_create_reservation_rejects_unknown_room(client):
    response = client.post(
        "/api/v1/reservations",
        json={
            "room_number": "999",
            "check_in": "2030-06-10",
            "check_out": "2030-06-13",
        },
    )

    assert response.status_code == 404
    assert response.json["error"] == "room_not_found"


def test_create_reservation_rejects_inactive_room(client, app):
    with app.app_context():
        seed_room(is_active=False)

    response = client.post(
        "/api/v1/reservations",
        json={
            "room_number": "101",
            "check_in": "2030-06-10",
            "check_out": "2030-06-13",
        },
    )

    assert response.status_code == 404
    assert response.json["error"] == "room_not_found"


def test_create_reservation_rejects_non_object_json(client):
    response = client.post(
        "/api/v1/reservations",
        json=["not", "an", "object"],
    )

    assert response.status_code == 400
    assert response.json["error"] == "validation_error"
