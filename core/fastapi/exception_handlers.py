from __future__ import annotations

import json
import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.exceptions import CustomException

logger = logging.getLogger(__name__)


def _status_description(status_code: int) -> str:
    try:
        return HTTPStatus(status_code).description
    except ValueError:
        return HTTPStatus.INTERNAL_SERVER_ERROR.description


def _stringify_detail(detail: Any) -> str:
    if isinstance(detail, str):
        return detail
    try:
        return json.dumps(detail, default=str)
    except (TypeError, ValueError):
        return str(detail)


def register_exception_handlers(app: FastAPI) -> None:
    """Attach JSON exception handlers to the provided FastAPI app."""

    @app.exception_handler(CustomException)
    async def handle_custom_exception(
        request: Request, exc: CustomException  # noqa: ARG001
    ):
        return JSONResponse(
            status_code=int(exc.status_code),
            content={"message": exc.message, "description": exc.description},
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request, exc: StarletteHTTPException  # noqa: ARG001
    ):
        description = _status_description(exc.status_code)
        message = _stringify_detail(exc.detail or HTTPStatus(exc.status_code).phrase)
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": message, "description": description},
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(
        request: Request, exc: RequestValidationError  # noqa: ARG001
    ):
        status_code = HTTPStatus.UNPROCESSABLE_ENTITY
        message = f"Validation error: {_stringify_detail(exc.errors())}"
        return JSONResponse(
            status_code=status_code.value,
            content={"message": message, "description": status_code.description},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(
        request: Request, exc: Exception  # noqa: ARG001
    ):
        status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        logger.exception("Unhandled application error", exc_info=exc)
        return JSONResponse(
            status_code=status_code.value,
            content={
                "message": status_code.phrase,
                "description": status_code.description,
            },
        )
