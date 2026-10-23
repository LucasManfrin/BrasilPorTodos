"""Observed spending by budget function; never an implicit bridge to primary RTN."""

from copy import deepcopy
from datetime import UTC, date, datetime

from sqlalchemy import select, text

from app.integrations import federal_spending as provider
from app.modules.admin.models import record
from app.modules.indicators.fiscal_baseline import current as current_fiscal
from app.modules.indicators.models import FiscalSpendingCohort
from app.modules.sources.models import Source

METHOD = (
    "Pagamentos da fonte federal por função orçamentária, natureza e mês. Pago no "
    "exercício + restos a pagar pagos = pagamentos totais. Registros são normalizados "
    "a centavos por linha com half-even, mantendo valores assinados e grupos sem "
    "classificação. Todos os estágios e dimensões pertencem à mesma revisão do arquivo. "
    "A referência RTN escolhe apenas o ano; não reconciliamos estes valores com a "
    "despesa primária por pagamento efetivo do RTN."
)
LIMITATIONS = [
    "Recorte federal/OFSS da fonte, não Saúde ou Educação de todos os entes.",
    "Ordem bancária/valor pago, RAP e Extra-Siafi diferem do pagamento efetivo do RTN.",
    "Naturezas Primária, Financeira e Extra-Siafi permanecem distintas, com sinais publicados.",
    "Funções sem classificação N/A e OUTRAS não são Reserva de Contingência, "
    "embora compartilhem código 99.",
    "Grupo ausente não é zero; pagamentos negativos preservam ajustes da fonte.",
    "Pagamento não mede qualidade do serviço, mínimos constitucionais "
    "ou margem disponível para cortes.",
    "Centavos seguem uma política versionada de normalização; "
    "frações originais são auditáveis nos agregados.",
    "A reconciliação com o resumo publicado cobre um subconjunto explícito; "
    "não valida independentemente cada função.",
    "Esta camada não altera snapshots, a base primária, o motor fiscal ou previsões futuras.",
]


def source_snapshot(payload):
    return {
        **deepcopy(payload["source"]),
        "source_type": "OFFICIAL",
        "is_example": False,
        "description": (
            f"Dados oficiais de {payload['source']['institution']}. "
            f"Termos: {payload['source']['license']}. {payload['source']['license_url']}"
        ),
    }


def assemble(cohort, year, source=None):
    """Validate the selected revision first; invalid latest revisions never fall back."""
    result = {
        "status": "INCOMPLETE" if cohort else "EMPTY",
        "year": year,
        "period_start": date(year, 1, 1).isoformat() if year else None,
        "period_end": date(year, 12, 31).isoformat() if year else None,
        "collected_at": None,
        "revision": None,
        "cohort_fingerprint": None,
        "source": None,
        "payload": None,
        "methodology": METHOD,
        "limitations": list(LIMITATIONS),
        "missing": ["Conjunto funcional íntegro dos doze meses do ano de referência"],
    }
    if year is None:
        result["missing"] = ["Ano fechado da referência fiscal observada disponível"]
        return result
    if cohort is None:
        return result
    try:
        payload = cohort["payload"]
        provider.validate_payload(payload)
        expected = source_snapshot(payload)
        if (
            payload["year"] != year
            or cohort["year"] != year
            or cohort["source_hash"] != payload["resource"]["sha256"]
            or cohort["parser_version"] != payload["parser_version"]
            or cohort["precision_version"] != payload["precision_version"]
            or cohort["cohort_fingerprint"] != payload["fingerprint"]
            or provider.fingerprint(payload) != payload["fingerprint"]
            or cohort["source_snapshot"] != expected
            or type(cohort["revision"]) is not int
            or cohort["revision"] <= 0
            or source is None
            or any(
                source.get(key) != expected[key]
                for key in (
                    "title",
                    "institution",
                    "url",
                    "source_type",
                    "is_example",
                    "description",
                )
            )
        ):
            return result
        retrieved = datetime.fromisoformat(cohort["retrieved_at"])
        if retrieved.tzinfo is None or retrieved > datetime.now(UTC):
            return result
    except (KeyError, TypeError, ValueError):
        return result
    result.update(
        status="AVAILABLE",
        collected_at=cohort["retrieved_at"],
        revision=cohort["revision"],
        cohort_fingerprint=cohort["cohort_fingerprint"],
        source=deepcopy(expected),
        payload=deepcopy(payload),
        missing=[],
    )
    return result


