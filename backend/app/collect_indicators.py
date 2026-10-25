"""Supervised daily worker; never polls HTTP application endpoints."""

import argparse
import signal
from datetime import UTC, datetime
from threading import Event

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.database.session import get_engine
from app.modules.indicators.collection import collect
from app.modules.indicators.schedule import get_schedule
from app.modules.users.models import User

POLL_SECONDS = 60


def collect_once(username: str | None, *, scheduled: bool, immediate: bool = False):
    with Session(get_engine()) as session:
        statement = select(User).where(User.is_active.is_(True), User.role == "ADMIN")
        if username:
            statement = statement.where(User.username == username)
        actor = session.scalar(statement.order_by(User.created_at, User.id).limit(1))
        if actor is None:
            raise DomainError(
                409, "COLLECTION_ACTOR_REQUIRED", "A coleta exige administrador ativo."
            )
        return collect(session, actor, scheduled=scheduled, ignore_cooldown=immediate)


def run_worker(*, username: str | None, watch: bool, immediate: bool, stop: Event) -> int:
    previous = None
    while not stop.is_set():
        try:
            result = collect_once(username, scheduled=watch, immediate=immediate)
            state = (
                "aguardando horário programado"
                if result["skipped"]
                else result["last_run"]["status"]
            )
            if not result["skipped"] or state != previous:
                print("Coleta: " + state, flush=True)
            previous = state
        except (DomainError, SQLAlchemyError) as error:
            # No raw DB/provider exception or account identity reaches the worker log.
            state = "adiada: " + (
                error.code if isinstance(error, DomainError) else "DATABASE_ERROR"
            )
            if state != previous:
                print("Coleta " + state, flush=True)
            previous = state
            if not watch:
                return 1
        immediate = False
        if not watch:
            return 0
        stop.wait(POLL_SECONDS)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Coletor oficial com horário diário e retomada.")
    parser.add_argument(
        "--username", help="Administrador para atribuição; padrão configurado ou primeiro ativo."
    )
    parser.add_argument("--watch", action="store_true", help="Manter o agendador diário ativo.")
    parser.add_argument(
        "--now", action="store_true", help="Operador: uma coleta imediata após reparo."
    )
    args = parser.parse_args(argv)
    settings = get_schedule()
    if args.watch:
        print(
            f"Coleta diária: {settings.collection_daily_at} ({settings.collection_timezone}); "
            f"retentativa após {settings.collection_retry_minutes} min. "
            f"Início em {datetime.now(UTC).isoformat()}.",
            flush=True,
        )
    stop = Event()

    def shutdown(_signal, _frame):
        stop.set()

    numbers = [signal.SIGINT, signal.SIGTERM]
    if hasattr(signal, "SIGBREAK"):
        numbers.append(signal.SIGBREAK)
    previous = {number: signal.signal(number, shutdown) for number in numbers}
    try:
        return run_worker(
            username=args.username or settings.collection_username,
            watch=args.watch,
            immediate=args.now,
            stop=stop,
        )
    finally:
        for number, handler in previous.items():
            signal.signal(number, handler)


if __name__ == "__main__":
    raise SystemExit(main())
