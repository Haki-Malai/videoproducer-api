from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from app.controllers.flight import FlightController
from app.models import Role
from app.models.flight import FlightStatus
from app.schemas.responses.flights import FlightResponse
from core.factory import Factory
from core.fastapi.dependencies import AuthenticationRequired
from core.security.require_role import require_role

admin_router = APIRouter(prefix="/admin", tags=["Admin"])


class ApprovePayload(BaseModel):
    credits: int | None = Field(default=None, ge=0)


class RejectPayload(BaseModel):
    reason: str | None = None


@admin_router.get(
    "/flights",
    dependencies=[Depends(AuthenticationRequired), Depends(require_role(Role.MODERATOR))],
    response_model=list[FlightResponse],
)
async def list_admin_flights(
    status_: FlightStatus | None = Query(None, alias="status"),
    country: str | None = Query(None),
    pilot_name: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    flight_controller: FlightController = Depends(Factory().get_flight_controller),
) -> list[FlightResponse]:
    filters = {
        "status": status_,
        "country": country,
        "pilot_name": pilot_name,
    }
    flights = await flight_controller.list_public(
        bbox=None, filters=filters, limit=limit, offset=offset
    )
    return list(flights)


@admin_router.post(
    "/flights/{flight_id}/approve",
    dependencies=[Depends(AuthenticationRequired), Depends(require_role(Role.MODERATOR))],
    response_model=FlightResponse,
)
async def approve_flight(
    flight_id: int,
    payload: ApprovePayload,
    flight_controller: FlightController = Depends(Factory().get_flight_controller),
) -> FlightResponse:
    flight = await flight_controller.approve(flight_id, payload.credits)
    return flight


@admin_router.post(
    "/flights/{flight_id}/reject",
    dependencies=[Depends(AuthenticationRequired), Depends(require_role(Role.MODERATOR))],
    response_model=FlightResponse,
)
async def reject_flight(
    flight_id: int,
    payload: RejectPayload,
    flight_controller: FlightController = Depends(Factory().get_flight_controller),
) -> FlightResponse:
    flight = await flight_controller.reject(flight_id, payload.reason)
    return flight


@admin_router.get(
    "/stats/overview",
    dependencies=[Depends(AuthenticationRequired), Depends(require_role(Role.MODERATOR))],
)
async def stats_overview(
    start: date = Query(..., description="Start date inclusive"),
    end: date = Query(..., description="End date exclusive"),
    metric: str = Query(
        "flights",
        pattern="^(flights|credits|views)$",
    ),
    top_limit: int = Query(5, ge=1, le=50),
    flight_controller: FlightController = Depends(Factory().get_flight_controller),
) -> dict:
    metric = flight_controller.validate_metric(metric)
    return await flight_controller.stats_overview(
        start=start, end=end, metric=metric, top_limit=top_limit
    )
