import logging
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import SettingsConfigDict

from common.cache_settings import cached_settings
from common.schemas.app_base_settings import AppBaseSettings


class LogSettings(AppBaseSettings):
    """Logging settings."""

    level: Annotated[int | str, "Logging level"] = Field(default=logging.INFO)

    model_config = SettingsConfigDict(env_prefix="APP_LOG_")

    @field_validator("level", mode="before")
    @classmethod
    def parse_log_level(cls: type["LogSettings"], v: int | str) -> int:
        """
        Parse and validate the log level.

        Args:
        ----
            cls: The class object.
            v: The input value to be parsed.

        Returns:
        -------
            int: The parsed log level as an integer.

        Raises:
        ------
            ValueError: If the input is not a valid log level.

        """
        if isinstance(v, int):
            return v
        try:
            levels_map = logging.getLevelNamesMapping()
            return levels_map[v.upper()]
        except KeyError as err:
            msg = f"Invalid log level: {v}"
            raise ValueError(msg) from err


get_log_settings = cached_settings(LogSettings)
