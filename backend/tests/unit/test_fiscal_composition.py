"""Synthetic composition fixtures; no network or real fiscal constants."""

from copy import deepcopy
from datetime import date
from decimal import Decimal
from urllib.parse import parse_qs, urlsplit

import pytest
from test_fiscal_baseline import closed_year
from test_treasury import payload

from app.integrations import treasury
from app.integrations import treasury_composition as provider
from app.modules.indicators.fiscal_baseline import assemble as fiscal_assemble
from app.modules.indicators.fiscal_composition import SOURCE, assemble


def values():
    return dict(
        zip(
            provider.ALL_SERIES,
            map(
                Decimal,
                (
                    "1000.10",
                    "750.01",
                    "250.09",
                    "1100.10",
                    "100.00",
                    "800.00",
                    "-1.00",
                    "200.00",
                    "101.10",
                    "300.00",
                    "200.00",
                    "100.00",
                    "150.01",
                ),
            ),
            strict=True,
        )
    )


def records(year=2025):
    output = []
    for month in range(1, 13):
        when = date(year, month, 1)
        fingerprint = provider.period_fingerprint(when, values())
        for code, entry in provider.COMPOSITION_SERIES.items():
            output.append(
                {
                    "code": code,
                    "reference_date": when.isoformat(),
                    "value": str(values()[code]),
                    "revision": 1,
                    "retrieved_at": "2026-01-01T00:00:00+00:00",
                    "source": {
                        **SOURCE,
                        "source_type": "OFFICIAL",
                        "is_example": False,
                        "description": (
                            f"Dados oficiais de {SOURCE['institution']}. "
                            f"Termos: {treasury.LICENSE_NAME}. {treasury.LICENSE_URL}"
                        ),
                    },
                    "provenance": {
                        "collector": provider.COLLECTOR,
                        "method": entry["methodology"],
                        "method_version": provider.METHOD_VERSION,
                        "accounting_basis": "cash",
                        "price_basis": "nominal",
                        "currency": "BRL",
                        "original_unit": "R$ milhões",
                        "scale": "1000000",
                        "series": entry["series"],
                        "dataset_url": treasury.SOURCE_URL,
                        "institution": SOURCE["institution"],
                        "license": treasury.LICENSE_NAME,
                        "license_url": treasury.LICENSE_URL,
                        "period_fingerprint": fingerprint,
                        "definition": {
                            key: entry[key] for key in ("unit", "scope", "frequency", "methodology")
                        },
                    },
                }
            )
    return output


def fiscal():
    return fiscal_assemble(closed_year(), date(2026, 10, 10))


def test_signed_components_annual_arithmetic_and_original_inputs_preserved():
    rows = records()
    original = deepcopy(rows)
    result = assemble(rows, fiscal())
    assert result["status"] == "AVAILABLE"
    assert result["totals"] == {
        "gross_revenue": "13201.20",
        "transfers": "1200.00",
        "net_revenue": "12001.20",
        "primary_expenditure": "9000.12",
    }
    assert result["revenue"][1]["amount"] == "-12.00"
    assert len(result["revenue"]) == len(result["expenditure"]) == 4
    assert len(result["months"]) == 12 and rows == original
    assert set(row["series"] for row in result["expenditure"]) == {
        "10.03.1.1",
        "10.03.1.2",
        "10.03.1.3",
        "10.03.1.4",
    }


@pytest.mark.parametrize(
    "change",
    [
        "missing_month",
        "missing_code",
        "wrong_year",
        "changed_anchor",
        "bad_fingerprint",
        "invalid_latest",
        "invalid_license",
        "private_title",
        "bad_method",
        "example",
        "invalid_money",
    ],
)
def test_incomplete_or_incompatible_current_cohort_never_returns_old_or_partial_totals(change):
    rows, reference = records(), fiscal()
    if change == "missing_month":
        rows = [row for row in rows if row["reference_date"] != "2025-06-01"]
    if change == "missing_code":
        rows = rows[1:]
    if change == "wrong_year":
        rows = records(2024)
    if change == "changed_anchor":
        reference = fiscal_assemble(closed_year(revenue="1001.10"), date(2026, 10, 10))
    if change == "bad_fingerprint":
        rows[0]["provenance"]["period_fingerprint"] = "unrelated"
    if change == "invalid_latest":
        new = deepcopy(rows[0])
        new["revision"] = 2
        new["value"] = "1.00"
        rows.append(new)
    if change == "invalid_license":
        rows[0]["provenance"]["license"] = "unreviewed"
    if change == "private_title":
        rows[0]["source"]["title"] = "Private metadata"
    if change == "bad_method":
        rows[0]["provenance"]["definition"]["methodology"] = "Other method"
    if change == "example":
        rows[0]["source"]["is_example"] = True
    if change == "invalid_money":
        rows[0]["value"] = "NaN"
    result = assemble(rows, reference)
    assert result["status"] == "INCOMPLETE" and result["totals"] is None
    assert result["revenue"] == result["expenditure"] == result["months"] == []
    assert result["reference_amounts"] == {
        key: reference["amounts"][key]
        for key in ("net_revenue", "primary_expenditure", "published_primary_balance")
    }


