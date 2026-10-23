from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Query

from app.core.dependencies import DB, CurrentUser
from app.modules.plans import service
from app.modules.plans.schemas import (
    ArchiveInput,
    FiscalScenarioConfirmation,
    PlanInput,
    PlanUpdate,
)

router = APIRouter(prefix="/api/v1/plans", tags=["plans"])


@router.get("")
def plans(
    session: DB,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    q: Annotated[str | None, Query(max_length=120)] = None,
    author: Annotated[str | None, Query(min_length=3, max_length=50)] = None,
    year: Annotated[int | None, Query(ge=1900, le=2200)] = None,
):
    return service.list_plans(session, page, page_size, q, author=author, year=year)


@router.get("/mine")
def mine(
    session: DB,
    user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return service.list_plans(session, page, page_size, user=user)


@router.post("", status_code=201)
def create(data: PlanInput, session: DB, user: CurrentUser):
    return {"data": service.create(session, data, user)}


@router.patch("/{plan_id}")
def update(plan_id: UUID, data: PlanUpdate, session: DB, user: CurrentUser):
    return {"data": service.update(session, plan_id, data, user)}


@router.get("/{plan_id}/draft")
def draft(plan_id: UUID, session: DB, user: CurrentUser):
    return {"data": service.draft(session, plan_id, user)}


@router.post("/{plan_id}/draft")
def new_draft(plan_id: UUID, session: DB, user: CurrentUser):
    return {"data": service.draft(session, plan_id, user, create=True)}


@router.post("/{plan_id}/fiscal-scenario/confirm")
def confirm_fiscal_scenario(
    plan_id: UUID, data: FiscalScenarioConfirmation, session: DB, user: CurrentUser
):
    return {
        "data": service.confirm_fiscal_scenario(session, plan_id, data.expected_input_hash, user)
    }


@router.post("/{plan_id}/simulate")
def simulate(plan_id: UUID, session: DB, user: CurrentUser):
    return {"data": service.simulate_plan(session, plan_id, user)}


@router.post("/{plan_id}/publish")
def publish(plan_id: UUID, session: DB, user: CurrentUser):
    return {"data": service.publish(session, plan_id, user)}


@router.post("/{plan_id}/archive")
def archive(plan_id: UUID, data: ArchiveInput, session: DB, user: CurrentUser):
    return {"data": service.archive(session, plan_id, user, data.reason)}


@router.get("/{slug}/versions")
def versions(slug: str, session: DB):
    return service.history(session, slug)


@router.get("/{slug}/versions/{number}")
def version(slug: str, number: Annotated[int, Path(ge=1)], session: DB):
    return {"data": service.public(session, slug, number)}


@router.get("/{slug}")
def plan(slug: str, session: DB):
    return {"data": service.public(session, slug)}
