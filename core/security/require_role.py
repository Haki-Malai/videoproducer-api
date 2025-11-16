from fastapi import Depends

from app.models import Role
from app.schemas.responses import UserResponse
from core.exceptions import ForbiddenException
from core.fastapi.dependencies import get_current_user


def require_role(required_role: Role):
    def role_checker(current_user: UserResponse = Depends(get_current_user)):
        if current_user.role.value < required_role.value:
            raise ForbiddenException("Insufficient permissions")
        return current_user

    return role_checker
