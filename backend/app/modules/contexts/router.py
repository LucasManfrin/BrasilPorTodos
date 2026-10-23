from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Query

from app.core.dependencies import DB, CurrentUser
from app.modules.contexts import service
from app.modules.contexts.schemas import (
    ContextCreate,
    ContextPublishInput,
    ContextReviewInput,
    ContextUpdate,
)

router = APIRouter(prefix="/api/v1/contexts", tags=["contexts"])


@router.get("")
def contexts(
    session: DB,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    q: Annotated[str | None, Query(max_length=120)] = None,
    indicator_code: Annotated[str | None, Query(max_length=100)] = None,
):
    return service.list_contexts(session, page, page_size, q, indicator_code=indicator_code)


@router.get("/mine")
def mine(
    session: DB,
    user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return service.list_contexts(session, page, page_size, user=user)


@router.get("/review-queue")
def queue(
    session: DB,
    user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return service.review_queue(session, user, page, page_size)


@router.get("/references/{code}")
def references(
    code: Annotated[str, Path(max_length=100)],
    session: DB,
    user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return service.reference_choices(session, user, code, page, page_size)


@router.post("", status_code=201)
def create(data: ContextCreate, session: DB, user: CurrentUser):
    return {"data": service.create_context(session, data, user)}


@router.patch("/{context_id}")
@router.put("/{context_id}")
def update(context_id: UUID, data: ContextUpdate, session: DB, user: CurrentUser):
    return {"data": service.update_context(session, context_id, data, user)}


@router.get("/{context_id}/draft")
def draft(context_id: UUID, session: DB, user: CurrentUser):
    return {"data": service.draft_view(session, context_id, user)}


@router.post("/{context_id}/review")
def review(context_id: UUID, data: ContextReviewInput, session: DB, user: CurrentUser):
    return {"data": service.review_context(session, context_id, data, user)}


@router.post("/{context_id}/publish")
def publish(context_id: UUID, data: ContextPublishInput, session: DB, user: CurrentUser):
    return {"data": service.publish_context(session, context_id, data, user)}


@router.get("/{context_id}/versions")
def versions(context_id: UUID, session: DB):
    return service.history(session, context_id)


@router.get("/{context_id}/versions/{revision}")
def version(context_id: UUID, revision: Annotated[int, Path(ge=1)], session: DB):
    return {"data": service.public_context(session, context_id, revision)}


@router.get("/{context_id}")
def context(context_id: UUID, session: DB):
    return {"data": service.public_context(session, context_id)}
