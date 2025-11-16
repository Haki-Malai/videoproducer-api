from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, Query

from app.controllers.flight import FlightController
from app.schemas.responses.countries import CountryDetailResponse, CountryStatsResponse
from core.factory import Factory

countries_router = APIRouter(prefix="/countries", tags=["Countries"])

# Minimal static metadata – extend as needed.
COUNTRY_NAMES: dict[str, str] = {
    "GR": "Greece",
    "US": "United States",
    "DE": "Germany",
}

COUNTRY_FLAGS: dict[str, str] = {
    "GR": "https://flagcdn.com/gr.svg",
    "US": "https://flagcdn.com/us.svg",
    "DE": "https://flagcdn.com/de.svg",
}


def _enrich_country_row(row: dict) -> CountryStatsResponse:
    code = (row.get("country_code") or "").upper()
    return CountryStatsResponse(
        code=code,
        name=COUNTRY_NAMES.get(code),
        flag_url=COUNTRY_FLAGS.get(code),
        total_flights=row.get("flights_count", 0),
        total_pilots=row.get("unique_pilots", 0),
        total_credits=row.get("total_credits", 0),
        total_views=row.get("total_views", 0),
    )


@countries_router.get(
    "",
    response_model=list[CountryStatsResponse],
)
async def list_countries(
    metric: str = Query(
        "flights",
        pattern="^(flights|credits|views)$",
    ),
    period_start: date | None = Query(None),
    period_end: date | None = Query(None),
    limit: int = Query(200, ge=1, le=300),
    flight_controller: FlightController = Depends(Factory().get_flight_controller),
) -> list[CountryStatsResponse]:
    metric = flight_controller.validate_metric(metric)
    start_dt = (
        None
        if period_start is None
        else datetime.combine(period_start, datetime.min.time())
    )
    end_dt = (
        None
        if period_end is None
        else datetime.combine(period_end, datetime.min.time())
    )

    rows = await flight_controller.flight_repository.top_countries(
        metric=metric, start=start_dt, end=end_dt, limit=limit
    )
    return [_enrich_country_row(row) for row in rows]


@countries_router.get(
    "/{country_code}",
    response_model=CountryDetailResponse,
)
async def get_country_details(
    country_code: str,
    metric: str = Query(
        "flights",
        pattern="^(flights|credits|views)$",
    ),
    period_start: date | None = Query(None),
    period_end: date | None = Query(None),
    flight_controller: FlightController = Depends(Factory().get_flight_controller),
) -> CountryDetailResponse:
    metric = flight_controller.validate_metric(metric)
    start_dt = (
        None
        if period_start is None
        else datetime.combine(period_start, datetime.min.time())
    )
    end_dt = (
        None
        if period_end is None
        else datetime.combine(period_end, datetime.min.time())
    )

    rows = await flight_controller.flight_repository.top_countries(
        metric=metric, start=start_dt, end=end_dt, limit=500
    )
    code = country_code.upper()
    row = next(
        (r for r in rows if (r["country_code"] or "").upper() == code),
        None,
    )

    if not row:
        base = CountryStatsResponse(
            code=code,
            name=COUNTRY_NAMES.get(code),
            flag_url=COUNTRY_FLAGS.get(code),
            total_flights=0,
            total_pilots=0,
            total_credits=0,
            total_views=0,
        )
        top_pilots: list[dict] = []
    else:
        base = _enrich_country_row(row)
        top_pilots = await flight_controller.flight_repository.top_pilots(
            country_code=code,
            metric=metric,
            start=start_dt,
            end=end_dt,
            limit=10,
        )

    return CountryDetailResponse(
        **base.dict(),
        recent_flights=base.total_flights,
        top_pilots=top_pilots,
        bounding_box=None,
    )
