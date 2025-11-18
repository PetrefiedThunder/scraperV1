"""
SQLAlchemy base model.

All database models inherit from this base class.
"""

from sqlalchemy.orm import DeclarativeBase, declared_attr
from typing import Any


class Base(DeclarativeBase):
    """Base class for all database models."""

    id: Any
    __name__: str

    # Generate __tablename__ automatically
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower()
