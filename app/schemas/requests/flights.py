from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.models.flight import FlightStatus, FlightTheme


class PilotSubmission(BaseModel):
    username: str | None = Field(
        default=None, description="Public username / nickname for the pilot"
    )
    name: str | None = Field(default=None, description="Display name")
    email: EmailStr | None = Field(default=None)
    instagram: str | None = Field(default=None)
    youtube: str | None = Field(default=None)
    website: str | None = Field(default=None)

    @property
    def social_links(self) -> dict[str, str]:
        links: dict[str, str] = {}
        if self.instagram:
            links["instagram"] = self.instagram
        if self.youtube:
            links["youtube"] = self.youtube
        if self.website:
            links["website"] = self.website
        return links


class FlightSubmissionRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)

    pilot: PilotSubmission | None = Field(
        default=None,
        description="Optional pilot information; if omitted the flight is anonymous.",
    )

    drone_type: str | None = Field(default=None)
    tags: list[str] | None = Field(
        default=None, description="List of tags, e.g. ['urban', 'night']"
    )
    theme: FlightTheme | None = Field(default=None)
    duration_seconds: int | None = Field(default=None, ge=0)

    title: str | None = Field(default=None)
    description: str | None = Field(default=None)

    country_code: str | None = Field(
        default=None,
        min_length=2,
        max_length=2,
        description="ISO 3166-1 alpha-2 country code (optional; can be derived later).",
    )


class FlightUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    drone_type: str | None = None
    duration_seconds: int | None = Field(default=None, ge=0)
    theme: FlightTheme | None = None
    tags: list[str] | None = None
    credits: int | None = Field(default=None, ge=0)
    status: FlightStatus | None = None
    rejected_reason: str | None = None
    pilot_id: int | None = None
