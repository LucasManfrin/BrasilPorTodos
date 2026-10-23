from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.database.models import (
    FinancialImpact,
    Plan,
    PlanPolicy,
    PlanVersion,
    Policy,
    PolicyVersion,
    User,
)

pytestmark = pytest.mark.database


def author(session):
    token = uuid4().hex
    user = User(
        name="Test", username=token, email=f"{token}@example.test", password_hash="test-only"
    )
    session.add(user)
    session.flush()
    return user


def draft_policy(session, user):
    policy = Policy(author_id=user.id, slug=uuid4().hex)
    session.add(policy)
    session.flush()
    version = PolicyVersion(
        policy_id=policy.id,
        created_by=user.id,
        version_number=1,
        financial_impact_status="ESTIMATED",
    )
    session.add(version)
    session.flush()
    return policy, version


def publish(session, policy, version):
    version.status = "PUBLISHED"
    version.published_at = datetime.now(UTC)
    session.flush()
    policy.status = "PUBLISHED"
    policy.current_version_id = version.id
    session.flush()


def test_one_active_draft_per_identity(db_session):
    user = author(db_session)
    policy, _ = draft_policy(db_session, user)
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(PolicyVersion(policy_id=policy.id, created_by=user.id, version_number=2))
        db_session.flush()


def test_public_pointer_cannot_reference_draft_or_other_identity(db_session):
    user = author(db_session)
    policy, draft = draft_policy(db_session, user)
    with pytest.raises(IntegrityError), db_session.begin_nested():
        policy.status = "PUBLISHED"
        policy.current_version_id = draft.id
        db_session.flush()
        db_session.execute(text("SET CONSTRAINTS fk_policy_current_version IMMEDIATE"))
    db_session.expire_all()
    other, published = draft_policy(db_session, user)
    publish(db_session, other, published)
    with pytest.raises(IntegrityError), db_session.begin_nested():
        policy.status = "PUBLISHED"
        policy.current_version_id = published.id
        db_session.flush()
        db_session.execute(text("SET CONSTRAINTS fk_policy_current_version IMMEDIATE"))


def test_published_version_and_its_amounts_are_frozen(db_session):
    user = author(db_session)
    policy, version = draft_policy(db_session, user)
    impact = FinancialImpact(
        policy_version_id=version.id,
        year=2030,
        impact_type="NEW_EXPENSE",
        amount=Decimal("0.10"),
        description="Fictitious test",
    )
    db_session.add(impact)
    db_session.flush()
    publish(db_session, policy, version)
    for statement in (
        "UPDATE policy_versions SET title='changed' WHERE id=:id",
        "DELETE FROM policy_versions WHERE id=:id",
        "UPDATE financial_impacts SET amount=9 WHERE policy_version_id=:id",
        "DELETE FROM financial_impacts WHERE policy_version_id=:id",
        "INSERT INTO financial_impacts "
        "(id, policy_version_id, year, impact_type, amount, description) "
        "VALUES (gen_random_uuid(), :id, 2030, 'NEW_EXPENSE', 9, 'changed')",
    ):
        with pytest.raises(IntegrityError), db_session.begin_nested():
            db_session.execute(text(statement), {"id": version.id})
    db_session.refresh(impact)
    assert impact.amount == Decimal("0.10")
    assert version.created_at.tzinfo is not None


def test_plan_keeps_pinned_version_when_policy_v2_is_published(db_session):
    user = author(db_session)
    policy, v1 = draft_policy(db_session, user)
    publish(db_session, policy, v1)
    plan = Plan(author_id=user.id, slug=uuid4().hex)
    db_session.add(plan)
    db_session.flush()
    plan_version = PlanVersion(
        plan_id=plan.id, created_by=user.id, version_number=1, start_year=2030, end_year=2035
    )
    db_session.add(plan_version)
    db_session.flush()
    item = PlanPolicy(plan_version_id=plan_version.id, policy_version_id=v1.id, position=0)
    db_session.add(item)
    db_session.flush()
    plan_version.status = "PUBLISHED"
    plan_version.published_at = datetime.now(UTC)
    db_session.flush()
    plan.status = "PUBLISHED"
    plan.current_version_id = plan_version.id
    db_session.flush()
    v2 = PolicyVersion(policy_id=policy.id, created_by=user.id, version_number=2)
    db_session.add(v2)
    db_session.flush()
    publish(db_session, policy, v2)
    db_session.refresh(item)
    assert item.policy_version_id == v1.id
    with pytest.raises(IntegrityError), db_session.begin_nested():
        item.policy_version_id = v2.id
        db_session.flush()


def test_plan_rejects_duplicate_items_and_draft_policy(db_session):
    user = author(db_session)
    policy, version = draft_policy(db_session, user)
    plan = Plan(author_id=user.id, slug=uuid4().hex)
    db_session.add(plan)
    db_session.flush()
    plan_version = PlanVersion(
        plan_id=plan.id, created_by=user.id, version_number=1, start_year=2030, end_year=2031
    )
    db_session.add(plan_version)
    db_session.flush()
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(
            PlanPolicy(plan_version_id=plan_version.id, policy_version_id=version.id, position=0)
        )
        db_session.flush()
    publish(db_session, policy, version)
    db_session.add(
        PlanPolicy(plan_version_id=plan_version.id, policy_version_id=version.id, position=0)
    )
    db_session.flush()
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(
            PlanPolicy(plan_version_id=plan_version.id, policy_version_id=version.id, position=1)
        )
        db_session.flush()


@pytest.mark.parametrize("amount", [Decimal("-0.01"), Decimal("NaN")])
def test_invalid_fiscal_magnitudes_are_rejected_by_database(db_session, amount):
    user = author(db_session)
    _, version = draft_policy(db_session, user)
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(
            FinancialImpact(
                policy_version_id=version.id,
                year=2030,
                impact_type="NEW_EXPENSE",
                amount=amount,
                description="Fictitious test",
            )
        )
        db_session.flush()
