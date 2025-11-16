import enum


class Role(enum.Enum):
    ADMIN: int = 3
    MODERATOR: int = 2
    USER: int = 1
