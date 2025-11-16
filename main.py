import logging

import uvicorn

from core.config import config


def get_application():
    """Create FastAPI application

    :return: the FastAPI application
    """
    logging.basicConfig(level=logging.INFO)
    try:
        uvicorn.run(
            app="core.server:app",
            host="0.0.0.0",
            port=8000,
            reload=config.ENVIRONMENT != "production",
            workers=1,
            log_level="info",
        )
    except Exception:
        logging.error("Failed to start Uvicorn server:", exc_info=True)


app = get_application()
