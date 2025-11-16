from fastapi import APIRouter

from .health import health_router
from .tokens import tokens_router
from .users import users_router
from .flights import flights_router
from .countries import countries_router
from .leaderboards import leaderboards_router

v1_router = APIRouter()
v1_router.include_router(health_router)
v1_router.include_router(tokens_router)
v1_router.include_router(users_router)
v1_router.include_router(flights_router)
v1_router.include_router(countries_router)
v1_router.include_router(leaderboards_router)
