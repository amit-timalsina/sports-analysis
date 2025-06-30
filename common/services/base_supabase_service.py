from collections.abc import AsyncGenerator

from auth.config.supabase import get_supabase_settings
from supabase import Client, create_client


class BaseSupabaseService:
    """
    Base service class for Supabase operations.

    This class provides basic Supabase client functionality and initialization.
    It serves as a base class for other services that need to interact with Supabase.

    Attributes
    ----------
        _client (Client | None): Instance of Supabase client, lazily initialized
        _supabase_settings: Settings for Supabase connection

    Methods
    -------
        client: Property that returns initialized Supabase client instance

    """

    def __init__(self) -> None:
        """Initialize the service."""
        self._client: Client | None = None
        self._supabase_settings = get_supabase_settings()

    @property
    def client(self) -> Client:
        """Get the Supabase client."""
        if self._client is None:
            self._client = create_client(
                self._supabase_settings.url,
                self._supabase_settings.key,
            )
        return self._client

    @classmethod
    async def get_as_dependency(cls) -> AsyncGenerator["BaseSupabaseService", None]:
        """
        Get the Supabase service as a dependency.

        Yields
        ------
            SupabaseService: The Supabase service.

        """
        yield cls()
