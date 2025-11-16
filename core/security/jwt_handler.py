from datetime import datetime, timedelta

from jose import jwt

from core.config import config
from core.exceptions import UnauthorizedException


class JWTHandler:
    secret_key = config.SECRET_KEY
    algorithm = config.JWT_ALGORITHM
    expire_minutes = config.JWT_EXPIRE_MINUTES

    def encode(self, payload: dict) -> str:
        expire = datetime.now() + timedelta(minutes=self.expire_minutes)
        payload.update({"exp": expire})
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode(self, token: str) -> dict:
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except Exception:
            raise UnauthorizedException("Invalid token")


jwt_handler: JWTHandler = JWTHandler()
