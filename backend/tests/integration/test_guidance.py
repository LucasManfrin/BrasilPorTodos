from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from app.core.errors import DomainError
from app.modules.guidance import service
from app.modules.guidance.models import GuidanceCall
from app.modules.guidance.provider import ProviderFailure, ProviderResult
from app.modules.guidance.schemas import OrganizeInput
from app.modules.guidance.settings import GuidanceSettings
from app.modules.ideas.models import Idea
from app.modules.users.models import User

from .test_auth import signup

pytestmark = pytest.mark.database


def settings(**kwargs):
    return GuidanceSettings(
        _env_file=None, guidance_ai_enabled=True, gemini_api_key="not-real", **kwargs
    )


class LiteralProvider:
    def organize(self, question, answer):
        return ProviderResult([answer], {"text": answer})


def actor(client, session):
    credentials, _ = signup(client)
    return session.get(User, UUID(credentials["user"]["id"]))


def test_private_log_quota_and_clearing_keep_usage_limit(auth_client, db_session):
    user = actor(auth_client, db_session)
    data = OrganizeInput(step_id="proposal", answer="Quero estudar uma mudança", consent=True)
    result = service.organize(
        db_session,
        user,
        data,
        settings=settings(guidance_daily_limit=1),
        provider=LiteralProvider(),
    )
    assert result["assisted_by_ai"]
    assert result["original_text"] == data.answer and result["rewritten"] is False
    row = db_session.scalar(select(GuidanceCall).where(GuidanceCall.user_id == user.id))
    assert row.status == "SUCCEEDED" and row.script_version == "1.0.0"
    assert row.prompt_version == "4.0.0"
    assert row.prompt["answer"] == data.answer and row.response["text"] == data.answer
    assert row.response["duration_ms"] >= 0
    assert service.clear_history(db_session, user) == {"cleared": 1}
    assert row.prompt == {} and row.response is None
    with pytest.raises(DomainError) as error:
        service.organize(
            db_session,
            user,
            data,
            settings=settings(guidance_daily_limit=1),
            provider=LiteralProvider(),
        )
    assert error.value.code == "GUIDANCE_LIMIT"


def test_provider_failure_and_invalid_structure_are_audited(auth_client, db_session):
    user = actor(auth_client, db_session)
    data = OrganizeInput(step_id="risks", answer="Pode dar errado", consent=True)

    class InvalidStructure:
        def organize(self, *_):
            return ProviderResult([], {"text": "missing segments"})

    class Fails:
        def organize(self, *_):
            raise ProviderFailure("test")

    for implementation, code in [
        (InvalidStructure(), "GUIDANCE_INVALID_OUTPUT"),
        (Fails(), "GUIDANCE_UNAVAILABLE"),
    ]:
        with pytest.raises(DomainError) as error:
            service.organize(db_session, user, data, settings=settings(), provider=implementation)
        assert error.value.code == code
    rows = db_session.scalars(select(GuidanceCall).where(GuidanceCall.user_id == user.id)).all()
    assert {row.status for row in rows} == {"FAILED", "REJECTED"}
    assert (
        next(row for row in rows if row.status == "REJECTED").error_code
        == "INVALID_RESPONSE_FORMAT"
    )


def test_real_rewrite_returns_original_and_suggestion_without_filling_fields(
    auth_client, db_session
):
    user = actor(auth_client, db_session)
    original = "quero fazer com o salario seja por horas trabalhadas"
    revised = "Quero que o salário seja pago por horas trabalhadas."

    class Copyeditor:
        def organize(self, question, answer):
            assert question == "Em uma frase, o que você quer mudar?"
            assert answer == original
            return ProviderResult([revised], {"text": revised})

    result = service.organize(
        db_session,
        user,
        OrganizeInput(step_id="summary", answer=original, consent=True),
        settings=settings(),
        provider=Copyeditor(),
    )
    assert result["original_text"] == original
    assert result["organized_text"] == revised
    assert result["rewritten"] is True and result["assisted_by_ai"] is True
    assert result["script_version"] == "1.0.0"
    row = db_session.scalar(select(GuidanceCall).where(GuidanceCall.user_id == user.id))
    assert row.prompt["answer"] == original and row.response["text"] == revised


