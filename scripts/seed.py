from datetime import date

from sqlalchemy import select

from app import create_app
from app.extensions import db
from app.models import Reservation, Room


app = create_app()

SEED_ROOMS = [
    {"room_number": "101", "room_type": "deluxe"},
    {"room_number": "102", "room_type": "deluxe"},
    {"room_number": "201", "room_type": "standard"},
    {"room_number": "202", "room_type": "standard"},
    {"room_number": "301", "room_type": "suite"},
]


def seed_database():
    with app.app_context():
        for room_data in SEED_ROOMS:
            existing_room = db.session.execute(
                select(Room).where(Room.room_number == room_data["room_number"])
            ).scalar_one_or_none()

            if existing_room is None:
                db.session.add(Room(**room_data))

        db.session.flush()

        existing_reservation = db.session.execute(
            select(Reservation).where(Reservation.reference == "RSV-SEED-0001")
        ).scalar_one_or_none()

        room = db.session.execute(
            select(Room).where(Room.room_number == "101")
        ).scalar_one()

        if existing_reservation is None:
            db.session.add(
                Reservation(
                    reference="RSV-SEED-0001",
                    room_id=room.id,
                    check_in=date(2030, 5, 10),
                    check_out=date(2030, 5, 13),
                    status="CONFIRMED",
                )
            )

        db.session.commit()

        print("Database seeding completed successfully.")


if __name__ == "__main__":
    seed_database()
