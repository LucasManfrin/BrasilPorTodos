from datetime import date
from decimal import Decimal

import pytest

from app.integrations.ibge import parse_series


def payload(values, variable=4099):
    return [
        {
            "id": str(variable),
            "unidade": "%",
            "resultados": [
                {"classificacoes": [], "series": [{"localidade": {"id": "1"}, "serie": values}]}
            ],
        }
    ]


def test_official_rolling_period_and_missing_value_are_not_fabricated():
    result = parse_series(
        payload({"202601": "6.1", "202602": "..."}), 4099, date(2026, 1, 1), date(2026, 2, 28)
    )
    assert result == [(date(2026, 1, 1), Decimal("6.1"))]


@pytest.mark.parametrize("change", ["outside", "scope", "variable", "nonfinite", "breakdown"])
def test_definition_scope_and_bounded_date_contract(change):
    data = payload({"202601": "6.1"})
    if change == "outside":
        data[0]["resultados"][0]["series"][0]["serie"] = {"202501": "5"}
    if change == "scope":
        data[0]["resultados"][0]["series"][0]["localidade"]["id"] = "33"
    if change == "variable":
        data[0]["id"] = "8811"
    if change == "nonfinite":
        data[0]["resultados"][0]["series"][0]["serie"] = {"202601": "NaN"}
    if change == "breakdown":
        data[0]["resultados"][0]["classificacoes"] = [{"id": "sexo"}]
    with pytest.raises(ValueError):
        parse_series(data, 4099, date(2026, 1, 1), date(2026, 2, 28))
