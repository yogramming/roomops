from app.extensions import db


class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)

    room_number = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    room_type = db.Column(
        db.String(50),
        nullable=False,
        index=True
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    reservations = db.relationship(
        "Reservation",
        back_populates="room"
    )
