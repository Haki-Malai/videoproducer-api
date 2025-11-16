from __future__ import annotations

from collections.abc import Sequence

from app.models.pilot import Pilot
from app.repositories.flights import FlightRepository
from app.repositories.pilots import PilotRepository
from core.controller import BaseController
from core.exceptions import NotFoundException


class PilotController(BaseController[Pilot]):
    def __init__(
        self,
        pilot_repository: PilotRepository,
        flight_repository: FlightRepository,
    ):
        super().__init__(model=Pilot, repository=pilot_repository)
        self.pilot_repository = pilot_repository
        self.flight_repository = flight_repository

    async def get_by_username(self, username: str) -> Pilot:
        pilot = await self.pilot_repository.get_by_username(username)
        if not pilot:
            raise NotFoundException(
                f"Pilot with username '{username}' does not exist"
            )
        return pilot

    async def get_profile_with_flights(self, username: str) -> tuple[Pilot, Sequence]:
        pilot = await self.get_by_username(username)
        flights = await self.flight_repository.list_by_pilot(pilot.id)
        return pilot, flights
