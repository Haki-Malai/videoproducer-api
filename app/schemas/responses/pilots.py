from __future__ import annotations

from pydantic import Field

from .base import BaseResponse
from .flights import FlightSummary


class PilotProfileResponse(BaseResponse):
    username: str = Field(..., description="Public pilot username")
    display_name: str | None = None
    email: str | None = None
    country_code: str | None = None
    total_credits: int = 0

    instagram_url: str | None = None
    youtube_url: str | None = None
    website_url: str | None = None

    flights: list[FlightSummary] = Field(default_factory=list)

    class Config:
        from_attributes = True
