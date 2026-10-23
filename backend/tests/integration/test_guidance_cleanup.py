from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import func, select

from app.guidance_cleanup import cleanup_expired
from app.modules.guidance import service
from app.modules.guidance.models import GuidanceCall

from .test_auth import signup

pytestmark = pytest.mark.database


def test_cleanup_deletes_only_expired_logs_and_preserves_current_usage(auth_client, db_session):
    owner, _ = signup(auth_client)
    other, _ = signup(auth_client)
    now = datetime.now(UTC)
    rows = []
    for credentials, expiration in [
        (owner, now - timedelta(seconds=1)),
        (other, now),
        (owner, now + timedelta(days=7)),
    ]:
        row = GuidanceCall(
            user_id=UUID(credentials["user"]["id"]),
            step_id="summary",
            script_version="1.0.0",
            prompt_version="1.0.0",
            provider="gemini",
            model="test-only",
            prompt={"answer": "Conteudo ficticio privado"},
            response={"text": "Conteudo ficticio privado"},
            status="SUCCEEDED",
            created_at=now,
            expires_at=expiration,
        )
        db_session.add(row)
        rows.append(row)
    db_session.flush()
    active_id = rows[-1].id
    assert cleanup_expired(db_session, now=now) == 2
    assert db_session.scalar(select(func.count()).select_from(GuidanceCall)) == 1
    active = db_session.get(GuidanceCall, active_id)
    assert active is not None and active.prompt["answer"] == "Conteudo ficticio privado"
    # Explicit erasure keeps the active reservation, including its quota timestamp.
    from app.modules.users.models import User

    user = db_session.get(User, active.user_id)
    service.clear_history(db_session, user)
    assert active.prompt == {} and active.response is None
    assert cleanup_expired(db_session, now=now + timedelta(seconds=1)) == 0
    assert db_session.scalar(select(func.count()).select_from(GuidanceCall)) == 1
    assert active.created_at == now
