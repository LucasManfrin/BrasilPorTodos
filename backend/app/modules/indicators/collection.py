"""Daily collection with database-wide lock, persisted outcomes and retry cooldown."""

import logging
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, select, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.errors import DomainError
from app.database.base import Base
from app.database.mixins import CreatedAt, UUIDPrimaryKey
from app.database.session import get_engine
from app.integrations import bcb, gdp, ibge, treasury, treasury_composition, treasury_interest
from app.modules.indicators.models import Indicator, IndicatorValue
from app.modules.indicators.schedule import get_schedule, next_attempt_at, public_schedule
from app.seed_indicators import seed


class CollectionRun(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "indicator_collection_runs"
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(20))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    results: Mapped[dict] = mapped_column(JSONB)


def status(session):
    latest = session.scalar(
        select(CollectionRun).order_by(CollectionRun.created_at.desc()).limit(1)
    )
    return {
        "interval_hours": 24,
        "schedule": public_schedule(datetime.now(UTC), latest),
        "last_run": {
            "started_at": latest.created_at.isoformat(),
            "finished_at": latest.finished_at.isoformat() if latest.finished_at else None,
            "status": latest.status,
            "series": latest.results,
        }
        if latest
        else None,
    }


def collect(session, actor, manual=False, ignore_cooldown=False, scheduled=False):
    # A dedicated connection keeps the session advisory lock across per-observation commits.
    with get_engine().connect() as lock:
        acquired = lock.scalar(text("SELECT pg_try_advisory_lock(82461301)"))
        if not acquired:
            raise DomainError(409, "COLLECTION_RUNNING", "Uma coleta já está em andamento.")
        try:
            now = datetime.now(UTC)
            latest = session.scalar(
                select(CollectionRun).order_by(CollectionRun.created_at.desc()).limit(1)
            )
            if scheduled and not ignore_cooldown:
                due = next_attempt_at(
                    now,
                    latest.created_at if latest else None,
                    latest.status if latest else None,
                    get_schedule(),
                )
                if due > now:
                    return {**status(session), "skipped": True}
            cooldown = 1 if manual or scheduled or (latest and latest.status != "SUCCESS") else 24
            if (
                latest
                and not ignore_cooldown
                and now - latest.created_at < timedelta(hours=cooldown)
            ):
                return {**status(session), "skipped": True}
            run = CollectionRun(actor_id=actor.id, created_at=now, status="RUNNING", results={})
            session.add(run)
            session.commit()
            results = {}
            end = now.date()
            # Re-fetch bounded windows to discover official revisions.
            # Missing observations are never invented.
            for provider, catalog in ((bcb, bcb.BCB_SERIES), (ibge, ibge.IBGE_SERIES)):
                for code in catalog:
                    if provider is ibge and code == ibge.INCOME_CODE:
                        # Real-income histories share a moving global price reference.
                        # Collect their windows as one independently verified cohort.
                        continue
                    try:
                        years = 1 if catalog[code]["frequency"] == "DAILY" else 3
                        cursor = (
                            end - timedelta(days=365)
                            if years == 1
                            else (end - timedelta(days=365 * years)).replace(day=1)
                        )
                        imported = set()
                        while cursor <= end:
                            until = end if years == 1 else min(date(cursor.year, 12, 31), end)
                            observations, url = provider.fetch_series(code, cursor, until)
                            if observations:
                                seed(session, actor, code, observations, url)
                                imported.update(when for when, _ in observations)
                            cursor = until + timedelta(days=1)
                        if not imported:
                            results[code] = {"status": "NO_DATA"}
                        else:
                            results[code] = {"status": "SUCCESS", "observations": len(imported)}
                    except Exception as error:
                        logging.getLogger("brasil_portodos.collection").warning(
                            "Official collection failed: code=%s error=%s",
                            code,
                            type(error).__name__,
                        )
                        session.rollback()
                        # Public status exposes no exception payload, credentials or private data.
                        results[code] = {
                            "status": "FAILED",
                            "message": (
                                "Fonte indisponível ou resposta fora do contrato. Dados anteriores "
                                "preservados."
                            ),
                        }
                    run = session.get(CollectionRun, run.id)
                    run.results = dict(results)
                    session.commit()
            results.update(collect_income(session, actor, end))
            results.update(collect_fiscal(session, actor, end))
            results.update(collect_composition(session, actor, end))
            results.update(collect_interest(session, actor, end))
            results.update(collect_spending(session, actor, end))
            results.update(collect_general_government(session, actor, end))
            results.update(collect_gdp(session, actor, end))
            run = session.get(CollectionRun, run.id)
            run.results = dict(results)
            run.status = (
                "SUCCESS" if all(r["status"] == "SUCCESS" for r in results.values()) else "PARTIAL"
            )
            run.finished_at = datetime.now(UTC)
            session.commit()
            return {**status(session), "skipped": False}
        finally:
            lock.execute(text("SELECT pg_advisory_unlock(82461301)"))


