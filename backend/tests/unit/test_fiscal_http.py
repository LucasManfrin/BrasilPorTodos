"""Offline HTTP precision and endpoint boundaries for reviewed fiscal APIs."""

import io
from decimal import Decimal

import pytest

from app.integrations import http


class Response(io.BytesIO):
    headers = {"Content-Encoding": "identity"}


class Opener:
    def __init__(self, data):
        self.data = data

    def open(self, request, *, timeout):
        assert request.full_url.startswith("https://apiapex.tesouro.gov.br/")
        assert timeout == 20
        return Response(self.data)


def test_official_fiscal_json_number_is_decimal_without_float_roundtrip(monkeypatch):
    monkeypatch.setattr(
        http,
        "build_opener",
        lambda *args: Opener(b'{"valor":258004.04353337252,"page":1}'),
    )
    parsed = http.read_json("https://apiapex.tesouro.gov.br/test", decimal_numbers=True)
    assert type(parsed["valor"]) is Decimal
    assert parsed["valor"] == Decimal("258004.04353337252")
    assert type(parsed["page"]) is int


@pytest.mark.parametrize(
    "url",
    [
        "https://apiapex.tesouro.gov.br:8443/test",
        "http://apiapex.tesouro.gov.br/test",
        "https://apiapex.tesouro.gov.br.evil.example/test",
        "https://user:secret@apiapex.tesouro.gov.br/test",
    ],
)
def test_fiscal_endpoint_boundaries_are_checked_before_network(monkeypatch, url):
    def forbidden(*args):
        raise AssertionError("No network is permitted in this test")

    monkeypatch.setattr(http, "build_opener", forbidden)
    with pytest.raises(ValueError, match="Unapproved"):
        http.read_json(url, decimal_numbers=True)
