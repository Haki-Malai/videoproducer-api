from fastapi import Depends, FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.authentication import AuthenticationMiddleware

from api import router
from core.config import config
from core.database.migration import prepare_database
from core.fastapi.dependencies import Logging
from core.fastapi.exception_handlers import register_exception_handlers
from core.fastapi.middlewares import (
    AuthenticationBackend,
    ResponseLoggerMiddleware,
    SQLAlchemyMiddleware,
)


def init_routers(app_: FastAPI) -> None:
    """Initialize the routers for the FastAPI application.

    :param app_: The FastAPI application.
    """
    app_.include_router(router)


def init_listeners(app_: FastAPI) -> None:
    """Initialize the listeners for the FastAPI application.

    :param app_: The FastAPI application.
    """
    register_exception_handlers(app_)

    @app_.on_event("startup")
    async def ensure_database_ready():
        await prepare_database()


def make_middleware() -> list[Middleware]:
    """Create the middleware for the FastAPI application.

    :returns: The middleware for the FastAPI application.
    """
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
        Middleware(SQLAlchemyMiddleware),
        Middleware(ResponseLoggerMiddleware),
        Middleware(AuthenticationMiddleware, backend=AuthenticationBackend()),
    ]
    return middleware


def create_app() -> FastAPI:
    """Create the FastAPI application.

    :returns: The FastAPI application.
    """
    app_ = FastAPI(
        title=config.TITLE,
        description=config.DESCRIPTION,
        version=config.RELEASE_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        dependencies=[Depends(Logging)],
        middleware=make_middleware(),
    )
    # Initialize the routers
    app_.include_router(router)
    init_listeners(app_=app_)

    # Redirect to the docs
    @app_.get("/", include_in_schema=False)
    async def redirect_to_docs():
        return RedirectResponse(url="/docs")

    return app_


app = create_app()
