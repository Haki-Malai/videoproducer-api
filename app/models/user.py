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
