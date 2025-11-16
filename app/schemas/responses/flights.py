from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.flight import FlightStatus, FlightTheme
from .base import BaseResponse


class PilotSummary(BaseModel):
    id: int | None = Field(default=None)
    username: str | None = Field(default=None)
    display_name: str | None = Field(default=None)
    country_code: str | None = Field(default=None)
    email: str | None = Field(default=None)

    class Config:
        from_attributes = True


class FlightResponse(BaseResponse):
    status: FlightStatus
    video_url: str

    title: str | None = None
    description: str | None = None

    lat: float
    lng: float
    country_code: str | None = None

    drone_type: str | None = None
    duration_seconds: int | None = None
    theme: FlightTheme | None = None
    tags: list[str] = Field(default_factory=list)

    credits: int
    views: int
    likes: int

    approved_at: datetime | None = None
    rejected_reason: str | None = None

    pilot: PilotSummary | None = None

    class Config:
        from_attributes = True


class FlightSummary(BaseModel):
    id: int
    title: str | None = None
    video_url: str
    lat: float
    lng: float
    country_code: str | None = None
    drone_type: str | None = None
    theme: FlightTheme | None = None
    created_at: datetime

    class Config:
        from_attributes = True
