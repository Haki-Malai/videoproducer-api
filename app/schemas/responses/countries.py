from __future__ import annotations

from pydantic import BaseModel, Field


class CountryStatsResponse(BaseModel):
    code: str = Field(..., description="ISO 3166-1 alpha-2 code")
    name: str | None = Field(default=None)
    flag_url: str | None = Field(default=None)
    total_flights: int
    total_pilots: int
    total_credits: int
    total_views: int


class CountryDetailResponse(CountryStatsResponse):
    recent_flights: int
    top_pilots: list[dict] = Field(
        default_factory=list, description="Top pilots for this country"
    )
    bounding_box: list[float] | None = Field(
        default=None, description="[min_lng, min_lat, max_lng, max_lat]"
    )
