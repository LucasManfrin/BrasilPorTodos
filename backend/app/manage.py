"""Explicit local operations; never creates default accounts or passwords."""

import argparse

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.database.session import get_engine
from app.modules.admin.models import record
from app.modules.users.models import User


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["bootstrap-admin"])
    parser.add_argument("--username", required=True)
    parser.add_argument("--reason", required=True)
    args = parser.parse_args()
    with Session(get_engine()) as session:
        session.execute(text("LOCK TABLE users IN SHARE ROW EXCLUSIVE MODE"))
        user = session.scalar(select(User).where(User.username == args.username.lower()))
        if user is None or not user.is_active:
            parser.error("Register an active local account first.")
        existing = session.scalar(select(User).where(User.role == "ADMIN").limit(1))
        if existing:
            parser.error("An administrator already exists; bootstrap refused.")
        user.role = "ADMIN"
        record(session, user, "user", user.id, "BOOTSTRAP_ADMIN", args.reason)
        session.commit()
        print("Local administrator configured. No password or token was printed.")


if __name__ == "__main__":
    main()
