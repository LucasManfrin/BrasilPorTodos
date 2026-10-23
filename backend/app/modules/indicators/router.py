from typing import Annotated, Literal

from fastapi import APIRouter, Query

from app.core.dependencies import DB
from app.modules.indicators import service

router = APIRouter(prefix="/api/v1/indicators", tags=["indicators"])


@router.get("")
def indicators(
    session: DB,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    q: Annotated[str | None, Query(max_length=120)] = None,
    category: Literal["ECONOMY", "FISCAL", "SOCIAL", "PUBLIC_SPENDING"] | None = None,
):
    return service.catalog(session, page, page_size, q, category)


@router.get("/collection/status")
def collection_status(session: DB):
    from app.modules.indicators.collection import status

    return {"data": status(session)}


@router.get("/baseline/current")
def baseline_current(session: DB):
    from app.modules.indicators.baseline import current

    return {"data": current(session)}


@router.get("/baseline/fiscal")
def fiscal_baseline_current(session: DB):
    from app.modules.indicators.fiscal_baseline import current

    return {"data": current(session)}


@router.get("/baseline/composition")
def fiscal_composition_current(session: DB):
    from app.modules.indicators.fiscal_composition import current

    return {"data": current(session)}


@router.get("/baseline/interest")
def fiscal_interest_current(session: DB):
    from app.modules.indicators.fiscal_interest import current

    return {"data": current(session)}


@router.get("/spending/functions")
def fiscal_spending_current(session: DB):
    from app.modules.indicators.fiscal_spending import current

    return {"data": current(session)}


@router.get("/government/general")
def general_government_current(session: DB):
    from app.modules.indicators.general_government import current

    return {"data": current(session)}


@router.get("/{code}")
def indicator(
    code: str,
    session: DB,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return service.detail(session, code, page, page_size)
