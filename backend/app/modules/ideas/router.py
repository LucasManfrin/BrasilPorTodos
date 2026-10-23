from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.core.dependencies import DB, CurrentUser
from app.modules.ideas import service
from app.modules.ideas.schemas import (
    IdeaInput,
    IdeaUpdate,
    ReportInput,
    ResolutionInput,
    SuggestionInput,
    SuggestionResolution,
)

router = APIRouter(prefix="/api/v1/ideas", tags=["ideas"])


@router.get("")
def listing(
    session: DB,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return service.listing(session, page, page_size)


@router.get("/mine")
def mine(
    session: DB,
    user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return service.listing(session, page, page_size, user)


@router.get("/moderation")
def moderation(session: DB, user: CurrentUser):
    return {"data": service.moderation(session, user)}


@router.post("/moderation/{report_id}/resolve")
def resolve(report_id: UUID, data: ResolutionInput, session: DB, user: CurrentUser):
    return {"data": service.resolve_report(session, report_id, data, user)}


@router.post("", status_code=201)
def create(data: IdeaInput, session: DB, user: CurrentUser):
    return {"data": service.create(session, data, user)}


@router.get("/{idea_id}")
def own(idea_id: UUID, session: DB, user: CurrentUser):
    return {"data": service.view(session, service.owned(session, idea_id, user))}


@router.get("/{idea_id}/shared")
def public(idea_id: UUID, session: DB):
    return {"data": service.shared(session, idea_id).shared_snapshot}


@router.patch("/{idea_id}")
def update(idea_id: UUID, data: IdeaUpdate, session: DB, user: CurrentUser):
    return {"data": service.update(session, idea_id, data, user)}


@router.post("/{idea_id}/share")
def share(idea_id: UUID, session: DB, user: CurrentUser):
    return {"data": service.share(session, idea_id, user)}


@router.post("/{idea_id}/unshare")
def unshare(idea_id: UUID, session: DB, user: CurrentUser):
    return {"data": service.unshare(session, idea_id, user)}


@router.post("/{idea_id}/duplicate", status_code=201)
def duplicate(idea_id: UUID, session: DB, user: CurrentUser):
    return {"data": service.duplicate(session, idea_id, user)}


@router.post("/{idea_id}/promote")
def promote(idea_id: UUID, session: DB, user: CurrentUser):
    return {"data": service.promote(session, idea_id, user)}


@router.post("/{idea_id}/suggestions", status_code=201)
def suggest(idea_id: UUID, data: SuggestionInput, session: DB, user: CurrentUser):
    return {"data": service.suggest(session, idea_id, data, user)}


@router.get("/{idea_id}/suggestions")
def suggestions(idea_id: UUID, session: DB, user: CurrentUser):
    return {"data": service.suggestions(session, idea_id, user)}


@router.post("/{idea_id}/suggestions/{suggestion_id}/resolve")
def resolve_suggestion(
    idea_id: UUID, suggestion_id: UUID, data: SuggestionResolution, session: DB, user: CurrentUser
):
    return {"data": service.resolve_suggestion(session, idea_id, suggestion_id, data.action, user)}


@router.post("/{idea_id}/report", status_code=201)
def report(idea_id: UUID, data: ReportInput, session: DB, user: CurrentUser):
    return {"data": service.report(session, idea_id, data, user)}
