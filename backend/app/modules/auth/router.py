from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import DomainError
from app.database.session import get_session
from app.modules.auth import service
from app.modules.auth.dependencies import current_user
from app.modules.auth.schemas import AuthEnvelope, LoginInput, RegisterInput, UserEnvelope
from app.modules.users.models import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
DB = Annotated[Session, Depends(get_session)]
Config = Annotated[Settings, Depends(get_settings)]
CurrentUser = Annotated[User, Depends(current_user)]


def check_origin(request: Request, settings: Settings) -> None:
    origin = request.headers.get("Origin")
    if origin is not None and origin not in settings.cors_origins:
        raise DomainError(403, "ORIGIN_REJECTED", "Origem da requisição não permitida.")


def credentials_response(response: Response, result, refresh: str, settings: Settings):
    options = {
        "secure": settings.cookie_secure,
        "samesite": "strict",
        "max_age": settings.refresh_days * 86400,
    }
    response.set_cookie("bpt_refresh", refresh, httponly=True, path="/api/v1/auth", **options)
    response.set_cookie("bpt_csrf", result["csrf_token"], httponly=False, path="/", **options)
    response.headers["Cache-Control"] = "no-store"
    return {"data": result}


@router.get("/username-availability")
def username_availability(
    request: Request,
    response: Response,
    session: DB,
    username: Annotated[str, Query(min_length=3, max_length=50, pattern=r"^[a-z0-9_]+$")],
):
    service.consume_rate_limits(
        session, "username", request.client.host if request.client else "unknown"
    )
    response.headers["Cache-Control"] = "no-store"
    return {
        "data": {
            "available": session.scalar(select(User.id).where(User.username == username)) is None
        }
    }


@router.post("/register", response_model=AuthEnvelope, status_code=201)
def register(
    data: RegisterInput, request: Request, response: Response, session: DB, settings: Config
):
    check_origin(request, settings)
    service.consume_rate_limits(
        session, "register", request.client.host if request.client else "unknown", str(data.email)
    )
    result, refresh = service.register(session, data, settings)
    return credentials_response(response, result, refresh, settings)


@router.post("/login", response_model=AuthEnvelope)
def login(data: LoginInput, request: Request, response: Response, session: DB, settings: Config):
    check_origin(request, settings)
    service.consume_rate_limits(
        session, "login", request.client.host if request.client else "unknown", str(data.email)
    )
    result, refresh = service.login(session, data, settings)
    return credentials_response(response, result, refresh, settings)


@router.post("/refresh", response_model=AuthEnvelope)
def refresh(request: Request, response: Response, session: DB, settings: Config):
    check_origin(request, settings)
    service.consume_rate_limits(
        session, "refresh", request.client.host if request.client else "unknown"
    )
    result, new_refresh = service.refresh(
        session, request.cookies.get("bpt_refresh"), request.headers.get("X-CSRF-Token"), settings
    )
    return credentials_response(response, result, new_refresh, settings)


@router.post("/logout")
def logout(request: Request, response: Response, session: DB, settings: Config):
    check_origin(request, settings)
    service.consume_rate_limits(
        session, "logout", request.client.host if request.client else "unknown"
    )
    service.logout(session, request.cookies.get("bpt_refresh"), request.headers.get("X-CSRF-Token"))
    response.delete_cookie(
        "bpt_refresh",
        path="/api/v1/auth",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="strict",
    )
    response.delete_cookie("bpt_csrf", path="/", secure=settings.cookie_secure, samesite="strict")
    response.headers["Cache-Control"] = "no-store"
    return {"data": {"status": "logged_out"}}


@router.get("/me", response_model=UserEnvelope)
def me(user: CurrentUser, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return {"data": user}
