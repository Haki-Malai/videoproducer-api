from __future__ import annotations

from pydantic import BaseModel


class PilotLeaderboardEntry(BaseModel):
    pilot_id: int
    username: str | None = None
    display_name: str | None = None
    country_code: str | None = None
    rank: int
    metric_value: int
    flights_count: int
    total_credits: int
    total_views: int


class CountryLeaderboardEntry(BaseModel):
    country_code: str | None
    rank: int
    metric_value: int
    flights_count: int
    unique_pilots: int
    total_credits: int
    total_views: int