def test_paragraph_only_reorganization_is_honestly_marked_unchanged(auth_client, db_session):
    user = actor(auth_client, db_session)

    class Paragraphs:
        def organize(self, question, answer):
            return ProviderResult(["Primeira frase.", "Segunda frase."], {"text": answer})

    result = service.organize(
        db_session,
        user,
        OrganizeInput(step_id="proposal", answer="Primeira frase. Segunda frase.", consent=True),
        settings=settings(),
        provider=Paragraphs(),
    )
    assert result["organized_text"] == "Primeira frase.\n\nSegunda frase."
    assert result["rewritten"] is False and result["assisted_by_ai"] is True


@pytest.mark.parametrize(
    "original, revised",
    [
        ("quero aumentar o tributo", "Quero aumentar o tributo."),
        ("quero reduzir o tributo", "Quero reduzir o tributo."),
        ("nao quero aumentar o tributo", "Não quero aumentar o tributo."),
        ("talvez eu queira reduzir o tributo", "Talvez eu queira reduzir o tributo."),
    ],
)
def test_opposite_positions_and_caveats_use_same_question(
    auth_client, db_session, original, revised
):
    user = actor(auth_client, db_session)

    class Copyeditor:
        def organize(self, question, answer):
            assert question == "O que mudaria na prática com a sua proposta?"
            return ProviderResult([revised], {"text": revised})

    result = service.organize(
        db_session,
        user,
        OrganizeInput(step_id="proposal", answer=original, consent=True),
        settings=settings(),
        provider=Copyeditor(),
    )
    assert result["original_text"] == original and result["organized_text"] == revised
    assert result["rewritten"] and result["assisted_by_ai"]


def test_one_user_cannot_clear_other_users_logs(auth_client, db_session):
    owner = actor(auth_client, db_session)
    other = actor(auth_client, db_session)
    data = OrganizeInput(step_id="summary", answer="Minha frase privada", consent=True)
    service.organize(db_session, owner, data, settings=settings(), provider=LiteralProvider())
    assert service.clear_history(db_session, other) == {"cleared": 0}
    assert (
        db_session.scalar(select(GuidanceCall).where(GuidanceCall.user_id == owner.id)).prompt[
            "answer"
        ]
        == data.answer
    )
    assert (
        db_session.scalar(
            select(func.count()).select_from(GuidanceCall).where(GuidanceCall.user_id == other.id)
        )
        == 0
    )


def test_guidance_routes_require_account_and_public_script_has_no_secret(auth_client):
    response = auth_client.get("/api/v1/guidance/script")
    assert response.status_code == 200
    assert response.json()["data"]["version"] == "1.0.0"
    assert "gemini_api_key" not in response.text
    assert (
        auth_client.post(
            "/api/v1/guidance/organize", json={"step_id": "title", "answer": "Ideia"}
        ).status_code
        == 401
    )
    assert auth_client.delete("/api/v1/guidance/history").status_code == 401


def test_erasure_during_pending_model_call_cannot_restore_response(auth_client, db_session):
    user = actor(auth_client, db_session)
    data = OrganizeInput(step_id="title", answer="Minha resposta privada", consent=True)

    class ClearsWhilePending:
        def organize(self, question, answer):
            assert service.clear_history(db_session, user) == {"cleared": 1}
            return ProviderResult([answer], {"text": answer})

    result = service.organize(
        db_session, user, data, settings=settings(), provider=ClearsWhilePending()
    )
    assert result["assisted_by_ai"]
    row = db_session.scalar(select(GuidanceCall).where(GuidanceCall.user_id == user.id))
    assert row.status == "SUCCEEDED" and row.cleared_at is not None
    assert row.prompt == {} and row.response is None


