from __future__ import annotations

import sqlalchemy as sa
import sqlalchemy.orm as so

from core.database import Base
from core.database.mixins import TimestampMixin


class Pilot(Base, TimestampMixin):
    __tablename__ = "pilots"

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True, index=True)
    display_name: so.Mapped[str | None] = so.mapped_column(sa.String(128))
    email: so.Mapped[str | None] = so.mapped_column(sa.String(256), index=True)
    country_code: so.Mapped[str | None] = so.mapped_column(sa.String(2), index=True)
    total_credits: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)

    instagram_url: so.Mapped[str | None] = so.mapped_column(sa.String(256))
    youtube_url: so.Mapped[str | None] = so.mapped_column(sa.String(256))
    website_url: so.Mapped[str | None] = so.mapped_column(sa.String(256))

    flights: so.Mapped[list["Flight"]] = so.relationship(
        "Flight", back_populates="pilot", lazy="selectin"
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Pilot {self.username}>"
