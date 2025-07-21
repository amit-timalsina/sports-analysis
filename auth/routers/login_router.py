import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from supabase import Client, create_client

from auth.config.supabase import get_supabase_settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["authentication"])


# Initialize Supabase client with settings from environment variables
supabase_settings = get_supabase_settings()


# Supabase client
supabase: Client = create_client(
    supabase_settings.url,
    supabase_settings.key,
)


# Request model for login
class LoginRequest(BaseModel):
    """Login request model containing email and password."""

    email: str
    password: str


# Serve index.html at root


@router.post("/api/login")
async def login(request: LoginRequest) -> dict:
    """
    Authenticate user with email and password.

    Parameters
    ----------
    request : LoginRequest
        Login request containing email and password.

    Returns
    -------
    dict
        Dictionary containing authentication result with access token, user ID, email, and redirect URL.

    Raises
    ------
    HTTPException
        If authentication fails or an error occurs during the process.
    """
    logger.info("Received login request")
    try:
        response = supabase.auth.sign_in_with_password(
            {"email": request.email, "password": request.password},
        )
        if response.user:
            logger.info("User authenticated")
            return {
                "message": "Success: User authenticated!",
                "access_token": response.session.access_token,
                "user_id": response.user.id,
                "email": response.user.email,
                "redirect": "/email",
            }
        else:
            raise HTTPException(
                status_code=401, detail="Authentication failed: Invalid email or password."
            )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


@router.get("/email/{token}", response_class=HTMLResponse)
async def serve_email(token: str) -> HTMLResponse:
    try:
        user = supabase.auth.get_user(token)
        email = user.user.email if user and user.user else None
        if not email:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        static_path = Path("static")
        html_file = static_path / "email.html"

        return HTMLResponse(content=html_file.read_text(), status_code=200)
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed")
