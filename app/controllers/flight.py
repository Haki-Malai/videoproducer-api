from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime
from typing import Any

from app.models.flight import Flight, FlightStatus
from app.repositories.flights import FlightRepository
from app.repositories.pilots import PilotRepository
from app.schemas.requests.flights import FlightSubmissionRequest
from app.tasks.flights import process_new_flight
from core.controller import BaseController
from core.exceptions import BadRequestException
from core.repository import BaseRepository


class FlightController(BaseController[Flight]):
    def __init__(
        self,
        flight_repository: FlightRepository,
        pilot_repository: PilotRepository,
    ):
        super().__init__(model=Flight, repository=flight_repository)
        self.flight_repository = flight_repository
        self.pilot_repository = pilot_repository

    async def submit_flight(self, payload: FlightSubmissionRequest) -> Flight:
        pilot = None
        if payload.pilot:
            pilot = await self.pilot_repository.get_or_create(
                username=payload.pilot.username,
                email=payload.pilot.email,
                display_name=payload.pilot.name,
                country_code=payload.country_code,
                social=payload.pilot.social_links,
            )

        video_provider = self._detect_video_provider(str(payload.video_url))

        attributes: dict[str, Any] = {
            "pilot_id": pilot.id if pilot else None,
            "status": FlightStatus.PENDING,
            "video_url": str(payload.video_url),
            "video_provider": video_provider,
            "title": payload.title,
            "description": payload.description,
            "lat": payload.lat,
            "lng": payload.lng,
            "country_code": payload.country_code,
            "drone_type": payload.drone_type,
            "duration_seconds": payload.duration_seconds,
            "theme": payload.theme,
            "tags": payload.tags or [],
        }

        flight = await self.repository.create(attributes)

        # Background processing (metadata, thumbnails, stats, etc.)
        process_new_flight.delay(flight.id)

        return flight

    async def list_public(
        self,
        bbox: tuple[float, float, float, float] | None,
        filters: dict[str, object] | None,
        limit: int,
        offset: int,
    ) -> Sequence[Flight]:
        return await self.flight_repository.list_public(
            bbox=bbox, filters=filters, limit=limit, offset=offset
        )

    async def list_by_pilot(self, pilot_id: int) -> Sequence[Flight]:
        return await self.flight_repository.list_by_pilot(pilot_id)

    async def approve(self, flight_id: int, credits: int | None) -> Flight:
        flight = await self.get_by_id(flight_id)
        if flight.status == FlightStatus.APPROVED:
            return flight

        flight.status = FlightStatus.APPROVED
        flight.approved_at = datetime.utcnow()
        if credits is not None:
            flight.credits = credits

        if flight.pilot_id:
            pilot = await self.pilot_repository.get_by(
                field="id", value=flight.pilot_id, unique=True
            )
            if pilot:
                pilot.total_credits = (pilot.total_credits or 0) + flight.credits
                self.flight_repository.session.add(pilot)

        self.flight_repository.session.add(flight)
        await self.flight_repository.session.commit()
        return flight

    async def reject(self, flight_id: int, reason: str | None) -> Flight:
        flight = await self.get_by_id(flight_id)
        flight.status = FlightStatus.REJECTED
        flight.rejected_reason = reason
        self.flight_repository.session.add(flight)
        await self.flight_repository.session.commit()
        return flight

    async def stats_overview(
        self,
        start: date,
        end: date,
        metric: str,
        top_limit: int,
    ) -> dict[str, object]:
        if start > end:
            raise BadRequestException("Start date must be before end date")

        metric = self.validate_metric(metric)

        flights_per_day = await self.flight_repository.flights_per_day(start, end)

        start_dt = datetime.combine(start, datetime.min.time())
        end_dt = datetime.combine(end, datetime.min.time())

        top_countries = await self.flight_repository.top_countries(
            metric=metric, start=start_dt, end=end_dt, limit=top_limit
        )
        top_pilots = await self.flight_repository.top_pilots(
            country_code=None,
            metric=metric,
            start=start_dt,
            end=end_dt,
            limit=top_limit,
        )

        pending = await self.flight_repository.get_filtered(
            filters={"status": FlightStatus.PENDING},
            skip=0,
            limit=1_000_000,
        )

        return {
            "flights_per_day": flights_per_day,
            "top_countries": top_countries,
            "top_pilots": top_pilots,
            "pending_flights": len(pending),
        }

    def validate_metric(self, metric: str) -> str:
        allowed = {"flights", "credits", "views"}
        if metric not in allowed:
            raise BadRequestException(
                f"Invalid metric '{metric}'. Allowed: {', '.join(sorted(allowed))}"
            )
        return metric

    def _detect_video_provider(self, url: str) -> str:
        lower = url.lower()
        if "youtube.com" in lower or "youtu.be" in lower:
            return "youtube"
        if "vimeo.com" in lower:
            return "vimeo"
        return "other"
