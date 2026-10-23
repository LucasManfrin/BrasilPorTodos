from datetime import UTC, datetime, timedelta
from time import perf_counter
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.modules.guidance.models import GuidanceCall
from app.modules.guidance.provider import GeminiOrganizer, Organizer, ProviderFailure
from app.modules.guidance.schemas import OrganizeInput
from app.modules.guidance.script import (
    PROMPT_VERSION,
    SCRIPT,
    SYSTEM_PROMPT,
    get_step,
    normalized,
    unknown_answer,
    validate_extras,
    validate_segments,
)
from app.modules.guidance.settings import GuidanceSettings, get_guidance_settings
from app.modules.users.models import User


def script_view():
    settings = get_guidance_settings()
    return {
        **SCRIPT,
        "ai_available": settings.available,
        "provider": "gemini",
        "privacy": {
            "log_retention_days": settings.guidance_log_retention_days,
            "notice": "Ao usar IA, sua resposta e trechos confirmados são enviados ao Gemini. "
            "Pergunta, resposta e versões "
            "ficam em registro privado temporário. Não inclua dados pessoais sensíveis. "
            "Você pode continuar sem IA e apagar seus registros.",
        },
    }


def organize(
    session: Session,
    user: User,
    data: OrganizeInput,
    settings: GuidanceSettings | None = None,
    provider: Organizer | None = None,
):
    settings = settings or get_guidance_settings()
    step = get_step(data.step_id)
    unknown = unknown_answer(data.answer)
    result = {
        "step_id": step["id"],
        "question": step["question"],
        "script_version": SCRIPT["version"],
        "original_text": data.answer,
        "rewritten": False,
        "organized_text": "" if unknown else data.answer,
        "unknown": unknown,
        "assisted_by_ai": False,
        "suggestions": [],
        "open_questions": [],
        "call_id": None,
    }
    if unknown or not data.use_ai or not settings.available:
        return result
    if not data.consent:
        raise DomainError(
            422, "GUIDANCE_CONSENT_REQUIRED", "Confirme o envio ao Gemini ou continue sem IA."
        )
    now = datetime.now(UTC)
    # Serialize reservation per user; failed/invalid responses count toward the quota too.
    session.scalar(select(User).where(User.id == user.id).with_for_update())
    session.execute(delete(GuidanceCall).where(GuidanceCall.expires_at <= now))
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    count = session.scalar(
        select(func.count())
        .select_from(GuidanceCall)
        .where(GuidanceCall.user_id == user.id, GuidanceCall.created_at >= today)
    )
    recent = session.scalar(
        select(func.count())
        .select_from(GuidanceCall)
        .where(
            GuidanceCall.user_id == user.id, GuidanceCall.created_at >= now - timedelta(minutes=1)
        )
    )
    if count >= settings.guidance_daily_limit or recent >= 5:
        session.rollback()
        raise DomainError(
            429,
            "GUIDANCE_LIMIT",
            "Limite de assistência atingido. Continue sem IA ou tente mais tarde.",
        )
    call = GuidanceCall(
        user_id=user.id,
        created_at=now,
        step_id=step["id"],
        script_version=SCRIPT["version"],
        prompt_version=PROMPT_VERSION,
        provider="gemini",
        model=settings.guidance_model,
        prompt={
            "system": SYSTEM_PROMPT,
            "question": step["question"],
            "answer": data.answer,
            "context": data.context,
        },
        status="PENDING",
        expires_at=now + timedelta(days=settings.guidance_log_retention_days),
    )
    session.add(call)
    session.commit()
    started = perf_counter()
    try:
        organizer = provider or GeminiOrganizer(settings)
        generated = organizer.organize(
            step["question"], data.answer, **({"context": data.context} if data.context else {})
        )
        call = session.scalar(
            select(GuidanceCall)
            .where(GuidanceCall.id == call.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if call.cleared_at is None:
            call.response = {
                **generated.response,
                "duration_ms": round((perf_counter() - started) * 1000, 2),
            }
        try:
            text = validate_segments(data.answer, generated.segments, context=data.context)
            if step["id"] == "title" and len(text) > 200:
                raise ValueError("Título deve ter até 200 caracteres.")
            known = "\n".join([data.answer, *data.context.values()])
            suggestions = validate_extras(generated.suggestions, known=known)
            open_questions = validate_extras(generated.open_questions, known=known, questions=True)
        except ValueError:
            call.status = "REJECTED"
            call.error_code = "INVALID_RESPONSE_FORMAT"
            session.commit()
            raise DomainError(
                502,
                "GUIDANCE_INVALID_OUTPUT",
                "O Gemini retornou uma resposta fora do formato ou tamanho esperado. "
                "Tente novamente ou siga com seu texto original.",
            ) from None
        call.status = "SUCCEEDED"
        session.commit()
    except ProviderFailure as failure:
        call = session.scalar(
            select(GuidanceCall)
            .where(GuidanceCall.id == call.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        call.status = "FAILED"
        call.error_code = (
            f"PROVIDER_HTTP_{failure.http_status}"
            if failure.http_status is not None
            else "PROVIDER_UNAVAILABLE"
        )
        session.commit()
        raise DomainError(
            502,
            "GUIDANCE_UNAVAILABLE",
            {
                429: "O Gemini atingiu um limite de uso. Aguarde e tente novamente ou siga sem IA.",
                503: "O Gemini está temporariamente indisponível. Sua resposta foi preservada; "
                "tente novamente ou siga sem IA.",
                401: "O Gemini recusou a autenticação. Confira a chave no backend ou siga sem IA.",
                403: "O Gemini recusou o acesso. Confira a chave e as permissões ou siga sem IA.",
                404: "O modelo Gemini configurado não está disponível. "
                "Confira o modelo no backend.",
            }.get(
                failure.http_status,
                "O Gemini não respondeu. Sua resposta continua aqui; você pode seguir sem IA.",
            ),
        ) from None
    return {
        **result,
        "organized_text": text,
        "assisted_by_ai": True,
        "rewritten": normalized(text) != normalized(data.answer),
        "suggestions": suggestions,
        "open_questions": open_questions,
        "call_id": str(call.id),
    }


def latest_call_detail(session: Session, user: User):
    call_id = session.scalar(
        select(GuidanceCall.id)
        .where(
            GuidanceCall.user_id == user.id,
            GuidanceCall.cleared_at.is_(None),
            GuidanceCall.expires_at > datetime.now(UTC),
        )
        .order_by(GuidanceCall.created_at.desc(), GuidanceCall.id.desc())
        .limit(1)
    )
    if call_id is None:
        raise DomainError(404, "GUIDANCE_CALL_NOT_FOUND", "Registro não encontrado.")
    return call_detail(session, user, call_id)


def call_detail(session: Session, user: User, call_id: UUID):
    row = session.scalar(
        select(GuidanceCall).where(
            GuidanceCall.id == call_id,
            GuidanceCall.user_id == user.id,
            GuidanceCall.cleared_at.is_(None),
            GuidanceCall.expires_at > datetime.now(UTC),
        )
    )
    if row is None:
        raise DomainError(404, "GUIDANCE_CALL_NOT_FOUND", "Registro não encontrado.")
    # Explicit projection excludes all transport headers and credentials.
    return {
        "id": str(row.id),
        "step_id": row.step_id,
        "provider": row.provider,
        "model": row.model,
        "status": row.status,
        "error_code": row.error_code,
        "script_version": row.script_version,
        "prompt_version": row.prompt_version,
        "created_at": row.created_at,
        "expires_at": row.expires_at,
        "request": {
            name: row.prompt.get(name) for name in ("system", "question", "answer", "context")
        },
        "response": (
            {name: row.response.get(name) for name in ("text", "usage", "duration_ms")}
            if row.response is not None
            else None
        ),
    }


def clear_history(session: Session, user: User):
    # Deletion is explicitly requested by the authenticated owner; quota is separately retained.
    rows = session.scalars(
        select(GuidanceCall).where(GuidanceCall.user_id == user.id).with_for_update()
    ).all()
    for row in rows:
        row.cleared_at = datetime.now(UTC)
        row.prompt = {}
        row.response = None
    session.commit()
    return {"cleared": len(rows)}
