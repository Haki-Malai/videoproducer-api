from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Response, status

from app.controllers.flight import FlightController
from app.models import Role
from app.models.flight import FlightStatus, FlightTheme
from app.schemas.requests.flights import FlightSubmissionRequest, FlightUpdateRequest
from app.schemas.responses.flights import FlightResponse
from core.factory import Factory
from core.fastapi.dependencies import AuthenticationRequired
from core.security.require_role import require_role

flights_router = APIRouter(prefix="/flights", tags=["Flights"])


def _parse_bbox(bbox: str | None) -> tuple[float, float, float, float] | None:
    if not bbox:
        return None
    parts = bbox.split(",")
    if len(parts) != 4:
        raise ValueError("bbox must be 'min_lng,min_lat,max_lng,max_lat'")
    min_lng, min_lat, max_lng, max_lat = map(float, parts)
    return min_lng, min_lat, max_lng, max_lat


@flights_router.post(
    "",
    response_model=FlightResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(AuthenticationRequired), Depends(require_role(Role.MODERATOR))],
)
async def submit_flight(
    payload: FlightSubmissionRequest,
    flight_controller: FlightController = Depends(Factory().get_flight_controller),
) -> FlightResponse:
    flight = await flight_controller.submit_flight(payload)
    return flight


@flights_router.get(
    "",
    response_model=list[FlightResponse],
)
async def list_flights(
    bbox: str | None = Query(
        None,
        description="Bounding box as 'min_lng,min_lat,max_lng,max_lat'",
    ),
    country: str | None = Query(None),
    drone_type: str | None = Query(None),
    theme: FlightTheme | None = Query(None),
    pilot_name: str | None = Query(None),
    tags: str | None = Query(
        None, description="Comma-separated list of tags to require"
    ),
    duration_min: int | None = Query(None, ge=0),
    duration_max: int | None = Query(None, ge=0),
    q: str | None = Query(
        None,
        description="Free-text search over title and description",
    ),
    status_: FlightStatus = Query(
        FlightStatus.APPROVED,
        alias="status",
        description="Flight status to filter on",
    ),
    limit: int = Query(500, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    flight_controller: FlightController = Depends(Factory().get_flight_controller),
) -> list[FlightResponse]:
    filters: dict[str, Any] = {
        "country": country,
        "drone_type": drone_type,
        "theme": theme,
        "pilot_name": pilot_name,
        "duration_min": duration_min,
        "duration_max": duration_max,
        "q": q,
        "status": status_,
    }

    if tags:
        filters["tags"] = [t.strip() for t in tags.split(",") if t.strip()]

    bbox_tuple = _parse_bbox(bbox) if bbox else None

    flights = await flight_controller.list_public(
        bbox=bbox_tuple, filters=filters, limit=limit, offset=offset
    )
    return list(flights)


@flights_router.get(
    "/{flight_id}",
    response_model=FlightResponse,
)
async def get_flight(
    flight_id: int,
    flight_controller: FlightController = Depends(Factory().get_flight_controller),
) -> FlightResponse:
    return await flight_controller.get_by_id(flight_id)


@flights_router.put(
    "/{flight_id}",
    response_model=FlightResponse,
    dependencies=[Depends(AuthenticationRequired), Depends(require_role(Role.MODERATOR))],
)
async def update_flight(
    flight_id: int,
    payload: FlightUpdateRequest,
    flight_controller: FlightController = Depends(Factory().get_flight_controller),
) -> FlightResponse:
    attributes = payload.model_dump(exclude_unset=True)
    flight = await flight_controller.update_flight(flight_id, attributes)
    return flight


@flights_router.delete(
    "/{flight_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=[Depends(AuthenticationRequired), Depends(require_role(Role.MODERATOR))],
)
async def delete_flight(
    flight_id: int,
    flight_controller: FlightController = Depends(Factory().get_flight_controller),
) -> Response:
    await flight_controller.delete(flight_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
