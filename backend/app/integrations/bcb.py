"""Explicit CLI import from an allowlisted API; never accepts contributed URLs."""

from datetime import UTC, date, datetime
from decimal import Decimal
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler

from app.modules.indicators.catalog import BCB_SERIES


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Unexpected API redirect refused.")


def parse_observations(payload, start, end):
    if not isinstance(payload, list) or len(payload) > 370:
        raise ValueError("Unexpected observation payload.")
    output = []
    seen = set()
    for row in payload:
        when = datetime.strptime(row["data"], "%d/%m/%Y").date()
        value = Decimal(row["valor"])
        if when < start or when > end or when > datetime.now(UTC).date():
            raise ValueError("API returned an observation outside the requested period.")
        if when in seen or not value.is_finite():
            raise ValueError("Duplicate or nonfinite observation.")
        seen.add(when)
        output.append((when, value))
    return sorted(output)


def fetch_series(code, start: date, end: date):
    if (
        code not in BCB_SERIES
        or start > end
        or (end - start).days > 365
        or end > datetime.now(UTC).date()
    ):
        raise ValueError("Choose an approved series and a past interval of up to one year.")
    query = urlencode(
        {
            "formato": "json",
            "dataInicial": start.strftime("%d/%m/%Y"),
            "dataFinal": end.strftime("%d/%m/%Y"),
        }
    )
    url = (
        f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{BCB_SERIES[code]['series']}/dados?{query}"
    )
    from app.integrations.http import read_json

    return parse_observations(read_json(url), start, end), url
