"""Remove expired private guidance logs without calling any AI provider."""

import argparse
import signal
from collections.abc import Callable
from datetime import UTC, datetime
from threading import Event

from sqlalchemy import delete, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.session import get_engine
from app.modules.guidance.models import GuidanceCall

POLL_SECONDS = 300


def cleanup_expired(session: Session, *, now: datetime | None = None) -> int:
    cutoff = now if now is not None else datetime.now(UTC)
    if cutoff.tzinfo is None or cutoff.utcoffset() is None:
        raise ValueError("A limpeza exige data com fuso horario.")
    result = session.execute(delete(GuidanceCall).where(GuidanceCall.expires_at <= cutoff))
    return int(result.rowcount or 0)


def cleanup_once() -> int:
    with Session(get_engine()) as session:
        try:
            # A worker must not wait indefinitely behind an abandoned transaction.
            session.execute(text("SET LOCAL statement_timeout = '10000'"))
            count = cleanup_expired(session)
            session.commit()
            return count
        except SQLAlchemyError:
            session.rollback()
            raise


def run_worker(*, watch: bool, stop: Event, cleanup: Callable[[], int] | None = None) -> int:
    operation = cleanup or cleanup_once
    while not stop.is_set():
        try:
            count = operation()
            print(f"Limpeza IA: {count} registros expirados removidos.", flush=True)
        except (SQLAlchemyError, ValueError):
            # Exception text may include connection strings or private SQL parameters.
            print("Limpeza IA indisponivel; confira banco e configuracao local.", flush=True)
            if not watch:
                return 1
        if not watch:
            return 0
        stop.wait(POLL_SECONDS)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apaga somente registros de IA expirados.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="Executa uma limpeza e encerra (padrao).")
    mode.add_argument("--watch", action="store_true", help="Repete a cada 300 segundos.")
    args = parser.parse_args(argv)
    stop = Event()

    def shutdown(_signal, _frame):
        stop.set()

    handled = [signal.SIGINT, signal.SIGTERM]
    if hasattr(signal, "SIGBREAK"):
        handled.append(signal.SIGBREAK)
    previous = {number: signal.signal(number, shutdown) for number in handled}
    try:
        return run_worker(watch=args.watch, stop=stop)
    finally:
        for number, handler in previous.items():
            signal.signal(number, handler)


if __name__ == "__main__":
    raise SystemExit(main())
