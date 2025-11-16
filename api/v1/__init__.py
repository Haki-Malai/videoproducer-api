from fastapi import APIRouter

from .health import health_router
from .tokens import tokens_router
from .users import users_router

v1_router = APIRouter()
v1_router.include_router(health_router)
v1_router.include_router(tokens_router)
v1_router.include_router(users_router)
