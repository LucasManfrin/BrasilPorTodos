from datetime import UTC, datetime
from threading import Event
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app import collect_indicators as worker
from app.core.errors import DomainError
from app.modules.indicators.schedule import CollectionSchedule, next_attempt_at, public_schedule


def schedule(**extra):
    return CollectionSchedule(_env_file=None, **extra)


def instant(value):
    return datetime.fromisoformat(value)


def test_first_start_catches_up_once():
    now = instant("2026-10-25T14:00:00+00:00")
    assert next_attempt_at(now, None, None, schedule()) == now


def test_calendar_midnight_does_not_drift_by_previous_start_seconds():
    now = instant("2026-10-26T03:00:00+00:00")
    previous = instant("2026-10-25T03:00:03+00:00")
    assert next_attempt_at(now, previous, "SUCCESS", schedule()) == now


def test_successful_current_slot_waits_until_next_midnight():
    now = instant("2026-10-25T14:00:00+00:00")
    previous = instant("2026-10-25T03:01:00+00:00")
    assert next_attempt_at(now, previous, "SUCCESS", schedule()) == instant(
        "2026-10-26T03:00:00+00:00"
    )


def test_a_successful_catch_up_is_not_repeated_on_restart():
    now = instant("2026-10-25T14:01:00+00:00")
    previous = instant("2026-10-25T14:00:00+00:00")
    assert next_attempt_at(now, previous, "SUCCESS", schedule()) > now


@pytest.mark.parametrize("status", ["PARTIAL", "RUNNING", "FAILED"])
def test_unsuccessful_or_interrupted_run_waits_an_hour(status):
    previous = instant("2026-10-25T13:00:00+00:00")
    now = instant("2026-10-25T13:59:00+00:00")
    expected = instant("2026-10-25T14:00:00+00:00")
    assert next_attempt_at(now, previous, status, schedule()) == expected
    assert next_attempt_at(expected, previous, status, schedule()) == expected


def test_recent_manual_collection_delays_midnight_instead_of_bypassing_cooldown():
    now = instant("2026-10-26T03:00:00+00:00")
    previous = instant("2026-10-26T02:50:00+00:00")
    assert next_attempt_at(now, previous, "SUCCESS", schedule()) == instant(
        "2026-10-26T03:50:00+00:00"
    )


def test_calendar_schedule_handles_twenty_three_hour_day():
    settings = schedule(collection_timezone="America/New_York")
    now = instant("2026-03-08T05:01:00+00:00")
    previous = instant("2026-03-08T05:00:00+00:00")
    assert next_attempt_at(now, previous, "SUCCESS", settings) == instant(
        "2026-03-09T04:00:00+00:00"
    )


def test_custom_hour_checks_the_last_due_slot():
    settings = schedule(collection_daily_at="12:30")
    now = instant("2026-10-25T14:00:00+00:00")
    previous = instant("2026-10-24T15:30:00+00:00")
    assert next_attempt_at(now, previous, "SUCCESS", settings) == instant(
        "2026-10-25T15:30:00+00:00"
    )


@pytest.mark.parametrize(
    "extra",
    [
        {"collection_daily_at": "24:00"},
        {"collection_daily_at": "00:60"},
        {"collection_timezone": "Unknown/Timezone"},
        {"collection_retry_minutes": 1},
    ],
)
def test_invalid_schedule_is_rejected_without_echoing_config(extra):
    with pytest.raises(ValidationError) as caught:
        schedule(**extra)
    assert "input_value" not in str(caught.value)


def test_naive_timestamps_are_rejected():
    with pytest.raises(ValueError, match="fuso"):
        next_attempt_at(datetime(2026, 10, 25), None, None, schedule())


def test_public_schedule_reports_configuration_without_claiming_worker_liveness(monkeypatch):
    from app.modules.indicators import schedule as module

    monkeypatch.setattr(module, "get_schedule", lambda: schedule(collection_schedule_enabled=True))
    now = datetime(2026, 10, 25, 14, tzinfo=UTC)
    result = public_schedule(now, SimpleNamespace(created_at=now, status="SUCCESS"))
    assert result["enabled"] is True and result["daily_at"] == "00:00"
    assert result["next_attempt_at"] == "2026-10-26T03:00:00+00:00"
    assert "username" not in result and "running" not in result


def test_worker_consumes_force_once_and_waits_without_http_polling(monkeypatch):
    calls = []
    waits = []
    stop = Event()

    def collect(username, **options):
        calls.append(options)
        if len(calls) == 2:
            stop.set()
        return {"skipped": True}

    def wait(seconds):
        waits.append(seconds)

    monkeypatch.setattr(worker, "collect_once", collect)
    monkeypatch.setattr(stop, "wait", wait)
    assert worker.run_worker(username=None, watch=True, immediate=True, stop=stop) == 0
    assert calls == [
        {"scheduled": True, "immediate": True},
        {"scheduled": True, "immediate": False},
    ]
    assert waits == [60, 60]


@pytest.mark.parametrize(
    "error", [DomainError(409, "COLLECTION_ACTOR_REQUIRED", "private"), SQLAlchemyError("private")]
)
def test_worker_fails_safely_without_dumping_exception_payload(monkeypatch, capsys, error):
    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(worker, "collect_once", fail)
    assert worker.run_worker(username=None, watch=False, immediate=False, stop=Event()) == 1
    assert "private" not in capsys.readouterr().out
