import gzip
import io

import pytest

from app.integrations import http


class Response(io.BytesIO):
    headers = {"Content-Encoding": "gzip"}


class Opener:
    def __init__(self, data):
        self.data = data

    def open(self, *args, **kwargs):
        return Response(self.data)


def test_compressed_official_response_is_read(monkeypatch):
    monkeypatch.setattr(
        http, "build_opener", lambda *args: Opener(gzip.compress(b'[{"value":"1.2"}]'))
    )
    assert http.read_json("https://servicodados.ibge.gov.br/api/test") == [{"value": "1.2"}]


def test_expanded_body_limit_prevents_gzip_bomb(monkeypatch):
    monkeypatch.setattr(http, "build_opener", lambda *args: Opener(gzip.compress(b" " * 1_000_001)))
    with pytest.raises(ValueError, match="Expanded"):
        http.read_json("https://servicodados.ibge.gov.br/api/test")


def test_arbitrary_host_is_rejected_before_network(monkeypatch):
    def forbidden(*args):
        raise AssertionError("Network should not be used")

    monkeypatch.setattr(http, "build_opener", forbidden)
    with pytest.raises(ValueError, match="Unapproved"):
        http.read_json("https://example.org/test")
