from __future__ import annotations

import sqlalchemy as sa
import sqlalchemy.orm as so

from core.database import Base
from core.database.mixins import TimestampMixin
from core.security import password_handler

from .role import Role


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True, index=True)
    password_hash: so.Mapped[str] = so.mapped_column(sa.String(256))
    role: so.Mapped[Role] = so.mapped_column(sa.Enum(Role), default=Role.USER)

    display_name: so.Mapped[str | None] = so.mapped_column(sa.String(128))
    email: so.Mapped[str | None] = so.mapped_column(sa.String(256), unique=True, index=True)
    country_code: so.Mapped[str | None] = so.mapped_column(sa.String(2), index=True)
    total_credits: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)

    instagram_url: so.Mapped[str | None] = so.mapped_column(sa.String(256))
    youtube_url: so.Mapped[str | None] = so.mapped_column(sa.String(256))
    website_url: so.Mapped[str | None] = so.mapped_column(sa.String(256))

    flights: so.Mapped[list["Flight"]] = so.relationship(
        "Flight", back_populates="pilot", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"

    @property
    def password(self):
        raise AttributeError("Password is not a readable attribute")

    @password.setter
    def password(self, password: str):
        self.password_hash = password_handler.generate_password_hash(password)

    def verify_password(self, password: str) -> bool:
        return password_handler.check_password_hash(self.password_hash, password)
