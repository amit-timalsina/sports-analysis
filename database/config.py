from typing import Annotated

from pydantic_settings import SettingsConfigDict

from common.cache_settings import cached_settings
from common.schemas.app_base_settings import AppBaseSettings


class DatabaseSettings(AppBaseSettings):
    """Database settings."""

    host: Annotated[str, "Database host"] = "db"
    port: Annotated[int, "Database port"] = 5432
    username: Annotated[str, "Database username"] = "postgres"
    password: Annotated[str, "Database password"] = "postgres"
    database: Annotated[str, "Database name"] = "postgres"
    driver: Annotated[str, "Database driver"] = "postgresql"
    async_driver: Annotated[str, "Asynchronous database driver"] = "asyncpg"

    model_config = SettingsConfigDict(env_prefix="DB_")

    @property
    def database_url(self) -> str:
        """
        Generate the database URL string.

        Returns
        -------
            str: The formatted database URL.

        """
        return f"{self.driver}+{self.async_driver}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


get_database_settings = cached_settings(DatabaseSettings)
