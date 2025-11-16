from __future__ import annotations

from typing import Any

from sqlalchemy import select

from app.models.pilot import Pilot
from core.repository import BaseRepository


class PilotRepository(BaseRepository[Pilot]):
    async def get_by_username(self, username: str) -> Pilot | None:
        query = select(Pilot).where(Pilot.username == username)
        return await self._first(query)

    async def get_by_email(self, email: str) -> Pilot | None:
        query = select(Pilot).where(Pilot.email == email)
        return await self._first(query)

    async def get_or_create(
        self,
        username: str | None,
        email: str | None,
        display_name: str | None,
        country_code: str | None,
        social: dict[str, str] | None = None,
    ) -> Pilot:
        social = social or {}
        pilot: Pilot | None = None

        if username:
            pilot = await self.get_by_username(username)

        if not pilot and email:
            pilot = await self.get_by_email(email)

        if pilot:
            return pilot

        generated_username = username or (email.split("@")[0] if email else "pilot")

        attributes: dict[str, Any] = {
            "username": generated_username,
            "display_name": display_name or generated_username,
            "email": email,
            "country_code": country_code,
            "instagram_url": social.get("instagram"),
            "youtube_url": social.get("youtube"),
            "website_url": social.get("website"),
        }
        return await self.create(attributes)
