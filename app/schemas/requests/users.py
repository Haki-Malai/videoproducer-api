import re
from datetime import date

from pydantic import BaseModel, constr, field_validator

from app.models import Role
from core.exceptions import BadRequestException


class BaseUserRequest(BaseModel):
    username: str

    @field_validator("username")
    def username_must_not_contain_special_characters(cls, v):
        if v is not None and re.search(r"[^a-zA-Z0-9]", v):
            raise BadRequestException("Username must not contain special characters")
        return v


class RegisterUserRequest(BaseUserRequest):
    password: constr(min_length=8, max_length=64)


class UpdateUserRequest(BaseUserRequest):
    username: constr(min_length=3, max_length=64) | None = None
    role: Role | None = None
    password: constr(min_length=8, max_length=64) | None = None


class UpdateSelfRequest(BaseUserRequest):
    username: constr(min_length=3, max_length=64) | None = None
    password: constr(min_length=8, max_length=64) | None = None


class UserPagination(BaseModel):
    skip: int = 0
    limit: int = 10
    creation_year: int | None = None

    @field_validator("creation_year")
    def validate_year(cls, v):
        current_year = date.today().year
        if v is not None and (v > current_year or v < 1900):
            raise BadRequestException("Invalid year")
        return v
