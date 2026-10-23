"""Bound compressed and expanded API bodies; allowlisted official hosts only."""

import gzip
import io
import json
from decimal import Decimal
from urllib.parse import urlsplit
from urllib.request import Request, build_opener

from app.integrations.bcb import NoRedirect


def read_json(url, *, decimal_numbers=False):
    parts = urlsplit(url)
    if (
        parts.scheme != "https"
        or parts.hostname
        not in (
            "api.bcb.gov.br",
            "servicodados.ibge.gov.br",
            "apiapex.tesouro.gov.br",
            "apisidra.ibge.gov.br",
        )
        or parts.port not in (None, 443)
        or parts.username
        or parts.password
    ):
        raise ValueError("Unapproved official API host.")
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "User-Agent": "BrasilPorTodos/0.1",
        },
    )
    with build_opener(NoRedirect()).open(request, timeout=20) as response:
        raw = response.read(1_000_001)
        encoding = response.headers.get("Content-Encoding", "identity")
    if len(raw) > 1_000_000:
        raise ValueError("API payload exceeds size limit.")
    if encoding == "gzip" or raw.startswith(b"\x1f\x8b"):
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
            raw = stream.read(1_000_001)
    elif encoding not in ("identity", ""):
        raise ValueError("Unsupported API content encoding.")
    if len(raw) > 1_000_000:
        raise ValueError("Expanded API payload exceeds size limit.")
    return json.loads(raw, parse_float=Decimal if decimal_numbers else float)
