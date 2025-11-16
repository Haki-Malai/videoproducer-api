from http import HTTPStatus

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from core.exceptions import BadRequestException
from core.fastapi.exception_handlers import register_exception_handlers


class _SamplePayload(BaseModel):
    name: str
    strength: int


@pytest.fixture()
def test_client() -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/custom-error")
    async def custom_error_route():
        raise BadRequestException("Bad things happened")

    @app.get("/http-error")
    async def http_error_route():
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND.value, detail="Missing")

    @app.post("/validate")
    async def validate_route(payload: _SamplePayload):
        return payload

    @app.get("/explode")
    async def explode_route():
        raise RuntimeError("Unexpected failure")

    return TestClient(app, raise_server_exceptions=False)


def test_custom_exception_uses_standard_error_format(test_client: TestClient):
    response = test_client.get("/custom-error")

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == {
        "message": "Bad things happened",
        "description": HTTPStatus.BAD_REQUEST.description,
    }


def test_http_exception_is_serialized_like_api_errors(test_client: TestClient):
    response = test_client.get("/http-error")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {
        "message": "Missing",
        "description": HTTPStatus.NOT_FOUND.description,
    }


def test_validation_errors_are_reported_with_details(test_client: TestClient):
    response = test_client.post("/validate", json={"name": "Drone"})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    body = response.json()
    assert body["description"] == HTTPStatus.UNPROCESSABLE_ENTITY.description
    assert "Validation error" in body["message"]
    assert "strength" in body["message"]


def test_unhandled_exceptions_return_internal_error_body(test_client: TestClient):
    response = test_client.get("/explode")

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {
        "message": HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
        "description": HTTPStatus.INTERNAL_SERVER_ERROR.description,
    }
