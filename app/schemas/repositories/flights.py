from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime

import sqlalchemy as sa
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models import Role
from app.models.flight import Flight, FlightStatus, FlightTheme
from app.models.user import User
from core.repository import BaseRepository


class FlightRepository(BaseRepository[Flight]):
    async def list_public(
        self,
        bbox: tuple[float, float, float, float] | None,
        filters: dict[str, object] | None,
        limit: int,
        offset: int,
    ) -> Sequence[Flight]:
        query = select(Flight).options(selectinload(Flight.pilot))

        status_filter = filters.get("status") if filters else None
        if status_filter is None:
            query = query.where(Flight.status == FlightStatus.APPROVED)

        if bbox:
            min_lng, min_lat, max_lng, max_lat = bbox
            query = query.where(
                Flight.lat >= min_lat,
                Flight.lat <= max_lat,
                Flight.lng >= min_lng,
                Flight.lng <= max_lng,
            )

        query = self._apply_filters(query, filters)
        query = query.order_by(Flight.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    def _apply_filters(self, query, filters: dict[str, object] | None):
        if not filters:
            return query

        if (country := filters.get("country")):
            query = query.where(Flight.country_code == country)

        if (drone_type := filters.get("drone_type")):
            query = query.where(Flight.drone_type == drone_type)

        if (theme := filters.get("theme")):
            query = query.where(Flight.theme == theme)

        if (pilot_name := filters.get("pilot_name")):
            query = query.join(Flight.pilot).where(
                sa.or_(
                    User.username.ilike(f"%{pilot_name}%"),
                    User.display_name.ilike(f"%{pilot_name}%"),
                )
            )

        if (tags := filters.get("tags")):
            # tags is a list[str]; we require all tags to be present
            query = query.where(Flight.tags.contains(tags))

        duration_min = filters.get("duration_min")
        duration_max = filters.get("duration_max")
        if duration_min is not None:
            query = query.where(Flight.duration_seconds >= duration_min)
        if duration_max is not None:
            query = query.where(Flight.duration_seconds <= duration_max)

        if (q := filters.get("q")):
            like = f"%{q}%"
            query = query.where(
                sa.or_(
                    Flight.title.ilike(like),
                    Flight.description.ilike(like),
                )
            )

        if (status := filters.get("status")):
            query = query.where(Flight.status == status)

        return query

    async def top_pilots(
        self,
        country_code: str | None,
        metric: str,
        start: datetime | None,
        end: datetime | None,
        limit: int,
    ) -> list[dict]:
        metric_column = {
            "flights": func.count(Flight.id),
            "credits": func.coalesce(func.sum(Flight.credits), 0),
            "views": func.coalesce(func.sum(Flight.views), 0),
        }[metric]

        query = (
            select(
                User.id.label("pilot_id"),
                User.username,
                User.display_name,
                User.country_code,
                func.count(Flight.id).label("flights_count"),
                func.coalesce(func.sum(Flight.credits), 0).label("total_credits"),
                func.coalesce(func.sum(Flight.views), 0).label("total_views"),
                metric_column.label("metric_value"),
            )
            .join(User, Flight.pilot_id == User.id)
            .where(
                Flight.status == FlightStatus.APPROVED,
                User.role == Role.PILOT,
            )
            .group_by(
                User.id,
                User.username,
                User.display_name,
                User.country_code,
            )
            .order_by(sa.desc(metric_column))
            .limit(limit)
        )

        if country_code:
            query = query.where(User.country_code == country_code)

        if start:
            query = query.where(Flight.created_at >= start)
        if end:
            query = query.where(Flight.created_at < end)

        result = await self.session.execute(query)
        return [dict(row._mapping) for row in result]

    async def top_countries(
        self,
        metric: str,
        start: datetime | None,
        end: datetime | None,
        limit: int,
    ) -> list[dict]:
        metric_column = {
            "flights": func.count(Flight.id),
            "credits": func.coalesce(func.sum(Flight.credits), 0),
            "views": func.coalesce(func.sum(Flight.views), 0),
        }[metric]

        query = (
            select(
                Flight.country_code,
                func.count(Flight.id).label("flights_count"),
                func.count(sa.distinct(Flight.pilot_id)).label("unique_pilots"),
                func.coalesce(func.sum(Flight.credits), 0).label("total_credits"),
                func.coalesce(func.sum(Flight.views), 0).label("total_views"),
                metric_column.label("metric_value"),
            )
            .where(Flight.status == FlightStatus.APPROVED)
            .group_by(Flight.country_code)
            .order_by(sa.desc(metric_column))
            .limit(limit)
        )

        if start:
            query = query.where(Flight.created_at >= start)
        if end:
            query = query.where(Flight.created_at < end)

        result = await self.session.execute(query)
        return [dict(row._mapping) for row in result]

    async def flights_per_day(
        self,
        start: date,
        end: date,
    ) -> list[dict[str, object]]:
        date_expr = func.date(Flight.created_at)
        query = (
            select(
                date_expr.label("date"),
                func.count(Flight.id).label("count"),
            )
            .where(
                Flight.created_at >= datetime.combine(start, datetime.min.time()),
                Flight.created_at < datetime.combine(end, datetime.min.time()),
                Flight.status == FlightStatus.APPROVED,
            )
            .group_by(date_expr)
            .order_by(date_expr)
        )
        result = await self.session.execute(query)
        return [{"date": row.date.isoformat(), "count": row.count} for row in result]
