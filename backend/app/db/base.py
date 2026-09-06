from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import models here so Alembic can discover metadata.
from app.models import entities  # noqa: E402,F401
