from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Query
from pydantic import BaseModel, ConfigDict, Field

from app.core.dependencies import DB, CurrentUser
from app.modules.policies import service
from app.modules.policies.schemas import Category, PolicyEnvelope, PolicyInput, PolicyUpdate

router = APIRouter(prefix="/api/v1/policies", tags=["policies"])


class ArchiveInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    reason: str = Field(min_length=1, max_length=2000)


@router.get("")
def policies(
    session: DB,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    q: Annotated[str | None, Query(max_length=120)] = None,
    category: Category | None = None,
    author: Annotated[str | None, Query(min_length=3, max_length=50)] = None,
    year: Annotated[int | None, Query(ge=1900, le=2200)] = None,
):
    return service.list_policies(session, page, page_size, q, category, author=author, year=year)


@router.get("/mine")
def mine(
    session: DB,
    user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return service.list_policies(session, page, page_size, user=user)


@router.post("", response_model=PolicyEnvelope, status_code=201)
def create(data: PolicyInput, session: DB, user: CurrentUser):
    return {"data": service.create_policy(session, data, user)}


@router.patch("/{policy_id}", response_model=PolicyEnvelope)
def update(policy_id: UUID, data: PolicyUpdate, session: DB, user: CurrentUser):
    return {"data": service.update_policy(session, policy_id, data, user)}


@router.get("/{policy_id}/draft", response_model=PolicyEnvelope)
def draft(policy_id: UUID, session: DB, user: CurrentUser):
    return {"data": service.draft_view(session, policy_id, user)}


@router.post("/{policy_id}/draft", response_model=PolicyEnvelope)
def new_draft(policy_id: UUID, session: DB, user: CurrentUser):
    return {"data": service.draft_view(session, policy_id, user, create=True)}


@router.post("/{policy_id}/publish", response_model=PolicyEnvelope)
def publish(policy_id: UUID, session: DB, user: CurrentUser):
    return {"data": service.publish_policy(session, policy_id, user)}


@router.post("/{policy_id}/archive", response_model=PolicyEnvelope)
def archive(policy_id: UUID, data: ArchiveInput, session: DB, user: CurrentUser):
    return {"data": service.archive(session, policy_id, user, data.reason)}


@router.get("/{slug}/versions")
def versions(slug: str, session: DB):
    return service.history(session, slug)


@router.get("/{slug}/versions/{version_number}", response_model=PolicyEnvelope)
def version(slug: str, version_number: Annotated[int, Path(ge=1)], session: DB):
    return {"data": service.public_policy(session, slug, version_number)}


@router.get("/{slug}", response_model=PolicyEnvelope)
def policy(slug: str, session: DB):
    return {"data": service.public_policy(session, slug)}


@router.delete("/{policy_id}/draft")
def remove_draft(policy_id: UUID, session: DB, user: CurrentUser):
    return service.delete_draft(session, policy_id, user)
