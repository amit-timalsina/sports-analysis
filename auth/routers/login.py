import logging

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from supabase import Client, create_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["authentication"])

# Supabase client
supabase: Client = create_client(
    "https://mlinadgevpaabqrqgogb.supabase.co",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1saW5hZGdldnBhYWJxcnFnb2diIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI2NzcxMjQsImV4cCI6MjA2ODI1MzEyNH0.qLCOWiHp4tCez0Y1j5bwgc58URR9JsBQDehKaWQbq3c",
)


# Request model for login
class LoginRequest(BaseModel):
    email: str
    password: str


# Serve index.html at root


@router.post("/api/login")
async def login(request: LoginRequest) -> dict:
    logger.info(f"Received login request: {request}")
    try:
        response = supabase.auth.sign_in_with_password(
            {"email": request.email, "password": request.password},
        )
        if response.user:
            logger.info(f"User authenticated: {request.email}")
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

        return HTMLResponse(
            content=f"""from None  
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>User Email</title>
                <script src="https://cdn.tailwindcss.com"></script>
            </head>
            <body class="bg-gray-100 flex items-center justify-center min-h-screen">
                <div class="bg-white p-8 rounded-lg shadow-lg max-w-md mx-auto">
                    <h2 class="text-2xl font-bold text-center text-gray-800 mb-6">User Email</h2>
                    <p class="text-center text-gray-700">Email: {email}</p>
                    <a href="/" class="mt-4 block text-center text-blue-600 hover:underline">Back to Home</a>
                </div>
            </body>
            </html>
        """
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed")
