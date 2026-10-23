from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import DB, CurrentUser
from app.modules.guidance import service
from app.modules.guidance.impact import Sensitivity, analyze
from app.modules.guidance.schemas import OrganizeInput
from app.modules.policies.service import public_policy

router = APIRouter(prefix="/api/v1/guidance", tags=["proposal guidance"])


@router.get("/script")
def script():
    return {"data": service.script_view()}


@router.post("/organize")
def organize(data: OrganizeInput, session: DB, user: CurrentUser):
    return {"data": service.organize(session, user, data)}


@router.delete("/history")
def clear_history(session: DB, user: CurrentUser):
    return {"data": service.clear_history(session, user)}


@router.get("/calls/latest")
def latest_call_detail(session: DB, user: CurrentUser):
    return {"data": service.latest_call_detail(session, user)}


@router.get("/calls/{call_id}")
def call_detail(call_id: UUID, session: DB, user: CurrentUser):
    return {"data": service.call_detail(session, user, call_id)}


def sensitivity_parameters(
    cost_low: Annotated[str, Query(pattern=r"^(?:[01](?:\.\d{1,4})?|2(?:\.0{1,4})?)$")] = "1.00",
    cost_high: Annotated[str, Query(pattern=r"^(?:[01](?:\.\d{1,4})?|2(?:\.0{1,4})?)$")] = "1.00",
    gain_low: Annotated[str, Query(pattern=r"^(?:[01](?:\.\d{1,4})?|2(?:\.0{1,4})?)$")] = "1.00",
    gain_high: Annotated[str, Query(pattern=r"^(?:[01](?:\.\d{1,4})?|2(?:\.0{1,4})?)$")] = "1.00",
):
    from pydantic import ValidationError

    from app.core.errors import DomainError

    try:
        return Sensitivity(
            cost_low=cost_low, cost_high=cost_high, gain_low=gain_low, gain_high=gain_high
        )
    except ValidationError:
        raise DomainError(
            422,
            "INVALID_SENSITIVITY",
            "As faixas devem conter o valor declarado: mínimo até 1 e máximo entre 1 e 2.",
        ) from None


@router.get("/impact/{slug}")
def impact(
    slug: str,
    session: DB,
    assumptions: Annotated[Sensitivity, Depends(sensitivity_parameters)],
    version: Annotated[int | None, Query(ge=1)] = None,
):
    policy = public_policy(session, slug, version)
    return {"data": analyze(policy.version, assumptions)}
