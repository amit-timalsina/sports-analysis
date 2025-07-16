from enum import StrEnum


class IdentityProvider(StrEnum):
    """Defines the identity providers that can be used for authentication."""

    SUPABASE = "SUPABASE"
    FIREBASE = "FIREBASE"
