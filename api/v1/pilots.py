from __future__ import annotations

from fastapi import APIRouter, Depends

from app.controllers.pilot import PilotController
from app.schemas.responses.pilots import PilotProfileResponse
from core.factory import Factory

pilots_router = APIRouter(prefix="/pilots", tags=["Pilots"])


@pilots_router.get(
    "/{username}",
    response_model=PilotProfileResponse,
)
async def get_pilot_profile(
    username: str,
    pilot_controller: PilotController = Depends(Factory().get_pilot_controller),
) -> PilotProfileResponse:
    pilot, flights = await pilot_controller.get_profile_with_flights(username)
    return PilotProfileResponse(
        id=pilot.id,
        created_at=pilot.created_at,
        updated_at=pilot.updated_at,
        username=pilot.username,
        display_name=pilot.display_name,
        email=pilot.email,
        country_code=pilot.country_code,
        total_credits=pilot.total_credits,
        instagram_url=pilot.instagram_url,
        youtube_url=pilot.youtube_url,
        website_url=pilot.website_url,
        flights=flights,
    )
