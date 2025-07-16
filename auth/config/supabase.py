from typing import Annotated

from pydantic_settings import SettingsConfigDict

from common.cache_settings import cached_settings
from common.schemas.app_base_settings import AppBaseSettings


class SupabaseSettings(AppBaseSettings):
    """Configuration for the supabase client."""

    url: Annotated[str, "URL of the Supabase instance"] = "unique supabase url"
    jwt_secret: Annotated[str, "JWT secret for the Supabase instance"] = "unique jwt secret"
    key: Annotated[str, "Key of the Supabase project (Service Role)"] = "Supabase service role key "

    model_config = SettingsConfigDict(env_prefix="SUPABASE_")


get_supabase_settings = cached_settings(SupabaseSettings)
