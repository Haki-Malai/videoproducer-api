from collections.abc import Sequence

from sqlalchemy.future import select

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