def test_http_accepts_frontend_four_decimal_multipliers(auth_client, db_session):
    from .test_policies import draft, headers

    credentials, _ = signup(auth_client)
    policy, _ = draft(auth_client, credentials)
    response = auth_client.post(
        f"/api/v1/policies/{policy['id']}/publish", headers=headers(credentials)
    )
    assert response.status_code == 200
    slug = response.json()["data"]["slug"]
    response = auth_client.get(
        f"/api/v1/guidance/impact/{slug}?version=1&cost_low=1.0000&cost_high=1.2000&gain_low=0.9999&gain_high=1.0000"
    )
    assert response.status_code == 200, response.text
    assert response.json()["data"]["available"] is False  # legacy is never reclassified
    assert auth_client.get(f"/api/v1/guidance/impact/{slug}?cost_high=2.0001").status_code == 422


@pytest.mark.parametrize(
    "status, message", [(503, "temporariamente indisponível"), (429, "limite de uso")]
)
def test_upstream_failure_is_explained_and_audited_without_filling_fields(
    auth_client, db_session, status, message
):
    user = actor(auth_client, db_session)

    class Unavailable:
        def organize(self, *_):
            raise ProviderFailure("provider_unavailable", http_status=status)

    with pytest.raises(DomainError) as error:
        service.organize(
            db_session,
            user,
            OrganizeInput(step_id="title", answer="Ideia fictícia", consent=True),
            settings=settings(),
            provider=Unavailable(),
        )
    assert error.value.code == "GUIDANCE_UNAVAILABLE"
    assert message in error.value.message
    row = db_session.scalar(select(GuidanceCall).where(GuidanceCall.user_id == user.id))
    assert row.status == "FAILED"
    assert row.error_code == f"PROVIDER_HTTP_{status}"
    assert row.response is None


def test_elaboration_with_confirmed_context_and_private_trace(auth_client, db_session):
    credentials, _ = signup(auth_client)
    user = db_session.get(User, UUID(credentials["user"]["id"]))
    context = {"title": "Atendimento local", "summary": "Ampliar atendimento em 2026"}
    original = "quero ampliar o atendimento"
    developed = "Quero ampliar o atendimento em 2026, com foco no acesso ao serviço."

    class Elaborates:
        def organize(self, question, answer, *, context):
            assert context["summary"] == "Ampliar atendimento em 2026"
            return ProviderResult(
                [developed],
                {
                    "text": "resposta estruturada",
                    "usage": {"totalTokenCount": 25},
                    "headers": {"Authorization": "not-to-export"},
                },
                ["Uma possibilidade é avaliar a implantação gradual."],
                ["Quem seria responsável pela execução?"],
            )

    result = service.organize(
        db_session,
        user,
        OrganizeInput(step_id="proposal", answer=original, context=context, consent=True),
        settings=settings(),
        provider=Elaborates(),
    )
    assert result["suggestions"] == ["Uma possibilidade é avaliar a implantação gradual."]
    assert result["open_questions"] == ["Quem seria responsável pela execução?"]
    assert result["organized_text"] == developed and result["original_text"] == original
    assert result["rewritten"] and result["assisted_by_ai"]
    call_id = UUID(result["call_id"])
    trace = service.call_detail(db_session, user, call_id)
    assert trace["request"]["context"] == context
    assert trace["request"]["answer"] == original
    assert trace["model"] == settings().guidance_model
    assert trace["script_version"] == "1.0.0" and trace["prompt_version"] == "4.0.0"
    assert trace["status"] == "SUCCEEDED" and trace["error_code"] is None
    assert trace["response"]["usage"] == {"totalTokenCount": 25}
    assert trace["response"]["duration_ms"] >= 0
    response = auth_client.get(
        f"/api/v1/guidance/calls/{call_id}",
        headers={"Authorization": f"Bearer {credentials['access_token']}"},
    )
    assert response.status_code == 200 and "not-to-export" not in response.text
    assert "gemini_api_key" not in response.text
    assert auth_client.get(f"/api/v1/guidance/calls/{call_id}").status_code == 401


