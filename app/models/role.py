import enum


class Role(enum.IntEnum):
    USER: int = 1
    PILOT: int = 2
    MODERATOR: int = 3
    ADMIN: int = 4
