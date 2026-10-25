from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import select

from app.core.errors import DomainError
from app.modules.indicators import collection
from app.modules.indicators.collection import CollectionRun
from app.modules.indicators.schedule import CollectionSchedule
from app.modules.users.models import User

from .test_admin_indicators import administrator

pytestmark = pytest.mark.database


def frozen_clock(monkeypatch):
    now = datetime(2026, 10, 26, 3, tzinfo=UTC)

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return now.astimezone(tz) if tz else now.replace(tzinfo=None)

    monkeypatch.setattr(collection, "datetime", Clock)
    monkeypatch.setattr(collection, "get_schedule", lambda: CollectionSchedule(_env_file=None))
    return now


def test_daily_slot_is_rechecked_inside_database_lock(auth_client, db_session, monkeypatch):
    actor = administrator(auth_client, db_session)
    user = db_session.get(User, UUID(actor["user"]["id"]))
    now = frozen_clock(monkeypatch)
    db_session.add(
        CollectionRun(
            actor_id=user.id,
            created_at=now - timedelta(minutes=1),
            finished_at=now,
            status="SUCCESS",
            results={},
        )
    )
    db_session.commit()
    result = collection.collect(db_session, user, scheduled=True)
    assert result["skipped"] is True
    assert len(db_session.scalars(select(CollectionRun)).all()) == 1


def test_scheduled_slot_collects_without_waiting_rolling_twenty_four_hours(
    auth_client, db_session, monkeypatch
):
    actor = administrator(auth_client, db_session)
    user = db_session.get(User, UUID(actor["user"]["id"]))
    now = frozen_clock(monkeypatch)
    db_session.add(
        CollectionRun(
            actor_id=user.id,
            created_at=now - timedelta(days=1) + timedelta(seconds=3),
            finished_at=now - timedelta(days=1) + timedelta(seconds=10),
            status="SUCCESS",
            results={},
        )
    )
    db_session.commit()
    monkeypatch.setattr(collection.bcb, "BCB_SERIES", {})
    monkeypatch.setattr(collection.ibge, "IBGE_SERIES", {})
    for function in [
        "collect_income",
        "collect_fiscal",
        "collect_composition",
        "collect_interest",
        "collect_spending",
        "collect_general_government",
    ]:
        monkeypatch.setattr(collection, function, lambda *args: {})
    calls = []

    def provider(*args):
        calls.append(True)
        return {"fixture": {"status": "SUCCESS"}}

    monkeypatch.setattr(collection, "collect_gdp", provider)
    assert collection.collect(db_session, user)["skipped"] is True
    result = collection.collect(db_session, user, scheduled=True)
    assert result["skipped"] is False and result["last_run"]["status"] == "SUCCESS"
    assert calls == [True]
    assert collection.collect(db_session, user, scheduled=True)["skipped"] is True


def test_schedule_never_bypasses_global_advisory_lock(auth_client, db_session):
    actor = administrator(auth_client, db_session)
    user = db_session.get(User, UUID(actor["user"]["id"]))
    with collection.get_engine().connect() as owner:
        owner.exec_driver_sql("SELECT pg_advisory_lock(82461301)")
        try:
            with pytest.raises(DomainError, match="COLLECTION_RUNNING"):
                collection.collect(db_session, user, scheduled=True)
        finally:
            owner.exec_driver_sql("SELECT pg_advisory_unlock(82461301)")
