from datetime import date

import pytest

from app.core.errors import DomainError
from app.modules.contexts.resolver import KNOWN_CODES, measurement_period


@pytest.mark.parametrize(
    "code,reference,frequency,start,end",
    [
        ("selic-meta", date(2025, 2, 15), "DAILY", date(2025, 2, 15), date(2025, 2, 15)),
        ("ipca-mensal", date(2024, 2, 1), "MONTHLY", date(2024, 2, 1), date(2024, 2, 29)),
        ("desocupacao", date(2025, 1, 1), "MONTHLY", date(2024, 11, 1), date(2025, 1, 31)),
        ("renda-trabalho-real", date(2025, 2, 1), "MONTHLY", date(2024, 12, 1), date(2025, 2, 28)),
        ("informalidade", date(2025, 3, 1), "MONTHLY", date(2025, 1, 1), date(2025, 3, 31)),
        (
            "participacao-forca-trabalho",
            date(2025, 3, 1),
            "MONTHLY",
            date(2025, 1, 1),
            date(2025, 3, 31),
        ),
        ("ipca-12-meses", date(2025, 1, 1), "MONTHLY", date(2024, 2, 1), date(2025, 1, 31)),
        (
            "pib-nominal-trimestral",
            date(2025, 10, 1),
            "QUARTERLY",
            date(2025, 10, 1),
            date(2025, 12, 31),
        ),
        (
            "rtn-resultado-primario",
            date(2025, 5, 1),
            "MONTHLY",
            date(2025, 5, 1),
            date(2025, 5, 31),
        ),
    ],
)
def test_stored_reference_carries_the_actual_measurement_window(
    code, reference, frequency, start, end
):
    assert measurement_period(code, reference, frequency) == (start, end)


@pytest.mark.parametrize(
    "code,reference,frequency",
    [
        ("inventado", date(2025, 1, 1), "MONTHLY"),
        ("rtn-juros-nominais", date(2025, 1, 1), "MONTHLY"),
        ("ipca-mensal", date(2025, 1, 15), "MONTHLY"),
        ("pib-nominal-trimestral", date(2025, 2, 1), "QUARTERLY"),
        ("ipca-mensal", date(2025, 1, 1), "IRREGULAR"),
    ],
)
def test_unknown_or_ambiguous_period_is_not_invented(code, reference, frequency):
    with pytest.raises(DomainError):
        measurement_period(code, reference, frequency)


def test_catalog_remains_fourteen_main_series_without_auxiliary_budget_numbers():
    assert len(KNOWN_CODES) == 14


@pytest.mark.parametrize(
    "provenance",
    [
        {"license": ["ODbL"], "license_url": "https://example.org/terms"},
        {"license": "ODbL", "license_url": {"url": "https://example.org/terms"}},
        {},
        "corrupt",
    ],
)
def test_observation_terms_are_validated_before_building_a_set(provenance):
    from types import SimpleNamespace
    from uuid import uuid4

    from app.modules.contexts.resolver import _source

    key = uuid4()
    source = SimpleNamespace(id=key)
    row = SimpleNamespace(source_id=key, provenance=provenance)
    with pytest.raises(DomainError) as error:
        _source(None, source, {uuid4(): row})
    assert error.value.code == "CONTEXT_REFERENCE_INVALID"


def test_conflicting_historical_terms_are_not_replaced_with_latest_terms():
    from types import SimpleNamespace
    from uuid import uuid4

    from app.modules.contexts.resolver import _source

    key = uuid4()
    source = SimpleNamespace(id=key)
    rows = {
        uuid4(): SimpleNamespace(
            source_id=key,
            provenance={
                "license": license_name,
                "license_url": f"https://example.org/{license_name}",
            },
        )
        for license_name in ("historical", "revised")
    }
    with pytest.raises(DomainError) as error:
        _source(None, source, rows)
    assert error.value.code == "CONTEXT_TERMS_CONFLICT"


def test_known_indicator_cannot_claim_a_different_measurement_frequency():
    with pytest.raises(DomainError):
        measurement_period("ipca-mensal", date(2025, 1, 15), "DAILY")


def income_fixture():
    from datetime import UTC, datetime
    from decimal import Decimal
    from types import SimpleNamespace
    from uuid import uuid4

    return SimpleNamespace(
        id=uuid4(),
        source_id=uuid4(),
        revision=1,
        value=Decimal("100.000000"),
        reference_date=date(2025, 1, 1),
        retrieved_at=datetime(2026, 1, 2, tzinfo=UTC),
        provenance={
            "definition": {
                "unit": "R$",
                "scope": "Recorte de teste",
                "frequency": "MONTHLY",
                "methodology": "Renda real habitual, definição congelada.",
            },
            "income_price_reference": "2025-12-01",
            "income_price_period": "out–dez/2025",
            "income_price_method_url": "https://example.org/metodo-ficticio",
        },
    ), SimpleNamespace(
        code="renda-trabalho-real", methodology="Texto vivo não substitui o histórico."
    )


def test_real_income_preserves_the_observation_price_reference_in_its_method():
    from app.modules.contexts.resolver import _observation

    value, indicator = income_fixture()
    anchor = _observation(value, indicator)
    assert "Renda real habitual, definição congelada." in anchor.methodology
    assert "2025-12-01" in anchor.methodology and "out–dez/2025" in anchor.methodology
    assert "Texto vivo" not in anchor.methodology
    assert anchor.period_start == date(2024, 11, 1)


@pytest.mark.parametrize(
    "missing", ["income_price_reference", "income_price_period", "income_price_method_url"]
)
def test_real_income_without_a_historical_price_reference_is_not_invented(missing):
    from app.modules.contexts.resolver import _observation

    value, indicator = income_fixture()
    del value.provenance[missing]
    with pytest.raises(DomainError) as error:
        _observation(value, indicator)
    assert error.value.code == "CONTEXT_INCOME_PRICE_REFERENCE"
