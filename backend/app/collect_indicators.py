import argparse
import time

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.database.session import get_engine
from app.modules.indicators.collection import collect
from app.modules.users.models import User


def main():
    parser = argparse.ArgumentParser(
        description="Coletor oficial diário; execute como processo supervisionado."
    )
    parser.add_argument("--username", required=True)
    parser.add_argument("--watch", action="store_true")
    parser.add_argument(
        "--now",
        action="store_true",
        help="Operador: executar uma coleta imediata registrada, após reparo do coletor",
    )
    args = parser.parse_args()
    while True:
        with Session(get_engine()) as session:
            actor = session.scalar(
                select(User).where(
                    User.username == args.username, User.is_active.is_(True), User.role == "ADMIN"
                )
            )
            if actor is None:
                parser.error("Use um administrador ativo.")
            try:
                result = collect(session, actor, ignore_cooldown=args.now)
            except (DomainError, SQLAlchemyError) as error:
                if not args.watch:
                    raise
                print("Coleta adiada: " + type(error).__name__, flush=True)
                result = {"skipped": True}
            args.now = False
            print(
                "Coleta: "
                + (
                    "aguardando janela diária"
                    if result["skipped"]
                    else result["last_run"]["status"]
                ),
                flush=True,
            )
        if not args.watch:
            return
        time.sleep(900)


if __name__ == "__main__":
    main()
