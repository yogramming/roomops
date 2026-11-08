import uuid

from sqlalchemy import CheckConstraint, Enum, ForeignKey

from app.extensions import db


class Reservation(db.Model):
    __tablename__ = "reservations"

    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)

    reference = db.Column(db.String(30), unique=True, nullable=False, index=True)

    room_id = db.Column(db.Integer, ForeignKey("rooms.id"), nullable=False)

    check_in = db.Column(db.Date, nullable=False)

    check_out = db.Column(db.Date, nullable=False)

    status = db.Column(
        Enum("CONFIRMED", "CANCELLED", name="reservation_status"),
        nullable=False,
        default="CONFIRMED",
    )

    created_at = db.Column(
        db.DateTime(timezone=True), server_default=db.func.now(), nullable=False
    )

    room = db.relationship("Room", back_populates="reservations")

    __table_args__ = (
        CheckConstraint("check_out > check_in", name="valid_reservation_date_range"),
    )