@pytest.mark.parametrize("inaccessible", ["other_owner", "expired", "cleared", "missing"])
def test_private_trace_hides_owner_expired_cleared_and_missing_uniformly(
    auth_client, db_session, inaccessible
):
    user = actor(auth_client, db_session)
    result = service.organize(
        db_session,
        user,
        OrganizeInput(step_id="title", answer="Ideia", consent=True),
        settings=settings(),
        provider=LiteralProvider(),
    )
    call_id = UUID(result["call_id"])
    if inaccessible == "other_owner":
        user = actor(auth_client, db_session)
    elif inaccessible == "expired":
        row = db_session.get(GuidanceCall, call_id)
        row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        db_session.commit()
    elif inaccessible == "cleared":
        service.clear_history(db_session, user)
    else:
        call_id = uuid4()
    with pytest.raises(DomainError) as error:
        service.call_detail(db_session, user, call_id)
    assert error.value.status == 404 and error.value.code == "GUIDANCE_CALL_NOT_FOUND"
    assert error.value.message == "Registro não encontrado."


@pytest.mark.parametrize("extra", ["Custo R$ 100", "Fonte https://example.org"])
def test_options_are_returned_for_review_without_creating_an_idea(auth_client, db_session, extra):
    user = actor(auth_client, db_session)
    idea_count = db_session.scalar(select(func.count()).select_from(Idea))

    class Suggests:
        def organize(self, question, answer):
            return ProviderResult([answer], {"text": "option awaiting review"}, [extra])

    result = service.organize(
        db_session,
        user,
        OrganizeInput(step_id="proposal", answer="Minha ideia", consent=True),
        settings=settings(),
        provider=Suggests(),
    )
    assert result["original_text"] == result["organized_text"] == "Minha ideia"
    assert result["suggestions"] == [extra] and result["assisted_by_ai"]
    assert db_session.scalar(select(func.count()).select_from(Idea)) == idea_count
    row = db_session.scalar(select(GuidanceCall).where(GuidanceCall.user_id == user.id))
    assert row.status == "SUCCEEDED" and row.error_code is None


def test_changed_meaning_is_available_for_human_confirmation_not_auto_saved(
    auth_client, db_session
):
    user = actor(auth_client, db_session)
    original = "Pode dar errado"
    revised = "Não tem risco"
    idea_count = db_session.scalar(select(func.count()).select_from(Idea))

    class Rewrites:
        def organize(self, question, answer):
            assert answer == original
            return ProviderResult([revised], {"text": revised})

    result = service.organize(
        db_session,
        user,
        OrganizeInput(step_id="risks", answer=original, consent=True),
        settings=settings(),
        provider=Rewrites(),
    )
    assert result["original_text"] == original and result["organized_text"] == revised
    assert result["rewritten"] and result["assisted_by_ai"]
    assert db_session.scalar(select(func.count()).select_from(Idea)) == idea_count
    row = db_session.scalar(select(GuidanceCall).where(GuidanceCall.user_id == user.id))
    assert row.status == "SUCCEEDED" and row.prompt["answer"] == original
    assert row.response["text"] == revised


def test_invalid_extra_structure_is_rejected_and_audited(auth_client, db_session):
    user = actor(auth_client, db_session)

    class InvalidExtra:
        def organize(self, question, answer):
            return ProviderResult([answer], {"text": "invalid option"}, [None])

    with pytest.raises(DomainError) as error:
        service.organize(
            db_session,
            user,
            OrganizeInput(step_id="proposal", answer="Minha ideia", consent=True),
            settings=settings(),
            provider=InvalidExtra(),
        )
    assert error.value.code == "GUIDANCE_INVALID_OUTPUT"
    row = db_session.scalar(select(GuidanceCall).where(GuidanceCall.user_id == user.id))
    assert row.status == "REJECTED" and row.error_code == "INVALID_RESPONSE_FORMAT"


