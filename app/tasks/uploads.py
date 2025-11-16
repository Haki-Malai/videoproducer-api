import logging

from core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="uploads.process_uploaded_file")
def process_uploaded_file(path: str) -> None:
    """Background processing for an uploaded file.

    Plug in transcoding, thumbnail extraction, etc. here.
    """
    logger.info("Processing uploaded file at %s", path)
