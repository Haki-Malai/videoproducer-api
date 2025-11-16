from collections.abc import Sequence
import secrets
from typing import Any

from sqlalchemy.future import select

from app.models import Role
from app.models.user import User
from core.repository import BaseRepository


class UserRepository(BaseRepository[User]):
    async def get_by_username(self, username: str) -> User:
        """Get a user by username.

        :param username: The username of the user.

        :return: The user with the username.
        """
        result = await self.session.execute(
            select(User).filter(User.username == username)
        )
        return result.scalar()

    async def search_by_username(self, query: str) -> Sequence[User]:
        """Get users by username using a query.

        :param query: The query to search for.

        :return: A list of users that match the query.
        """
        result = await self.session.execute(
            select(User).filter(User.username.ilike(f"%{query}%"))
        )
        return result.scalars().all()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).filter(User.email == email))
        return result.scalar()

    async def get_or_create_pilot(
        self,
        username: str | None,
        email: str | None,
        display_name: str | None,
        country_code: str | None,
        social: dict[str, str] | None = None,
    ) -> User:
        social = social or {}
        user: User | None = None

        if username:
            user = await self.get_by_username(username)
        if not user and email:
            user = await self.get_by_email(email)

        if user:
            updated: dict[str, Any] = {}
            if user.role.value < Role.PILOT.value:
                updated["role"] = Role.PILOT
            if display_name and not user.display_name:
                updated["display_name"] = display_name
            if email and not user.email:
                updated["email"] = email
            if country_code and not user.country_code:
                updated["country_code"] = country_code
            if social.get("instagram") and social["instagram"] != user.instagram_url:
                updated["instagram_url"] = social["instagram"]
            if social.get("youtube") and social["youtube"] != user.youtube_url:
                updated["youtube_url"] = social["youtube"]
            if social.get("website") and social["website"] != user.website_url:
                updated["website_url"] = social["website"]

            if updated:
                user = await self.update(user, updated)
            return user

        generated_username = username or (email.split("@")[0] if email else "pilot")
        random_password = secrets.token_urlsafe(16)

        attributes: dict[str, Any] = {
            "username": generated_username,
            "password": random_password,
            "role": Role.PILOT,
            "display_name": display_name or generated_username,
            "email": email,
            "country_code": country_code,
            "instagram_url": social.get("instagram"),
            "youtube_url": social.get("youtube"),
            "website_url": social.get("website"),
        }
        return await self.create(attributes)
