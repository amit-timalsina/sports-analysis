from typing import Any

import jwt
from gotrue.types import AuthResponse  # type: ignore[import-untyped]

from common.services.base_supabase_service import BaseSupabaseService


class AuthSupabaseService(BaseSupabaseService):
    """Service to interact with Supabase."""

    def _decode_access_token(self, access_token: str) -> dict[str, Any]:
        """
        Decode the access token.

        Args:
        ----
            access_token: The access token to decode.

        Returns:
        -------
            The decoded access token.

        """
        return jwt.decode(
            access_token,
            key=self._supabase_settings.jwt_secret,
            do_verify=True,
            algorithms=["HS256"],
            audience="authenticated",
        )

    def get_current_user_supabase_id(self, access_token: str) -> str:
        """
        Get the Supabase ID of the current user.

        Args:
        ----
            access_token: The access token of the current user.

        Returns:
        -------
            The Supabase ID of the current user.

        """
        return self._decode_access_token(access_token)["sub"]

    def refresh_access_token(self, refresh_token: str) -> AuthResponse:
        """
        Refresh the access token using a refresh token.

        This method calls Supabase client's auth.refresh_session to get a new access token
        using the provided refresh token.

        Args:
        ----
            refresh_token (str): The refresh token used to obtain a new access token

        Returns:
        -------
            AuthResponse: Response containing the new access token and session information

        Raises:
        ------
            AuthError: If the refresh token is invalid or expired

        """
        return self.client.auth.refresh_session(refresh_token)
