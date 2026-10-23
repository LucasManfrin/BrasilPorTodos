from datetime import date
from decimal import Decimal

import pytest

from app.integrations.bcb import fetch_series, parse_observations


def test_official_payload_is_decimal_and_period_bounded():
    assert parse_observations(
        [{"data": "01/01/2025", "valor": "1.234567"}], date(2025, 1, 1), date(2025, 1, 31)
    ) == [(date(2025, 1, 1), Decimal("1.234567"))]
    with pytest.raises(ValueError):
        parse_observations(
            [{"data": "01/02/2025", "valor": "1"}], date(2025, 1, 1), date(2025, 1, 31)
        )


@pytest.mark.parametrize(
    "payload",
    [[{"data": "01/01/2025", "valor": "NaN"}], [{"data": "01/01/2025", "valor": "1"}] * 2],
)
def test_duplicate_or_nonfinite_observations_are_refused(payload):
    with pytest.raises(ValueError):
        parse_observations(payload, date(2025, 1, 1), date(2025, 1, 31))


def test_importer_refuses_unapproved_series_without_network():
    with pytest.raises(ValueError):
        fetch_series("https://example.org", date(2025, 1, 1), date(2025, 1, 31))
