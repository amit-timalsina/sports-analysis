from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

from common.mixins.base_model_mixin import BaseModelMixin

# Define naming conventions for database constraints and indexes
# Default naming convention only has ix
convention = {
    # Foreign Key: fk_<table_name>_<column_name>_<referred_table_name>
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    # Unique Constraint: uq_<table_name>_<column_name>
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    # Check Constraint: ck_<table_name>_<constraint_name>
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    # Index: ix_<table_name>_<column_name>
    "ix": "ix_%(table_name)s_%(column_0_name)s",
}


class Base(AsyncAttrs, DeclarativeBase):
    """Async Sqlalchemy Declarative Base."""


class CommonBase(BaseModelMixin, Base):
    """
    Common base for all models.

    Developers should add new functionality to this class instead of ProductionBase or TestBase.
    This ensures that ProductionBase and TestBase remain as similar as possible, providing better
    testing guarantees.
    """

    __abstract__ = True


class ProductionBase(CommonBase):
    """
    Base for all models in production.

    This helps us to specify a clear target for the exact models we want to use in production.
    Note: Alembic will create migrations for all models that inherit from this base.

    Important: Do not add functionality directly to this class. Instead, add it to CommonBase.
    """

    __abstract__ = True
    metadata = MetaData(naming_convention=convention)


class TestBase(CommonBase):
    """
    Base for all models in test.

    This helps us to specify a clear target for the exact models we want to use in test.
    Note: These models will be skipped during migrations.

    Important: Do not add functionality directly to this class. Instead, add it to CommonBase.
    """

    __abstract__ = True
    metadata = MetaData(naming_convention=convention)
