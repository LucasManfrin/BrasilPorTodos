from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.core.dependencies import DB, CurrentUser
from app.modules.sources import service
from app.modules.sources.schemas import SourceEnvelope, SourceInput

router = APIRouter(prefix="/api/v1/sources", tags=["sources"])
Page = Annotated[int, Query(ge=1)]
Size = Annotated[int, Query(ge=1, le=100)]
Search = Annotated[str | None, Query(max_length=120)]


@router.get("")
def sources(
    session: DB,
    page: Page = 1,
    page_size: Size = 20,
    q: Search = None,
    institution: Search = None,
    source_type: Search = None,
):
    return service.list_sources(
        session, page, page_size, q, institution=institution, source_type=source_type
    )


@router.get("/mine")
def mine(session: DB, user: CurrentUser, page: Page = 1, page_size: Size = 20, q: Search = None):
    return service.list_sources(session, page, page_size, q, user)


@router.post("", response_model=SourceEnvelope, status_code=201)
def create(data: SourceInput, session: DB, user: CurrentUser):
    return {"data": service.create_source(session, data, user)}


@router.get("/{source_id}", response_model=SourceEnvelope)
def source(source_id: UUID, session: DB):
    return {"data": service.source_view(session, service.readable_source(session, source_id))}
