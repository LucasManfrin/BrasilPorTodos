import argparse
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_engine
from app.integrations import gdp, treasury, treasury_composition, treasury_interest
from app.integrations.bcb import fetch_series
from app.integrations.ibge import IBGE_SERIES, IBGE_TERMS
from app.modules.indicators import service
from app.modules.indicators.catalog import BCB_SERIES, LICENSE_URL
from app.modules.indicators.models import Indicator
from app.modules.indicators.schemas import IndicatorInput, ObservationInput
from app.modules.sources.models import Source
from app.modules.users.models import User


def seed(session, actor, code, observations, request_url, provenance_extra=None, *, commit=True):
    entry = (
        BCB_SERIES
        | IBGE_SERIES
        | treasury.TREASURY_SERIES
        | treasury_composition.COMPOSITION_SERIES
        | treasury_interest.INTEREST_SERIES
        | gdp.GDP_SERIES
    )[code]
    is_ibge = code in IBGE_SERIES or code in gdp.GDP_SERIES
    is_treasury = (
        code in treasury.TREASURY_SERIES
        or code in treasury_composition.COMPOSITION_SERIES
        or code in treasury_interest.INTEREST_SERIES
    )
    institution = (
        "Secretaria do Tesouro Nacional"
        if is_treasury
        else ("IBGE" if is_ibge else "Banco Central do Brasil")
    )
    license_name = (
        treasury.LICENSE_NAME
        if is_treasury
        else ("Termos do portal IBGE" if is_ibge else "ODbL 1.0")
    )
    terms_url = treasury.LICENSE_URL if is_treasury else (IBGE_TERMS if is_ibge else LICENSE_URL)
    dataset_url = (
        treasury.SOURCE_URL
        if is_treasury
        else (
            f"https://sidra.ibge.gov.br/tabela/{entry['aggregate']}"
            if is_ibge
            else f"https://dadosabertos.bcb.gov.br/dataset/{entry['dataset']}"
        )
    )
    indicator = session.scalar(select(Indicator).where(Indicator.code == code))
    if indicator is None:
        data = IndicatorInput(
            code=code,
            **{
                key: value
                for key, value in entry.items()
                if key in IndicatorInput.model_fields and key not in ("reason", "code")
            },
            reason="Catálogo de fontes oficiais revisadas",
        )
        service.save(session, data, actor, commit=commit)
        indicator = session.scalar(select(Indicator).where(Indicator.code == code))
    elif any(
        getattr(indicator, key) != entry[key]
        for key in ("unit", "scope", "methodology", "frequency")
    ):
        raise ValueError("Existing indicator definition differs from the reviewed catalog.")
    source_title = "Resultado do Tesouro Nacional (RTN)" if is_treasury else entry["name"]
    source_description = f"Dados oficiais de {institution}. Termos: {license_name}. {terms_url}"
    # An equal URL never grants permission to publish another contributor's private metadata.
    source = session.scalar(
        select(Source)
        .where(
            Source.url == dataset_url,
            Source.created_by == actor.id,
            Source.source_type == "OFFICIAL",
            Source.is_example.is_(False),
            Source.institution == institution,
            Source.title == source_title,
            Source.description == source_description,
        )
        .order_by(Source.created_at, Source.id)
        .limit(1)
    )
    if source is None:
        source = Source(
            created_by=actor.id,
            title=source_title,
            institution=institution,
            url=dataset_url,
            source_type="OFFICIAL",
            accessed_at=datetime.now(UTC).date(),
            description=source_description,
        )
        session.add(source)
        if commit:
            session.commit()
        else:
            session.flush()
    for when, value in observations:
        payload = ObservationInput(
            reference_date=when,
            value=value,
            source_id=source.id,
            retrieved_at=datetime.now(UTC),
            revision_reason="Coleta revisada da API oficial; correções geram nova revisão",
            provenance={
                "dataset_url": dataset_url,
                "license": license_name,
                "license_url": terms_url,
                "institution": institution,
                "method": entry["methodology"],
                "request_url": request_url,
                "series": str(entry.get("series", entry.get("variable"))),
                "transformation": "million_brl_to_brl_round_cent"
                if is_treasury or code in gdp.GDP_SERIES
                else "none",
                **(
                    provenance_extra(when)
                    if callable(provenance_extra)
                    else (provenance_extra or {})
                ),
            },
        )
        service.add_observation(session, indicator.id, payload, actor, commit=commit)
    return indicator.id


def main():
    parser = argparse.ArgumentParser(description="Importação manual BCB; não roda no startup.")
    parser.add_argument("--username", required=True)
    parser.add_argument("--series", choices=BCB_SERIES, required=True)
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    args = parser.parse_args()
    with Session(get_engine()) as session:
        actor = session.scalar(
            select(User).where(
                User.username == args.username, User.is_active.is_(True), User.role == "ADMIN"
            )
        )
        if actor is None:
            parser.error("Use an active local administrator.")
        observations, url = fetch_series(args.series, args.start, args.end)
        if not observations:
            parser.error("No official observations in this interval; nothing imported.")
        seed(session, actor, args.series, observations, url)
        print(f"{len(observations)} official observations imported; existing values preserved.")


if __name__ == "__main__":
    main()
