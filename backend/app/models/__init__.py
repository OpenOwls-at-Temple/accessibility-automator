"""ORM models. Importing this package registers every model on ``Base`` so
Alembic autogenerate and ``create_all`` see the full schema.
"""

from backend.app.models.user import User

__all__ = ["User"]
