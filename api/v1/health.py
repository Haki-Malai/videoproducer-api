from fastapi import APIRouter

from app.schemas.extras import Health
from core.config import config

health_router = APIRouter(prefix="/health", tags=["Health"])


@health_router.get("")
async def health() -> Health:
    """Health check endpoint.

    :returns: The health check response.
    """
    return Health(version=config.RELEASE_VERSION, status="OK")
