"""Seed (or promote) the first admin so someone can invite everyone else.

    python -m backend.app.seed --admin you@temple.edu [--name "Your Name"]

Run *after* ``alembic upgrade head`` — this only writes a row, it does not
create tables. Idempotent: re-running promotes/reactivates the same email.
"""

from __future__ import annotations

import argparse

from sqlalchemy import select

from backend.app.core.database import SessionLocal
from backend.app.models.user import User


def seed_admin(email: str, name: str = "") -> str:
    email = email.strip().lower()
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            db.add(User(email=email, name=name, is_admin=True))
            db.commit()
            return f"Created admin: {email}"
        user.is_admin = True
        user.is_active = True
        if name and not user.name:
            user.name = name
        db.commit()
        return f"Promoted existing user to admin: {email}"
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the first admin user.")
    parser.add_argument("--admin", required=True, help="admin email (e.g. you@temple.edu)")
    parser.add_argument("--name", default="", help="optional display name")
    args = parser.parse_args()
    print(seed_admin(args.admin, args.name))


if __name__ == "__main__":
    main()