def request_collection(session, actor, tasks):
    latest = session.scalar(
        select(CollectionRun).order_by(CollectionRun.created_at.desc()).limit(1)
    )
    if latest and datetime.now(UTC) - latest.created_at < timedelta(hours=1):
        return {**status(session), "skipped": True, "accepted": False}
    tasks.add_task(run_requested_collection, actor.id)
    return {**status(session), "accepted": True, "skipped": False}


def run_requested_collection(actor_id):
    from app.modules.users.models import User

    with Session(get_engine()) as session:
        actor = session.get(User, actor_id)
        if actor is None or not actor.is_active or actor.role != "ADMIN":
            return
        try:
            collect(session, actor, manual=True)
        except DomainError:
            # Another worker holds the lock; only one official collection runs.
            return


def collect_income(session, actor, end):
    """Atomic real-income history; global price anchor must stay stable across reads."""
    code = ibge.INCOME_CODE
    try:
        price_reference = ibge.income_price_reference()
        bundles = []
        cursor = (end - timedelta(days=365 * 3)).replace(day=1)
        reference_end = date.fromisoformat(price_reference["income_price_reference"])
        cursor = min(cursor, reference_end)
        previous_dates = set(
            session.scalars(
                select(IndicatorValue.reference_date)
                .join(Indicator, Indicator.id == IndicatorValue.indicator_id)
                .where(Indicator.code == code)
                .distinct()
            )
        )
        if previous_dates:
            cursor = min(cursor, min(previous_dates))
        while cursor <= end:
            until = min(date(cursor.year, 12, 31), end)
            observations, url = ibge.fetch_series(code, cursor, until)
            bundles.append((observations, url))
            cursor = until + timedelta(days=1)
        if ibge.income_price_reference() != price_reference:
            raise ValueError("Income source price reference changed during collection.")
        count = 0
        for observations, _ in bundles:
            if any(when > reference_end for when, _ in observations):
                raise ValueError("Income history exceeds the verified global price reference.")
        fetched_dates = {when for observations, _ in bundles for when, _ in observations}
        if not previous_dates.issubset(fetched_dates):
            raise ValueError("Income release omitted stored history; mixed price bases refused.")
        fetched = {when: value for observations, _ in bundles for when, value in observations}
        from decimal import Decimal

        if fetched.get(reference_end) != Decimal(price_reference["income_price_anchor_value"]):
            raise ValueError("Income history differs from its global latest source anchor.")
        for observations, url in bundles:
            if not observations:
                continue
            seed(
                session,
                actor,
                code,
                observations,
                url,
                provenance_extra={"collector": "ibge-pnad-income-v1", **price_reference},
                commit=False,
            )
            count += len(observations)
        session.commit()
        return {
            code: {"status": "SUCCESS", "observations": count} if count else {"status": "NO_DATA"}
        }
    except Exception as error:
        logging.getLogger("brasil_portodos.collection").warning(
            "Income collection failed: error=%s", type(error).__name__
        )
        session.rollback()
        return {
            code: {
                "status": "FAILED",
                "message": (
                    "Renda real anterior preservada; fonte indisponível, contrato incompatível "
                    "ou base de preços alterada durante a coleta."
                ),
            }
        }


