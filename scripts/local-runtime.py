"""Read-only launcher checks; never print secrets or native tracebacks."""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))


def local_settings():
    from app.core.config import get_settings

    return get_settings()


def configuration() -> int:
    from dotenv import dotenv_values
    from sqlalchemy.engine import make_url

    settings = local_settings()
    database = make_url(settings.database_url)
    frontend = dotenv_values(ROOT / "frontend" / ".env.local")
    print(
        json.dumps(
            {
                "python": sys.executable,
                "db_host": database.host or "localhost",
                "db_port": database.port or 5432,
                "db_name": database.database,
                "db_driver": database.drivername,
                "jwt_ready": bool(
                    settings.jwt_secret and len(settings.jwt_secret.get_secret_value()) >= 32
                ),
                "cookie_secure": settings.cookie_secure,
                "environment": settings.environment,
                "api_url": os.environ.get(
                    "API_INTERNAL_URL", frontend.get("API_INTERNAL_URL", "http://127.0.0.1:8000")
                ),
            }
        )
    )
    return 0


def database_check(schema: bool) -> int:
    from sqlalchemy import create_engine, text

    engine = create_engine(local_settings().database_url, connect_args={"connect_timeout": 4})
    try:
        with engine.connect() as connection:
            connection.execute(text("SET statement_timeout = '5000ms'"))
            connection.execute(text("SELECT 1"))
            if schema:
                from alembic.config import Config
                from alembic.runtime.migration import MigrationContext
                from alembic.script import ScriptDirectory

                actual = set(MigrationContext.configure(connection).get_current_heads())
                expected = set(
                    ScriptDirectory.from_config(Config(str(BACKEND / "alembic.ini"))).get_heads()
                )
                return 0 if actual == expected else 3
        return 0
    finally:
        engine.dispose()


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"configuration", "database", "schema"}:
        return 2
    os.chdir(BACKEND)
    try:
        if sys.argv[1] == "configuration":
            return configuration()
        return database_check(schema=sys.argv[1] == "schema")
    except Exception:
        # Caller emits a fixed actionable message. DSN and exception payload stay private.
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
