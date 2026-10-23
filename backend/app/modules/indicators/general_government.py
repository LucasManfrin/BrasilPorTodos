"""Official general-government statistics; never an implicit bridge to primary RTN."""

from copy import deepcopy
from datetime import UTC, date, datetime

from sqlalchemy import select, text

from app.integrations import general_government as provider
from app.modules.admin.models import record
from app.modules.indicators.fiscal_baseline import current as current_fiscal
from app.modules.indicators.models import GeneralGovernmentCohort
from app.modules.sources.models import Source

METHOD = (
    "Estatísticas anuais publicadas do Governo Geral, segundo o GFSM 2014 e "
    "competência modificada. Governo Central, estados, municípios e eliminações de "
    "consolidação pertencem à mesma revisão da publicação. Despesa agregada (2M) "
    "é gasto (2) mais investimento líquido (31); receita (1) menos despesa "
    "agregada (2M) produz a capacidade/necessidade de financiamento. Juros "
    "recebidos e pagos permitem conferir o resultado primário "
    "desta fonte. Valores originais em milhões são normalizados com Decimal, "
    "mantendo a precisão e as diferenças publicadas. O RTN escolhe somente o ano; "
    "esta camada não troca seu critério de pagamento efetivo nem soma entes ao RTN."
)
LIMITATIONS = [
    "Competência modificada/GFSM 2014 difere do caixa e pagamento efetivo do RTN.",
    "O Governo Central desta publicação exclui o Banco Central; "
    "não equivale ao recorte Governo Central RTN.",
    "O universo da fonte inclui 27 unidades estaduais e 5.570 municipais; "
    "recebimento municipal aproximado de 90%, com extrapolação publicada pelo Tesouro.",
    "Municípios são estimativa oficial publicada para a cobertura indicada; "
    "não uma soma de declarações completas de todos os municípios.",
    "Eliminações de consolidação preservam seus sinais; "
    "somar entes sem elas duplica operações entre governos.",
    "Investimento líquido é distinto de investimento bruto ou gasto orçamentário; "
    "pode ser negativo.",
    "A publicação é anual e revisável; a conferência de identidades da mesma "
    "fonte não constitui auditoria externa ou avaliação de uma política.",
    "Valores normalizados em reais mantêm proveniência em milhões; "
    "a representação em centavos não aumenta a precisão da fonte.",
    "Esta camada não altera snapshots publicados, indicadores contextuais, "
    "a referência RTN, o motor fiscal ou previsões futuras.",
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
    valid_year = type(year) is int and 2010 <= year < datetime.now(UTC).year
    result = {
        "status": "INCOMPLETE" if cohort else "EMPTY",
        "year": year,
        "period_start": date(year, 1, 1).isoformat() if valid_year else None,
        "period_end": date(year, 12, 31).isoformat() if valid_year else None,
        "collected_at": None,
        "revision": None,
        "cohort_fingerprint": None,
        "source": None,
        "payload": None,
        "methodology": METHOD,
        "limitations": list(LIMITATIONS),
        "missing": ["Estatística anual íntegra do Governo Geral no ano de referência"],
    }
    if not valid_year:
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
            or type(cohort["year"]) is not int
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
        select(GeneralGovernmentCohort)
        .where(GeneralGovernmentCohort.year == year)
        .order_by(GeneralGovernmentCohort.revision.desc())
        .limit(1)
    )


def current(session):
    fiscal = current_fiscal(session)
    year = fiscal["year"] if fiscal["status"] == "AVAILABLE" else None
    row = latest(session, year) if year else None
    source = session.get(Source, row.source_id) if row else None
    return assemble(
        cohort_view(row) if row else None,
        year,
        source_view(source) if source and source.created_by == row.created_by else None,
    )


def save_cohort(session, actor, payload, *, commit=True):
    """Called by the reviewed collector only; source collisions do not publish private metadata."""
    provider.validate_payload(payload)
    year = payload["year"]
    if type(year) is not int or not 2010 <= year < datetime.now(UTC).year:
        raise ValueError("A cohort must cover one closed year.")
    # Coordinates revision numbering even when an operator calls this service directly.
    session.execute(text("SELECT pg_advisory_xact_lock(82461303, :year)"), {"year": year})
    expected = source_snapshot(payload)
    fingerprint = provider.fingerprint(payload)
    if fingerprint != payload["fingerprint"]:
        raise ValueError("Invalid general-government cohort fingerprint.")
    existing = session.scalar(
        select(GeneralGovernmentCohort).where(
            GeneralGovernmentCohort.year == year,
            GeneralGovernmentCohort.source_hash == payload["resource"]["sha256"],
            GeneralGovernmentCohort.parser_version == payload["parser_version"],
            GeneralGovernmentCohort.precision_version == payload["precision_version"],
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
        if (
            assemble(
                cohort_view(existing),
                year,
                source_view(source)
                if source and source.created_by == existing.created_by
                else None,
            )["status"]
            != "AVAILABLE"
        ):
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
    row = GeneralGovernmentCohort(
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
        "general_government_cohort",
        row.id,
        "CREATE",
        "Coleta oficial das estatísticas do Governo Geral",
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
