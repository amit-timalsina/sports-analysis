from auth.schemas.identity_provider import IdentityProvider
from common.schemas.app_base_model import AppBaseModel


class UserIdentityBase(AppBaseModel):
    """Represents a user identity for a given identity provider."""

    provider: IdentityProvider
    provider_user_id: str
