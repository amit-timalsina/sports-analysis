from typing import Annotated

from pydantic import field_validator
from pydantic_settings import SettingsConfigDict

from common.cache_settings import cached_settings
from common.schemas.app_base_settings import AppBaseSettings


class CorsSettings(AppBaseSettings):
    """CORS configuration settings."""

    allow_origins: Annotated[str, "Allowed origins for CORS"] = "http://localhost:3000"
    allow_credentials: Annotated[bool, "Allow credentials for CORS"] = True
    allow_methods: Annotated[str, "Allowed methods for CORS"] = "*"
    allow_headers: Annotated[str, "Allowed headers for CORS"] = "*"

    model_config = SettingsConfigDict(env_prefix="APP_CORS_")

    @field_validator("allow_origins")
    @classmethod
    def parse_allow_origins(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v

    @field_validator("allow_methods")
    @classmethod
    def parse_allow_methods(cls, v):
        if isinstance(v, str) and v != "*":
            return v.split(",")
        return v

    @field_validator("allow_headers")
    @classmethod
    def parse_allow_headers(cls, v):
        if isinstance(v, str) and v != "*":
            return v.split(",")
        return v


get_cors_settings = cached_settings(CorsSettings)
