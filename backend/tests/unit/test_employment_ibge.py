"""Synthetic PNAD fixtures; no actual country values or external requests."""

from datetime import date
from decimal import Decimal

import pytest

from app.integrations import ibge


def payload(variable=5933, unit="Reais", values=None):
    return [
        {
            "id": str(variable),
            "unidade": unit,
            "resultados": [
                {
                    "classificacoes": [],
                    "series": [
                        {
                            "localidade": {"id": "1", "nivel": {"id": "N1"}, "nome": "Brasil"},
                            "serie": values if values is not None else {"202508": "1234"},
                        }
                    ],
                }
            ],
        }
    ]


@pytest.mark.parametrize(
    ("code", "variable", "unit", "raw"),
    [
        ("renda-trabalho-real", 5933, "Reais", "1234"),
        ("informalidade", 12466, "%", "39.2"),
        ("participacao-forca-trabalho", 4096, "%", "62.5"),
    ],
)
def test_reviewed_employment_measures_preserve_units_periods_and_missing_values(
    code, variable, unit, raw
):
    data = payload(variable, unit, {"202507": raw, "202508": "..."})
    result = ibge.parse_series(data, variable, date(2025, 7, 1), date(2025, 8, 31))
    assert result == [(date(2025, 7, 1), Decimal(raw))]
    assert ibge.IBGE_SERIES[code]["category"] == "SOCIAL"


@pytest.mark.parametrize(
    "change", ["unit", "class", "geography", "variable", "float", "negative", "nonfinite"]
)
def test_income_rejects_unreviewed_definition_breakdown_and_values(change):
    data = payload()
    if change == "unit":
        data[0]["unidade"] = "%"
    if change == "class":
        data[0]["resultados"][0]["classificacoes"] = [{"id": "sexo"}]
    if change == "geography":
        data[0]["resultados"][0]["series"][0]["localidade"]["id"] = "35"
    if change == "variable":
        data[0]["id"] = "5934"
    if change == "float":
        data[0]["resultados"][0]["series"][0]["serie"]["202508"] = 1234.1
    if change == "negative":
        data[0]["resultados"][0]["series"][0]["serie"]["202508"] = "-1234"
    if change == "nonfinite":
        data[0]["resultados"][0]["series"][0]["serie"]["202508"] = "NaN"
    with pytest.raises(ValueError):
        ibge.parse_series(data, 5933, date(2025, 8, 1), date(2025, 8, 31))


def test_percent_employment_measures_use_zero_to_hundred_range_and_unknown_variable_is_blocked():
    with pytest.raises(ValueError):
        ibge.parse_series(
            payload(12466, "%", {"202508": "101"}), 12466, date(2025, 8, 1), date(2025, 8, 31)
        )
    with pytest.raises(ValueError):
        ibge.parse_series(payload(9999, "%"), 9999, date(2025, 8, 1), date(2025, 8, 31))


def test_income_request_is_national_and_bounded_to_reviewed_table_and_variable(monkeypatch):
    calls = []

    def read(url):
        calls.append(url)
        assert "/agregados/6390/periodos/202507|202508/variaveis/5933" in url
        assert url.endswith("?localidades=N1[1]")
        return payload(values={"202507": "1200", "202508": "1234"})

    monkeypatch.setattr("app.integrations.http.read_json", read)
    result, url = ibge.fetch_series("renda-trabalho-real", date(2025, 7, 1), date(2025, 8, 31))
    assert len(calls) == 1 and url == calls[0]
    assert len(result) == 2 and result[0][1] == Decimal("1200")


@pytest.mark.parametrize(
    "period,label", [("202508", "jun–ago/2025"), ("202501", "nov/2024–jan/2025")]
)
def test_income_global_anchor_uses_latest_source_period_and_release_metadata(
    monkeypatch, period, label
):
    calls = []

    def read(url):
        calls.append(url)
        if url == ibge.INCOME_PERIODS_URL:
            return [
                {"id": period, "literals": ["Synthetic source label"], "modificacao": "29/09/2025"}
            ]
        assert url == ibge.INCOME_REFERENCE_URL
        return payload(values={period: "1234"})

    monkeypatch.setattr("app.integrations.http.read_json", read)
    reference = ibge.income_price_reference()
    assert reference["income_price_reference"] == f"{period[:4]}-{period[4:]}-01"
    assert reference["income_price_period"] == label
    assert reference["income_price_anchor_value"] == "1234"
    assert reference["income_source_modified"] == "2025-09-29"
    assert reference["price_basis"] == "real_latest_rolling_quarter"
    assert len(reference["income_periods_fingerprint"]) == 64 and len(calls) == 2


def test_release_metadata_and_latest_observation_disagreement_is_not_a_price_reference(monkeypatch):
    def read(url):
        if url == ibge.INCOME_PERIODS_URL:
            return [{"id": "202508", "literals": ["jun-jul-ago 2025"], "modificacao": "29/09/2025"}]
        return payload(values={"202507": "1234"})

    monkeypatch.setattr("app.integrations.http.read_json", read)
    with pytest.raises(ValueError):
        ibge.income_price_reference()
