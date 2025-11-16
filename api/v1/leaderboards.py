from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, Query

from app.controllers.flight import FlightController
from app.schemas.responses.leaderboards import (
    CountryLeaderboardEntry,
    PilotLeaderboardEntry,
)
from core.factory import Factory

leaderboards_router = APIRouter(prefix="/leaderboards", tags=["Leaderboards"])


@leaderboards_router.get(
    "/pilots",
    response_model=list[PilotLeaderboardEntry],
)
async def global_pilot_leaderboard(
    metric: str = Query(
        "credits",
        pattern="^(flights|credits|views)$",
        description="Ranking metric: flights, credits or views",
    ),
    period_start: date | None = Query(
        None, description="Start date (inclusive) in YYYY-MM-DD"
    ),
    period_end: date | None = Query(
        None, description="End date (exclusive) in YYYY-MM-DD"
    ),
    limit: int = Query(50, ge=1, le=100),
    flight_controller: FlightController = Depends(Factory().get_flight_controller),
) -> list[PilotLeaderboardEntry]:
    metric = flight_controller.validate_metric(metric)
    start = period_start
    end = period_end or date.today()

    rows = await flight_controller.flight_repository.top_pilots(
        country_code=None,
        metric=metric,
        start=None
        if start is None
        else datetime.combine(start, datetime.min.time()),
        end=None if end is None else datetime.combine(end, datetime.min.time()),
        limit=limit,
    )
    entries: list[PilotLeaderboardEntry] = []
    for idx, row in enumerate(rows, start=1):
        entries.append(
            PilotLeaderboardEntry(
                pilot_id=row["pilot_id"],
                username=row["username"],
                display_name=row["display_name"],
                country_code=row["country_code"],
                rank=idx,
                metric_value=row["metric_value"],
                flights_count=row["flights_count"],
                total_credits=row["total_credits"],
                total_views=row["total_views"],
            )
        )
    return entries


@leaderboards_router.get(
    "/pilots/{country_code}",
    response_model=list[PilotLeaderboardEntry],
)
async def country_pilot_leaderboard(
    country_code: str,
    metric: str = Query(
        "credits",
        pattern="^(flights|credits|views)$",
    ),
    period_start: date | None = Query(None),
    period_end: date | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    flight_controller: FlightController = Depends(Factory().get_flight_controller),
) -> list[PilotLeaderboardEntry]:
    metric = flight_controller.validate_metric(metric)
    start = period_start
    end = period_end or date.today()
    cc = country_code.upper()

    rows = await flight_controller.flight_repository.top_pilots(
        country_code=cc,
        metric=metric,
        start=None
        if start is None
        else datetime.combine(start, datetime.min.time()),
        end=None if end is None else datetime.combine(end, datetime.min.time()),
        limit=limit,
    )
    entries: list[PilotLeaderboardEntry] = []
    for idx, row in enumerate(rows, start=1):
        entries.append(
            PilotLeaderboardEntry(
                pilot_id=row["pilot_id"],
                username=row["username"],
                display_name=row["display_name"],
                country_code=row["country_code"],
                rank=idx,
                metric_value=row["metric_value"],
                flights_count=row["flights_count"],
                total_credits=row["total_credits"],
                total_views=row["total_views"],
            )
        )
    return entries


@leaderboards_router.get(
    "/countries",
    response_model=list[CountryLeaderboardEntry],
)
async def country_leaderboard(
    metric: str = Query(
        "flights",
        pattern="^(flights|credits|views)$",
    ),
    period_start: date | None = Query(None),
    period_end: date | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    flight_controller: FlightController = Depends(Factory().get_flight_controller),
) -> list[CountryLeaderboardEntry]:
    metric = flight_controller.validate_metric(metric)
    start = period_start
    end = period_end or date.today()

    rows = await flight_controller.flight_repository.top_countries(
        metric=metric,
        start=None
        if start is None
        else datetime.combine(start, datetime.min.time()),
        end=None if end is None else datetime.combine(end, datetime.min.time()),
        limit=limit,
    )
    entries: list[CountryLeaderboardEntry] = []
    for idx, row in enumerate(rows, start=1):
        entries.append(
            CountryLeaderboardEntry(
                country_code=row["country_code"],
                rank=idx,
                metric_value=row["metric_value"],
                flights_count=row["flights_count"],
                unique_pilots=row["unique_pilots"],
                total_credits=row["total_credits"],
                total_views=row["total_views"],
            )
        )
    return entries
