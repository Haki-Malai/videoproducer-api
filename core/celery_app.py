from __future__ import annotations

from celery import Celery

from core.config import config

celery_app = Celery("secure_waypoint")

celery_app.conf.broker_url = config.CELERY_BROKER_URL
celery_app.conf.result_backend = config.CELERY_RESULT_BACKEND
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.timezone = "UTC"
celery_app.conf.enable_utc = True
celery_app.conf.task_routes = {
    "flights.*": {"queue": "flights"},
}

# Autodiscover tasks in app.tasks.*
celery_app.autodiscover_tasks(["app.tasks"])