def collect_fiscal(session, actor, end):
    """Fetch and validate the whole bounded fiscal window before writing observations."""
    codes = treasury.TREASURY_SERIES
    results = {}
    try:
        bundles = [
            treasury.fetch_bundle(date(year, 1, 1), min(date(year, 12, 31), end))
            for year in range(end.year - 5, end.year + 1)
        ]
        counts = {code: 0 for code in codes}
        for bundle in bundles:
            monthly = {}
            for code, item in bundle.items():
                for when, value in item["observations"]:
                    monthly.setdefault(when, {})[code] = value
            fingerprints = {
                when: treasury.period_fingerprint(when, values) for when, values in monthly.items()
            }
            for code, item in bundle.items():
                if item["observations"]:
                    seed(
                        session,
                        actor,
                        code,
                        item["observations"],
                        item["request_url"],
                        commit=False,
                        provenance_extra=lambda when, fingerprints=fingerprints: {
                            "collector": "tesouro-rtn-v1",
                            "accounting_basis": "cash",
                            "price_basis": "nominal",
                            "currency": "BRL",
                            "original_unit": "R$ milhões",
                            "scale": "1000000",
                            "period_fingerprint": fingerprints[when],
                        },
                    )
                    counts[code] += len(item["observations"])
        session.commit()
        results = {
            code: {"status": "SUCCESS", "observations": count} if count else {"status": "NO_DATA"}
            for code, count in counts.items()
        }
    except Exception as error:
        logging.getLogger("brasil_portodos.collection").warning(
            "Fiscal collection failed: error=%s",
            type(error).__name__,
        )
        session.rollback()
        results = {
            code: {
                "status": "FAILED",
                "message": (
                    "Dados fiscais anteriores preservados; "
                    "fonte indisponível ou contrato incompatível."
                ),
            }
            for code in codes
        }
    return results


def collect_gdp(session, actor, end):
    """A separate atomic GDP cohort: a GDP outage does not erase valid RTN accounts."""
    from app.modules.indicators.gdp_baseline import current as current_gdp

    code = gdp.GDP_CODE
    try:
        bundles = [(year, gdp.fetch_year(year, end)) for year in range(end.year - 5, end.year + 1)]
        # A temporarily truncated response must not replace a usable closed-year
        # cohort with an incompatible partial fingerprint. Check the complete
        # fetched window before any write. Partial new/current years remain data,
        # never an annual denominator or a substitute for missing quarters.
        for year, bundle in bundles:
            observations = bundle["observations"]
            if not observations or year >= end.year:
                continue
            expected = {date(year, month, 1) for month in (1, 4, 7, 10)}
            if {when for when, _ in observations} != expected and current_gdp(session, year)[
                "status"
            ] == "AVAILABLE":
                raise ValueError("GDP response would replace an available annual cohort with gaps.")
        count = 0
        for year, bundle in bundles:
            observations = bundle["observations"]
            if not observations:
                continue
            fingerprint = gdp.year_fingerprint(year, dict(observations))
            seed(
                session,
                actor,
                code,
                observations,
                bundle["request_url"],
                commit=False,
                provenance_extra={
                    "collector": "ibge-cnt-gdp-v1",
                    "original_unit": "Milhões de Reais",
                    "scale": "1000000",
                    "aggregation": "sum_four_quarters_cnt",
                    "source_precision": "0.01_million_brl",
                    "annual_fingerprint": fingerprint,
                },
            )
            count += len(observations)
        session.commit()
        return {
            code: {"status": "SUCCESS", "observations": count} if count else {"status": "NO_DATA"}
        }
    except Exception as error:
        logging.getLogger("brasil_portodos.collection").warning(
            "GDP collection failed: error=%s",
            type(error).__name__,
        )
        session.rollback()
        return {
            code: {
                "status": "FAILED",
                "message": "PIB anterior preservado; fonte indisponível ou contrato incompatível.",
            }
        }


