from jose import ExpiredSignatureError, JWTError, jwt
from starlette.authentication import (
    AuthCredentials,
)
from starlette.authentication import (
    AuthenticationBackend as BaseAuthenticationBackend,
)
from starlette.requests import HTTPConnection

from app.schemas.extras import CurrentUser
from core.config import config


class AuthenticationBackend(BaseAuthenticationBackend):
    async def authenticate(
        self, conn: HTTPConnection
    ) -> tuple[AuthCredentials, CurrentUser] | None:
        """Authenticates the user based on the Authorization header.

        :param conn: The HTTP connection.

        :returns: The authentication credentials and the current user.
        """
        authorization: str = conn.headers.get("Authorization", "")
        scheme, token = self._extract_token(authorization)

        if scheme != "bearer" or not token:
            return None

        user_id = self._validate_token(token)
        if user_id is None:
            return None

        current_user = CurrentUser(id=user_id)
        return AuthCredentials(["authenticated"]), current_user

    def _extract_token(self, authorization: str) -> tuple[str, str | None]:
        """Extracts the token type and token value from the authorization header.

        :param authorization: The authorization header.

        :returns: The token type and token value.
        """
        try:
            scheme, token = authorization.strip().split(" ", 1)
            return scheme.lower(), token
        except ValueError:
            return "", None

    def _validate_token(self, token: str) -> str | None:
        """Validates the token and returns the user_id if valid.

        :param token: The token to validate.

        :returns: The user_id if the token is valid.
        """
        try:
            payload = jwt.decode(
                token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM]
            )
            return payload.get("user_id")
        except (JWTError, ExpiredSignatureError):
            return None