def test_empty_no_fiscal_reference_never_infers_zero():
    result = assemble([], {"status": "EMPTY"})
    assert result["status"] == "EMPTY" and result["totals"] is None and result["year"] is None
    assert result["reference_amounts"] is None


def test_cent_rounding_residual_is_reported_without_inventing_remainder():
    rows = records()
    month = values()
    month["rtn-executivo-programacao"] += Decimal("0.01")
    for row in rows:
        if row["reference_date"] == "2025-04-01":
            row["value"] = str(month[row["code"]])
            row["provenance"]["period_fingerprint"] = provider.period_fingerprint(
                date(2025, 4, 1), month
            )
    result = assemble(rows, fiscal())
    assert result["status"] == "AVAILABLE"
    assert result["reconciliation"]["expenditure_difference"] == "0.01"
    assert result["totals"]["primary_expenditure"] == "9000.12"


@pytest.mark.parametrize(
    "invalid", [Decimal("NaN"), Decimal("Infinity"), Decimal("100000000"), 1.2, True, "1"]
)
def test_parser_rejects_unreviewed_numeric_representation(invalid):
    with pytest.raises(ValueError):
        provider.parse_series(
            payload("10.01.1.2", {"2025-01-01T00:00:00Z": invalid}),
            "10.01.1.2",
            date(2025, 1, 1),
            date(2025, 12, 1),
        )


def test_parser_preserves_negative_incentive_and_legacy_allowlist():
    assert provider.parse_series(
        payload("10.01.1.2", {"2025-01-01T00:00:00Z": Decimal("-0.000001015")}),
        "10.01.1.2",
        date(2025, 1, 1),
        date(2025, 12, 1),
    ) == [(date(2025, 1, 1), Decimal("-1.02"))]
    with pytest.raises(ValueError):
        treasury.parse_series(
            payload("10.01.1.2"), "10.01.1.2", date(2025, 1, 1), date(2025, 12, 1)
        )


def test_bounded_fetch_validates_all_thirteen_complete_series(monkeypatch):
    calls = []

    def reader(url, *, decimal_numbers):
        assert decimal_numbers
        assert urlsplit(url).hostname == "apiapex.tesouro.gov.br"
        query = parse_qs(urlsplit(url).query)
        assert query["correcao_ipca"] == ["false"]
        series = query["codigo_da_serie"][0]
        calls.append(series)
        code = next(
            code for code, entry in provider.ALL_SERIES.items() if entry["series"] == series
        )
        return payload(
            series,
            {
                f"2025-{month:02}-01T00:00:00Z": values()[code] / treasury.SCALE
                for month in range(1, 13)
            },
        )

    monkeypatch.setattr("app.integrations.http.read_json", reader)
    bundle = provider.fetch_year(2025, date(2026, 10, 10))
    assert len(calls) == len(bundle) == 13
    assert all(len(item["observations"]) == 12 for item in bundle.values())
    fingerprint = provider.period_fingerprint(date(2025, 1, 1), values())
    assert fingerprint == provider.period_fingerprint(
        date(2025, 1, 1), dict(reversed(list(values().items())))
    )
    assert fingerprint != treasury.period_fingerprint(
        date(2025, 1, 1), {code: values()[code] for code in treasury.TREASURY_SERIES}
    )


def test_fetch_rejects_incomplete_year_even_if_all_series_omit_same_month(monkeypatch):
    monkeypatch.setattr(
        "app.integrations.http.read_json",
        lambda url, **kwargs: payload(parse_qs(urlsplit(url).query)["codigo_da_serie"][0], {}),
    )
    with pytest.raises(ValueError, match="incomplete"):
        provider.fetch_year(2025, date(2026, 10, 10))
