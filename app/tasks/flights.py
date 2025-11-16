import logging

from core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="flights.process_new_flight")
def process_new_flight(flight_id: int) -> None:
    """Background processing for a newly submitted flight.

    Extend this with:
      - video metadata fetching,
      - reverse geocoding,
      - thumbnail generation,
      - stats precomputation.
    """
    logger.info("Processing new flight %s", flight_id)