def cohort_view(row):
    return {
        key: getattr(row, key)
        for key in (
            "year",
            "revision",
            "source_hash",
            "parser_version",
            "precision_version",
            "cohort_fingerprint",
            "source_snapshot",
            "payload",
        )
    } | {"retrieved_at": row.retrieved_at.isoformat()}


def source_view(row):
    return (
        {
            key: getattr(row, key)
            for key in (
                "title",
                "institution",
                "url",
                "source_type",
                "is_example",
                "description",
            )
        }
        if row
        else None
    )


def latest(session, year):
    return session.scalar(
        select(FiscalSpendingCohort)
        .where(FiscalSpendingCohort.year == year)
        .order_by(FiscalSpendingCohort.revision.desc())
        .limit(1)
    )


def current(session):
    fiscal = current_fiscal(session)
    year = fiscal["year"] if fiscal["status"] == "AVAILABLE" else None
    row = latest(session, year) if year else None
    source = session.get(Source, row.source_id) if row else None
    return assemble(cohort_view(row) if row else None, year, source_view(source))


def save_cohort(session, actor, payload, *, commit=True):
    """Called by the reviewed collector only; source collisions do not publish private metadata."""
    provider.validate_payload(payload)
    year = payload["year"]
    if not 1997 <= year < datetime.now(UTC).year:
        raise ValueError("A cohort must cover one closed year.")
    # Coordinates revision numbering even when an operator calls this service directly.
    session.execute(text("SELECT pg_advisory_xact_lock(82461302, :year)"), {"year": year})
    expected = source_snapshot(payload)
    fingerprint = provider.fingerprint(payload)
    if fingerprint != payload["fingerprint"]:
        raise ValueError("Invalid spending cohort fingerprint.")
    existing = session.scalar(
        select(FiscalSpendingCohort).where(
            FiscalSpendingCohort.year == year,
            FiscalSpendingCohort.source_hash == payload["resource"]["sha256"],
            FiscalSpendingCohort.parser_version == payload["parser_version"],
            FiscalSpendingCohort.precision_version == payload["precision_version"],
        )
    )
    newest = latest(session, year)
    if existing:
        if (
            existing.cohort_fingerprint != fingerprint
            or existing.source_snapshot != expected
            or newest.id != existing.id
        ):
            raise ValueError(
                "Known file has different semantics or would revert the latest cohort."
            )
        source = session.get(Source, existing.source_id)
        if assemble(cohort_view(existing), year, source_view(source))["status"] != "AVAILABLE":
            raise ValueError("Existing latest cohort is incompatible; do not silently reuse it.")
        if commit:
            session.commit()
        return existing
    source = session.scalar(
        select(Source)
        .where(
            Source.created_by == actor.id,
            Source.title == expected["title"],
            Source.institution == expected["institution"],
            Source.url == expected["url"],
            Source.source_type == "OFFICIAL",
            Source.is_example.is_(False),
            Source.description == expected["description"],
        )
        .order_by(Source.created_at, Source.id)
        .limit(1)
    )
    if source is None:
        source = Source(
            created_by=actor.id,
            accessed_at=datetime.now(UTC).date(),
            **{
                key: expected[key]
                for key in (
                    "title",
                    "institution",
                    "url",
                    "source_type",
                    "description",
                    "is_example",
                )
            },
        )
        session.add(source)
        session.flush()
    row = FiscalSpendingCohort(
        year=year,
        revision=(newest.revision + 1 if newest else 1),
        source_id=source.id,
        created_by=actor.id,
        retrieved_at=datetime.now(UTC),
        source_hash=payload["resource"]["sha256"],
        parser_version=payload["parser_version"],
        precision_version=payload["precision_version"],
        cohort_fingerprint=fingerprint,
        source_snapshot=expected,
        payload=deepcopy(payload),
    )
    session.add(row)
    session.flush()
    record(
        session,
        actor,
        "fiscal_spending_cohort",
        row.id,
        "CREATE",
        "Coleta oficial de gasto funcional federal",
        {
            "year": year,
            "revision": row.revision,
            "source_hash": row.source_hash,
            "cohort_fingerprint": fingerprint,
        },
    )
    if commit:
        session.commit()
    return row
