from __future__ import annotations

import enum
from datetime import datetime

import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.dialects.postgresql import ARRAY

from core.database import Base
from core.database.mixins import TimestampMixin


class FlightStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class FlightTheme(str, enum.Enum):
    URBAN = "urban"
    RACING = "racing"
    MOUNTAIN = "mountain"
    FREESTYLE = "freestyle"
    OTHER = "other"


class Flight(Base, TimestampMixin):
    __tablename__ = "flights"

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    pilot_id: so.Mapped[int | None] = so.mapped_column(
        sa.Integer, sa.ForeignKey("pilots.id"), nullable=True, index=True
    )

    status: so.Mapped[FlightStatus] = so.mapped_column(
        sa.Enum(FlightStatus, name="flight_status"),
        default=FlightStatus.PENDING,
        index=True,
    )

    video_url: so.Mapped[str] = so.mapped_column(sa.String(512))
    video_provider: so.Mapped[str] = so.mapped_column(sa.String(32))

    title: so.Mapped[str | None] = so.mapped_column(sa.String(200))
    description: so.Mapped[str | None] = so.mapped_column(sa.Text)

    lat: so.Mapped[float] = so.mapped_column(sa.Float, index=True)
    lng: so.Mapped[float] = so.mapped_column(sa.Float, index=True)
    country_code: so.Mapped[str | None] = so.mapped_column(sa.String(2), index=True)

    drone_type: so.Mapped[str | None] = so.mapped_column(sa.String(64), index=True)
    duration_seconds: so.Mapped[int | None] = so.mapped_column(sa.Integer)

    theme: so.Mapped[FlightTheme | None] = so.mapped_column(
        sa.Enum(FlightTheme, name="flight_theme"), nullable=True, index=True
    )

    tags: so.Mapped[list[str]] = so.mapped_column(
        ARRAY(sa.String(64)),
        default=list,
    )

    credits: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)
    views: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)
    likes: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)

    approved_at: so.Mapped[datetime | None] = so.mapped_column(sa.DateTime)
    rejected_reason: so.Mapped[str | None] = so.mapped_column(sa.String(255))

    pilot: so.Mapped["Pilot | None"] = so.relationship(
        "Pilot", back_populates="flights", lazy="joined"
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Flight {self.id} status={self.status}>"
