from threading import Event

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app import guidance_cleanup


def test_once_reports_only_count_without_provider_configuration(capsys):
    assert guidance_cleanup.run_worker(watch=False, stop=Event(), cleanup=lambda: 3) == 0
    assert capsys.readouterr().out == "Limpeza IA: 3 registros expirados removidos.\n"


def test_failure_does_not_print_connection_details(capsys):
    def failure():
        raise SQLAlchemyError("private-answer postgres://user:password@host/db")

    assert guidance_cleanup.run_worker(watch=False, stop=Event(), cleanup=failure) == 1
    output = capsys.readouterr().out
    assert "indisponivel" in output
    assert "password" not in output and "private-answer" not in output


def test_watch_wait_is_interruptible_and_exactly_five_minutes():
    class Stop:
        stopped = False
        calls = []

        def is_set(self):
            return self.stopped

        def wait(self, seconds):
            self.calls.append(seconds)
            self.stopped = True

    stop = Stop()
    assert guidance_cleanup.run_worker(watch=True, stop=stop, cleanup=lambda: 0) == 0
    assert stop.calls == [300]


def test_cli_modes_are_exclusive():
    with pytest.raises(SystemExit) as error:
        guidance_cleanup.main(["--watch", "--once"])
    assert error.value.code == 2


def test_database_failure_rolls_back_and_does_not_commit(monkeypatch):
    class BrokenSession:
        rolled_back = False
        committed = False

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def execute(self, _):
            raise SQLAlchemyError("connection failed")

        def rollback(self):
            self.rolled_back = True

        def commit(self):
            self.committed = True

    session = BrokenSession()
    monkeypatch.setattr(guidance_cleanup, "Session", lambda _: session)
    monkeypatch.setattr(guidance_cleanup, "get_engine", lambda: object())
    with pytest.raises(SQLAlchemyError):
        guidance_cleanup.cleanup_once()
    assert session.rolled_back and not session.committed