def test_title_is_bounded_without_suggestions_being_adopted(auth_client, db_session):
    user = actor(auth_client, db_session)

    class LongTitle:
        def organize(self, question, answer):
            return ProviderResult(["x" * 201], {"text": "too long"})

    with pytest.raises(DomainError) as error:
        service.organize(
            db_session,
            user,
            OrganizeInput(step_id="title", answer="Título", consent=True),
            settings=settings(),
            provider=LongTitle(),
        )
    assert error.value.code == "GUIDANCE_INVALID_OUTPUT"


@pytest.mark.parametrize("failure", ["FAILED", "REJECTED"])
def test_latest_trace_includes_failed_and_rejected_calls_for_owner(
    auth_client, db_session, failure
):
    credentials, _ = signup(auth_client)
    user = db_session.get(User, UUID(credentials["user"]["id"]))

    class Failure:
        def organize(self, question, answer):
            if failure == "FAILED":
                raise ProviderFailure("provider_unavailable", http_status=503)
            return ProviderResult([answer], {"text": "option not accepted"}, [None])

    with pytest.raises(DomainError):
        service.organize(
            db_session,
            user,
            OrganizeInput(step_id="proposal", answer="Ideia", consent=True),
            settings=settings(),
            provider=Failure(),
        )
    response = auth_client.get(
        "/api/v1/guidance/calls/latest",
        headers={"Authorization": f"Bearer {credentials['access_token']}"},
    )
    assert response.status_code == 200, response.text
    trace = response.json()["data"]
    assert trace["status"] == failure and trace["request"]["answer"] == "Ideia"
    assert trace["error_code"] == (
        "PROVIDER_HTTP_503" if failure == "FAILED" else "INVALID_RESPONSE_FORMAT"
    )
    assert (
        trace["response"] is None
        if failure == "FAILED"
        else trace["response"]["text"] == "option not accepted"
    )
    assert auth_client.get("/api/v1/guidance/calls/latest").status_code == 401


@pytest.mark.parametrize("inaccessible", ["other_owner", "expired", "cleared", "missing"])
def test_latest_trace_never_exposes_other_expired_or_cleared_calls(
    auth_client, db_session, inaccessible
):
    owner = actor(auth_client, db_session)
    if inaccessible != "missing":
        result = service.organize(
            db_session,
            owner,
            OrganizeInput(step_id="title", answer="Ideia", consent=True),
            settings=settings(),
            provider=LiteralProvider(),
        )
        if inaccessible == "other_owner":
            owner = actor(auth_client, db_session)
        elif inaccessible == "expired":
            row = db_session.get(GuidanceCall, UUID(result["call_id"]))
            row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
            db_session.commit()
        else:
            service.clear_history(db_session, owner)
    with pytest.raises(DomainError) as error:
        service.latest_call_detail(db_session, owner)
    assert error.value.status == 404 and error.value.code == "GUIDANCE_CALL_NOT_FOUND"


def test_latest_trace_selects_most_recent_eligible_call(auth_client, db_session):
    user = actor(auth_client, db_session)
    first = service.organize(
        db_session,
        user,
        OrganizeInput(step_id="title", answer="Primeira", consent=True),
        settings=settings(),
        provider=LiteralProvider(),
    )
    second = service.organize(
        db_session,
        user,
        OrganizeInput(step_id="title", answer="Segunda", consent=True),
        settings=settings(),
        provider=LiteralProvider(),
    )
    assert service.latest_call_detail(db_session, user)["id"] == second["call_id"]
    row = db_session.get(GuidanceCall, UUID(second["call_id"]))
    row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db_session.commit()
    assert service.latest_call_detail(db_session, user)["id"] == first["call_id"]
