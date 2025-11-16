from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.controllers import FlightController
from app.models.flight import FlightStatus, FlightTheme
from app.schemas.requests.flights import FlightSubmissionRequest, PilotSubmission
from core.exceptions import BadRequestException


def make_controller(
    flight_repo: object | None = None, user_repo: object | None = None
) -> FlightController:
    flight_repo = flight_repo or SimpleNamespace()
    user_repo = user_repo or SimpleNamespace()
    return FlightController(
        flight_repository=flight_repo,
        user_repository=user_repo,
    )


@pytest.mark.asyncio
async def test_submit_flight_creates_pilot_and_triggers_background_task(monkeypatch):
    created_flight = SimpleNamespace(id=321)
    flight_repo = SimpleNamespace()
    flight_repo.create = AsyncMock(return_value=created_flight)

    pilot = SimpleNamespace(id=77)
    user_repo = SimpleNamespace()
    user_repo.get_or_create_pilot = AsyncMock(return_value=pilot)

    controller = make_controller(flight_repo=flight_repo, user_repo=user_repo)

    mock_delay = MagicMock()
    monkeypatch.setattr(
        "app.controllers.flight.process_new_flight.delay",
        mock_delay,
        raising=False,
    )

    payload = FlightSubmissionRequest(
        video_key="raw/foo.mp4",
        lat=12.34,
        lng=56.78,
        pilot=PilotSubmission(
            username="ace",
            name="Ace Pilot",
            email="ace@example.com",
            instagram="https://instagram.com/ace",
        ),
        drone_type="fpv",
        tags=["urban", "night"],
        theme=FlightTheme.URBAN,
        duration_seconds=180,
        title="City flight",
        description="Flying downtown",
        country_code="US",
    )

    monkeypatch.setattr(
        "app.controllers.flight.s3.build_s3_uri",
        lambda key: f"s3://bucket/{key}",
        raising=False,
    )

    result = await controller.submit_flight(payload)

    assert result is created_flight
    user_repo.get_or_create_pilot.assert_awaited_once_with(
        username="ace",
        email="ace@example.com",
        display_name="Ace Pilot",
        country_code="US",
        social={"instagram": "https://instagram.com/ace"},
    )
    attrs = flight_repo.create.await_args.args[0]
    assert attrs["pilot_id"] == pilot.id
    assert attrs["status"] == FlightStatus.PENDING
    assert attrs["video_path"] == "s3://bucket/raw/foo.mp4"
    assert attrs["tags"] == ["urban", "night"]
    mock_delay.assert_called_once_with(created_flight.id)


@pytest.mark.asyncio
async def test_submit_flight_without_pilot_leaves_pilot_id_null(monkeypatch):
    created_flight = SimpleNamespace(id=111)
    flight_repo = SimpleNamespace()
    flight_repo.create = AsyncMock(return_value=created_flight)

    user_repo = SimpleNamespace()
    user_repo.get_or_create_pilot = AsyncMock()

    controller = make_controller(flight_repo=flight_repo, user_repo=user_repo)

    mock_delay = MagicMock()
    monkeypatch.setattr(
        "app.controllers.flight.process_new_flight.delay",
        mock_delay,
        raising=False,
    )

    payload = FlightSubmissionRequest(
        video_key="raw/foo.mp4",
        lat=1.0,
        lng=2.0,
        pilot=None,
        drone_type=None,
        tags=None,
        theme=None,
        duration_seconds=None,
        title=None,
        description=None,
        country_code="DE",
    )

    monkeypatch.setattr(
        "app.controllers.flight.s3.build_s3_uri",
        lambda key: f"s3://bucket/{key}",
        raising=False,
    )

    await controller.submit_flight(payload)

    user_repo.get_or_create_pilot.assert_not_awaited()
    attrs = flight_repo.create.await_args.args[0]
    assert attrs["pilot_id"] is None
    assert attrs["video_path"] == "s3://bucket/raw/foo.mp4"
    mock_delay.assert_called_once_with(created_flight.id)


@pytest.mark.parametrize("metric", ["flights", "credits", "views"])
def test_validate_metric_accepts_allowed_values(metric: str):
    controller = make_controller()
    assert controller.validate_metric(metric) == metric


def test_validate_metric_rejects_unknown_metric():
    controller = make_controller()
    with pytest.raises(BadRequestException):
        controller.validate_metric("speed")


@pytest.mark.asyncio
async def test_update_flight_delegates_to_approve():
    controller = make_controller()
    controller.approve = AsyncMock(return_value="approved")

    result = await controller.update_flight(
        10, {"status": FlightStatus.APPROVED, "credits": 5}
    )

    controller.approve.assert_awaited_once_with(10, 5)
    assert result == "approved"


@pytest.mark.asyncio
async def test_update_flight_updates_when_no_status_change():
    flight_repo = SimpleNamespace()
    flight_repo.update = AsyncMock(return_value="updated")

    controller = make_controller(flight_repo=flight_repo)
    controller.get_by_id = AsyncMock(return_value="flight")

    result = await controller.update_flight(9, {"title": "New title"})

    controller.get_by_id.assert_awaited_once_with(9)
    flight_repo.update.assert_awaited_once_with("flight", {"title": "New title"})
    assert result == "updated"
