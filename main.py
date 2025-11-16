import logging

import uvicorn

from core.config import config


def main():
    """Run the FastAPI application with Uvicorn."""
    logging.basicConfig(level=logging.INFO)
    try:
        uvicorn.run(
            app="core.server:app",
            host="0.0.0.0",
            port=config.API_PORT,
            reload=config.ENVIRONMENT != "production",
            workers=1,
            log_level="info",
        )
    except Exception:
        logging.error("Failed to start Uvicorn server:", exc_info=True)


if __name__ == "__main__":
    main()