def collect_composition(session, actor, end):
    """Separate atomic cohort, matching the current historical triple exactly."""
    from app.modules.indicators.fiscal_baseline import current as current_fiscal

    key = "rtn-composition"
    try:
        fiscal = current_fiscal(session)
        if fiscal["status"] != "AVAILABLE":
            return {key: {"status": "NO_DATA", "message": "Referência anual ainda indisponível."}}
        bundle = treasury_composition.fetch_year(fiscal["year"], end)
        expected = {date(fiscal["year"], month, 1) for month in range(1, 13)}
        if set(bundle) != set(treasury_composition.ALL_SERIES):
            raise ValueError("Incomplete composition bundle.")
        monthly = {when: {} for when in expected}
        for code, item in bundle.items():
            if (
                len(item["observations"]) != 12
                or {when for when, _ in item["observations"]} != expected
            ):
                raise ValueError("Incomplete or duplicate composition months.")
            for when, value in item["observations"]:
                monthly[when][code] = value
        fingerprints = {
            when: treasury_composition.period_fingerprint(when, values)
            for when, values in monthly.items()
        }
        for month in fiscal["months"]:
            when = date.fromisoformat(month["reference_date"])
            for row in month["observations"]:
                from decimal import Decimal

                if monthly[when][row["code"]] != Decimal(row["value"]):
                    raise ValueError(
                        "Composition anchors differ from the current historical reference."
                    )
        for code in treasury_composition.COMPOSITION_SERIES:
            item = bundle[code]
            seed(
                session,
                actor,
                code,
                item["observations"],
                item["request_url"],
                commit=False,
                provenance_extra=lambda when: {
                    "collector": treasury_composition.COLLECTOR,
                    "method_version": treasury_composition.METHOD_VERSION,
                    "accounting_basis": "cash",
                    "price_basis": "nominal",
                    "currency": "BRL",
                    "original_unit": "R$ milhões",
                    "scale": "1000000",
                    "period_fingerprint": fingerprints[when],
                },
            )
        # An administrator may have revised anchors while this provider was read.
        # Reject any changed reference before committing the composition.
        latest_fiscal = current_fiscal(session)
        if (
            latest_fiscal["year"] != fiscal["year"]
            or latest_fiscal["amounts"] != fiscal["amounts"]
            or latest_fiscal["months"] != fiscal["months"]
        ):
            raise ValueError("Historical fiscal reference changed during composition collection.")
        session.commit()
        return {key: {"status": "SUCCESS", "observations": 120, "year": fiscal["year"]}}
    except Exception as error:
        logging.getLogger("brasil_portodos.collection").warning(
            "Composition collection failed: error=%s", type(error).__name__
        )
        session.rollback()
        return {
            key: {
                "status": "FAILED",
                "message": "Composição anterior preservada; fonte indisponível ou "
                "conjunto incompatível com a referência anual.",
            }
        }


def collect_interest(session, actor, end):
    """Independent below-line cohort; above-line amounts are never used in the equation."""
    from app.modules.indicators.fiscal_baseline import current as current_fiscal

    key = "rtn-interest"
    try:
        fiscal = current_fiscal(session)
        if fiscal["status"] != "AVAILABLE":
            return {key: {"status": "NO_DATA", "message": "Ano de referência ainda indisponível."}}
        year = fiscal["year"]
        bundle = treasury_interest.fetch_year(year, end)
        expected = {date(year, month, 1) for month in range(1, 13)}
        if set(bundle) != set(treasury_interest.INTEREST_SERIES):
            raise ValueError("Incomplete below-line bundle.")
        monthly = {when: {} for when in expected}
        for code, item in bundle.items():
            if (
                len(item["observations"]) != 12
                or {when for when, _ in item["observations"]} != expected
            ):
                raise ValueError("Incomplete or duplicate below-line months.")
            for when, value in item["observations"]:
                monthly[when][code] = value
        fingerprints = {
            when: treasury_interest.period_fingerprint(when, values)
            for when, values in monthly.items()
        }
        for code, item in bundle.items():
            entry = treasury_interest.INTEREST_SERIES[code]
            seed(
                session,
                actor,
                code,
                item["observations"],
                item["request_url"],
                commit=False,
                provenance_extra=lambda when, entry=entry: {
                    "collector": treasury_interest.COLLECTOR,
                    "method_version": treasury_interest.METHOD_VERSION,
                    "accounting_basis": entry["accounting_basis"],
                    "methodology_basis": "below_line",
                    "component": entry["component"],
                    "price_basis": "nominal",
                    "currency": "BRL",
                    "original_unit": "R$ milhões",
                    "scale": "1000000",
                    "statistical_authority": "Banco Central do Brasil",
                    "methodology_url": treasury_interest.METHOD_URL,
                    "period_fingerprint": fingerprints[when],
                },
            )
        latest = current_fiscal(session)
        if latest["status"] != "AVAILABLE" or latest["year"] != year:
            raise ValueError("Selected historical year changed during below-line collection.")
        session.commit()
        return {key: {"status": "SUCCESS", "observations": 36, "year": year}}
    except Exception as error:
        logging.getLogger("brasil_portodos.collection").warning(
            "Below-line collection failed: error=%s", type(error).__name__
        )
        session.rollback()
        return {
            key: {
                "status": "FAILED",
                "message": "Juros e resultado nominal "
                "anteriores preservados; fonte indisponível ou conjunto incompatível.",
            }
        }


