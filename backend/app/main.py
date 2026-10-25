import json
import logging
from time import perf_counter
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from app.core.config import get_settings
from app.core.errors import DomainError
from app.database.session import get_session
from app.modules.admin.router import router as admin_router
from app.modules.auth.router import router as auth_router
from app.modules.contexts.router import router as contexts_router
from app.modules.graphs.router import router as graphs_router
from app.modules.guidance.router import router as guidance_router
from app.modules.ideas.router import router as ideas_router
from app.modules.indicators.router import router as indicators_router
from app.modules.plans.router import router as plans_router
from app.modules.policies.router import router as policies_router
from app.modules.sources.router import router as sources_router

logger = logging.getLogger("brasil_portodos.http")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False


def error_response(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


def create_app() -> FastAPI:
    application = FastAPI(title="BrasilPorTodos API", version="0.1.0")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origins,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_credentials=True,
        allow_headers=["Accept", "Content-Type", "Authorization", "X-CSRF-Token"],
    )

    application.include_router(contexts_router)
    application.include_router(graphs_router)
    application.include_router(guidance_router)
    application.include_router(ideas_router)
    application.include_router(admin_router)
    application.include_router(indicators_router)
    application.include_router(auth_router)
    application.include_router(sources_router)
    application.include_router(policies_router)
    application.include_router(plans_router)

    @application.exception_handler(DomainError)
    async def domain_error(request: Request, exc: DomainError):
        response = error_response(exc.status, exc.code, exc.message)
        response.headers["Cache-Control"] = "no-store"
        if exc.status == 401:
            response.headers["WWW-Authenticate"] = "Bearer"
        if exc.status == 429:
            response.headers["Retry-After"] = "60"
        return response

    @application.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError):
        # Driver messages can embed private values even with hide_parameters enabled.
        logger.error(
            json.dumps(
                {
                    "request_id": getattr(request.state, "request_id", None),
                    "error": "database_error",
                    "exception_type": type(exc).__name__,
                }
            )
        )
        response = error_response(
            500, "DATABASE_ERROR", "Não foi possível concluir a operação. Tente novamente."
        )
        response.headers["Cache-Control"] = "no-store"
        return response

    @application.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = str(uuid4())
        request.state.request_id = request_id
        started_at = perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        if request.headers.get("Authorization"):
            response.headers["Cache-Control"] = "no-store"
        logger.info(
            json.dumps(
                {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                }
            )
        )
        return response

    @application.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        message = "Recurso não encontrado." if exc.status_code == 404 else "Requisição recusada."
        response = error_response(exc.status_code, f"HTTP_{exc.status_code}", message)
        if exc.headers:
            response.headers.update(exc.headers)
        return response

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        labels = {
            "email": "e-mail",
            "password": "senha",
            "username": "nome de usuário",
            "amount": "valor fiscal",
            "year": "ano",
            "category": "categoria",
            "url": "link da fonte",
            "accessed_at": "data de acesso",
            "reference_date": "data de referência",
            "retrieved_at": "data de coleta",
            "source_type": "tipo da fonte",
            "implementation_start": "ano inicial",
            "implementation_end": "ano final",
            "start_year": "ano inicial",
            "end_year": "ano final",
            "reason": "motivo",
            "title": "título",
        }
        fields = sorted(
            {
                labels.get(str(error["loc"][-1]), "campos do formulário")
                for error in exc.errors()
                if error["loc"]
            }
        )
        message = (
            "Verifique os dados informados" + (": " + ", ".join(fields) if fields else "") + "."
        )
        return error_response(422, "VALIDATION_ERROR", message)

    @application.get("/api/v1/health", tags=["health"])
    def health():
        return {"data": {"status": "ok"}}

    @application.get("/api/v1/ready", tags=["health"])
    def ready(session: Annotated[Session, Depends(get_session)]):
        try:
            session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            return error_response(503, "DATABASE_UNAVAILABLE", "Banco de dados indisponível.")
        return {"data": {"status": "ready"}}

    return application


app = create_app()
