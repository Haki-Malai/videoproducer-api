from datetime import datetime, timedelta

import pytest
from jose import JWTError, jwt

from core.config import config
from core.exceptions import UnauthorizedException
from core.security import jwt_handler


@pytest.fixture
def mock_payload():
    return {"sub": "1234567890", "name": "John Doe", "iat": 1516239022}


@pytest.fixture
def mock_token(mock_payload):
    expire = datetime.utcnow() + timedelta(minutes=config.JWT_EXPIRE_MINUTES)
    payload = mock_payload.copy()
    payload.update({"exp": expire})
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)


@pytest.fixture
def mock_expired_token(mock_payload):
    expire = (
        datetime.utcnow()
        - timedelta(minutes=config.JWT_EXPIRE_MINUTES)
        - timedelta(seconds=10)
    )
    payload = mock_payload.copy()
    payload.update({"exp": expire})
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)


class TestJWTHandler:
    def test_encode(self, mock_payload):
        token = jwt_handler.encode(mock_payload)
        assert token is not None
        assert isinstance(token, str)

    def test_decode(self, mock_token, mock_payload):
        decoded = jwt_handler.decode(mock_token)
        assert decoded is not None
        assert isinstance(decoded, dict)
        assert decoded.pop("exp") is not None
        assert decoded == mock_payload

    def test_decode_error(self):
        with pytest.raises(UnauthorizedException):
            with pytest.raises(JWTError):
                jwt_handler.decode("invalid_token")

    def test_decode_expired(self, mock_expired_token):
        with pytest.raises(UnauthorizedException):
            jwt_handler.decode(mock_expired_token)
