from datetime import datetime

from fastapi import APIRouter, Depends, status

from app.controllers import UserController
from app.models import Role, User
from app.schemas.requests import (
    RegisterUserRequest,
    UpdateSelfRequest,
    UpdateUserRequest,
    UserPagination,
)
from app.schemas.responses import UserResponse
from core.factory import Factory
from core.fastapi.dependencies import AuthenticationRequired, get_current_user
from core.security.require_role import require_role

users_router = APIRouter(tags=["Users"])


@users_router.post(
    "/users",
    dependencies=[
        Depends(AuthenticationRequired),
        Depends(require_role(Role.MODERATOR)),
    ],
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user_request: RegisterUserRequest,
    user_controller: UserController = Depends(Factory().get_user_controller),
):
    return await user_controller.create(user_request.dict())


@users_router.get(
    "/users",
    dependencies=[Depends(AuthenticationRequired)],
    response_model=list[UserResponse],
)
async def get_users(
    query_params: UserPagination = Depends(),
    user_controller: UserController = Depends(Factory().get_user_controller),
):
    filters = {}
    if query_params.creation_year:
        start_date = datetime(query_params.creation_year, 1, 1)
        end_date = datetime(query_params.creation_year + 1, 1, 1)
        filters["created_at"] = (start_date, end_date)

    return await user_controller.get_filtered(
        filters=filters, skip=query_params.skip, limit=query_params.limit
    )


@users_router.get(
    "/users/{user_id}",
    dependencies=[Depends(AuthenticationRequired)],
    response_model=UserResponse,
)
async def get_user_by_id(
    user_id: int,
    user_controller: UserController = Depends(Factory().get_user_controller),
):
    return await user_controller.get_by_id(user_id)


@users_router.get(
    "/users/search/",
    dependencies=[Depends(AuthenticationRequired)],
    response_model=list[UserResponse],
)
async def search_users_by_username(
    query: str, user_controller: UserController = Depends(Factory().get_user_controller)
):
    return await user_controller.search_by_username(query)


@users_router.put(
    "/users/{user_id}",
    dependencies=[
        Depends(AuthenticationRequired),
        Depends(require_role(Role.MODERATOR)),
    ],
    response_model=UserResponse,
)
async def update_user(
    user_id: int,
    user_request: UpdateUserRequest,
    user_controller: UserController = Depends(Factory().get_user_controller),
):
    return await user_controller.update(user_id, user_request.dict())


@users_router.delete(
    "/users/{user_id}",
    dependencies=[Depends(AuthenticationRequired), Depends(require_role(Role.ADMIN))],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: int,
    user_controller: UserController = Depends(Factory().get_user_controller),
):
    return await user_controller.delete(user_id)


@users_router.get(
    "/me", dependencies=[Depends(AuthenticationRequired)], response_model=UserResponse
)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@users_router.put(
    "/me", dependencies=[Depends(AuthenticationRequired)], response_model=UserResponse
)
async def update_me(
    user_request: UpdateSelfRequest,
    user_controller: UserController = Depends(Factory().get_user_controller),
    current_user: UserResponse = Depends(get_current_user),
):
    return await user_controller.update(current_user.id, user_request.dict())


@users_router.delete(
    "/me",
    dependencies=[Depends(AuthenticationRequired)],
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_me(
    user_controller: UserController = Depends(Factory().get_user_controller),
    current_user: UserResponse = Depends(get_current_user),
):
    return await user_controller.delete(current_user.id)
