from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.exceptions.base import UnauthorizedException


class AuthenticationRequired:
    def __init__(
        self,
        access_token: HTTPAuthorizationCredentials = Depends(
            HTTPBearer(auto_error=False)
        ),
    ):
        if not access_token:
            raise UnauthorizedException("Access token is required")