def collect_spending(session, actor, end):
    """Separate atomic spending file; unavailable dimensions never replace saved data."""
    from app.integrations import federal_spending
    from app.modules.indicators.fiscal_baseline import current as current_fiscal
    from app.modules.indicators.fiscal_spending import save_cohort

    key = "federal-spending"
    try:
        fiscal = current_fiscal(session)
        if fiscal["status"] != "AVAILABLE":
            return {key: {"status": "NO_DATA", "message": "Ano de referência ainda indisponível."}}
        year = fiscal["year"]
        payload = federal_spending.fetch_year(year, end)
        if payload.get("year") != year:
            raise ValueError("Spending source returned another year.")
        cohort = save_cohort(session, actor, payload, commit=False)
        latest = current_fiscal(session)
        if latest["status"] != "AVAILABLE" or latest["year"] != year:
            raise ValueError("Reference year changed during spending collection.")
        session.commit()
        return {
            key: {
                "status": "SUCCESS",
                "year": year,
                "observations": payload["row_count"],
                "revision": cohort.revision,
            }
        }
    except Exception as error:
        logging.getLogger("brasil_portodos.collection").warning(
            "Spending collection failed: error=%s", type(error).__name__
        )
        session.rollback()
        return {
            key: {
                "status": "FAILED",
                "message": "Gasto funcional anterior preservado; "
                "fonte indisponível ou arquivo/conjunto fora do contrato.",
            }
        }


def collect_general_government(session, actor, end):
    """Atomic annual publication; its own criteria never replace or modify RTN."""
    from app.integrations import general_government
    from app.modules.indicators.fiscal_baseline import current as current_fiscal
    from app.modules.indicators.general_government import save_cohort

    key = "general-government"
    try:
        fiscal = current_fiscal(session)
        if fiscal["status"] != "AVAILABLE":
            return {key: {"status": "NO_DATA", "message": "Ano de referência ainda indisponível."}}
        year = fiscal["year"]
        payload = general_government.fetch_year(year, end)
        if payload.get("year") != year:
            raise ValueError("General-government source returned another year.")
        cohort = save_cohort(session, actor, payload, commit=False)
        latest = current_fiscal(session)
        if latest["status"] != "AVAILABLE" or latest["year"] != year:
            raise ValueError("Reference year changed during general-government collection.")
        session.commit()
        return {
            key: {
                "status": "SUCCESS",
                "year": year,
                "observations": sum(len(sector["amounts"]) for sector in payload["sectors"]),
                "revision": cohort.revision,
            }
        }
    except Exception as error:
        logging.getLogger("brasil_portodos.collection").warning(
            "General-government collection failed: error=%s", type(error).__name__
        )
        session.rollback()
        return {
            key: {
                "status": "FAILED",
                "message": "Estatísticas anteriores do Governo Geral preservadas; "
                "fonte indisponível ou publicação/conjunto fora do contrato.",
            }
        }
