from fastapi import APIRouter

from .health import health_router
from .tokens import tokens_router
from .users import users_router
from .flights import flights_router
from .pilots import pilots_router
from .countries import countries_router
from .leaderboards import leaderboards_router
from .admin import admin_router
from .uploads import uploads_router

v1_router = APIRouter()
v1_router.include_router(health_router)
v1_router.include_router(tokens_router)
v1_router.include_router(users_router)
v1_router.include_router(flights_router)
v1_router.include_router(pilots_router)
v1_router.include_router(countries_router)
v1_router.include_router(leaderboards_router)
v1_router.include_router(admin_router)
v1_router.include_router(uploads_router)
