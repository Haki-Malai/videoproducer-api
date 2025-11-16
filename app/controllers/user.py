from collections.abc import Sequence

from app.models import User
from app.repositories import UserRepository
from app.schemas.extras import Token
from core.controller import BaseController
from core.exceptions import UnauthorizedException
from core.security.jwt_handler import jwt_handler


class UserController(BaseController[User]):
    def __init__(self, user_repository: UserRepository):
        super().__init__(model=User, repository=user_repository)
        self.user_repository = user_repository

    async def search_by_username(self, query: str) -> Sequence[User]:
        """Search for users by username using a query.

        :param query: The query to search for.

        :return: A list of users that match the query.
        """
        return await self.user_repository.search_by_username(query)

    async def login(self, username: str, password: str) -> Token | None:
        """Login a user with a username and password.

        :param username: The username of the user.
        :param password: The password of the user.

        :return: True if the login is successful, False otherwise.
        """
        user = await self.user_repository.get_by_username(username)
        if user and user.verify_password(password):
            return Token(
                access_token=jwt_handler.encode({"user_id": user.id}),
                refresh_token=jwt_handler.encode({"sub": "refresh_token"}),
            )
        raise UnauthorizedException("Invalid username or password")

    async def refresh_token(
        self, access_token: str, refresh_token: str
    ) -> Token | None:
        """Refresh a token.

        :param token: The token to refresh.

        :return: A new token.
        """
        refresh_token_payload = jwt_handler.decode(refresh_token)
        access_token_payload = jwt_handler.decode(access_token)
        try:
            if refresh_token_payload["sub"] == "refresh_token":
                return Token(
                    access_token=jwt_handler.encode(
                        {"user_id": access_token_payload["user_id"]}
                    ),
                    refresh_token=jwt_handler.encode({"sub": "refresh_token"}),
                )
        except KeyError:
            raise UnauthorizedException("Invalid token")
