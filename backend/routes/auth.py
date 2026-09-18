# ============================================================
# AUTH ROUTES — GOOGLE OAUTH
# ============================================================
#
# Handles Google OAuth flow for per-user Gmail access.
#
# Flow:
#   1. Frontend calls GET /api/auth/google/login
#   2. Backend redirects to Google consent screen
#   3. Google redirects to GET /api/auth/google/callback
#   4. Backend exchanges code for tokens, stores them,
#      creates JWT, redirects to frontend with token
# ============================================================

import os
import sys
import jwt
import logging
import requests as http_requests

from datetime import datetime, timedelta
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from dotenv import load_dotenv


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

load_dotenv(override=True)

router = APIRouter()
logger = logging.getLogger(__name__)
security = HTTPBearer()


# ============================================================
# CONFIG
# ============================================================

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
JWT_SECRET = os.getenv("JWT_SECRET", "email-copilot-secret-key-change-me")
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
MOBILE_REDIRECT_URI = os.getenv(
    "MOBILE_REDIRECT_URI",
    "com.lokesh.aiemailagent://auth/callback"
)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
]


# ============================================================
# JWT HELPERS
# ============================================================

def create_token(email, name="", picture=""):
    """Create a JWT access token with user info."""

    payload = {
        "sub": email,
        "name": name,
        "picture": picture,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(
            hours=JWT_EXPIRY_HOURS
        )
    }

    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def verify_token(token):
    """Verify and decode a JWT token."""

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"]
        )
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired."
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token."
        )


# ============================================================
# AUTH DEPENDENCY
# ============================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    FastAPI dependency that validates the JWT token.
    Returns the user's email address.
    """

    payload = verify_token(credentials.credentials)
    return payload["sub"]


# ============================================================
# GOOGLE OAUTH: INITIATE LOGIN
# ============================================================

@router.get("/api/auth/google/login")
async def google_login(platform: str = "web"):
    """
    Redirect user to Google OAuth consent screen.

    The frontend navigates here. Google will redirect
    back to /api/auth/google/callback with an auth code.
    """

    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_CLIENT_ID not configured."
        )

    redirect_uri = f"{BACKEND_URL}/api/auth/google/callback"

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": "android" if platform == "android" else "web",
    }

    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    return RedirectResponse(url=auth_url)


# ============================================================
# GOOGLE OAUTH: CALLBACK
# ============================================================

@router.get("/api/auth/google/callback")
async def google_callback(
    code: str = None,
    error: str = None,
    state: str = "web"
):
    """
    Google redirects here after user authorizes.

    Exchanges the auth code for tokens, fetches user info,
    stores tokens in MongoDB, creates JWT, and redirects
    to the frontend with the token.
    """

    if error:
        logger.warning("Google OAuth error: %s", error)
        if state == "android":
            return RedirectResponse(
                url=(
                    f"{MOBILE_REDIRECT_URI}?"
                    f"{urlencode({'auth_error': error})}"
                )
            )
        return RedirectResponse(
            url=f"{FRONTEND_URL}?auth_error={error}"
        )

    if not code:
        if state == "android":
            return RedirectResponse(
                url=(
                    f"{MOBILE_REDIRECT_URI}?"
                    f"{urlencode({'auth_error': 'no_code'})}"
                )
            )
        return RedirectResponse(
            url=f"{FRONTEND_URL}?auth_error=no_code"
        )

    # --------------------------------------------------------
    # Exchange auth code for tokens
    # --------------------------------------------------------

    redirect_uri = f"{BACKEND_URL}/api/auth/google/callback"

    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    try:
        token_response = http_requests.post(
            GOOGLE_TOKEN_URL,
            data=token_data,
            timeout=10
        )

        token_response.raise_for_status()
        tokens = token_response.json()

    except Exception as e:
        logger.error(
            "Token exchange failed: %s", str(e)
        )
        return RedirectResponse(
            url=f"{FRONTEND_URL}?auth_error=token_exchange_failed"
        )

    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")

    if not access_token:
        return RedirectResponse(
            url=f"{FRONTEND_URL}?auth_error=no_access_token"
        )

    # --------------------------------------------------------
    # Fetch user info
    # --------------------------------------------------------

    try:
        userinfo_response = http_requests.get(
            GOOGLE_USERINFO_URL,
            headers={
                "Authorization": f"Bearer {access_token}"
            },
            timeout=10
        )

        userinfo_response.raise_for_status()
        userinfo = userinfo_response.json()

    except Exception as e:
        logger.error(
            "Failed to fetch user info: %s", str(e)
        )
        return RedirectResponse(
            url=f"{FRONTEND_URL}?auth_error=userinfo_failed"
        )

    email = userinfo.get("email")
    name = userinfo.get("name", "")
    picture = userinfo.get("picture", "")

    if not email:
        return RedirectResponse(
            url=f"{FRONTEND_URL}?auth_error=no_email"
        )

    # --------------------------------------------------------
    # Calculate token expiry
    # --------------------------------------------------------

    expires_in = tokens.get("expires_in", 3600)
    expiry = (
        datetime.utcnow() + timedelta(seconds=expires_in)
    ).isoformat()

    # --------------------------------------------------------
    # Store tokens in MongoDB
    # --------------------------------------------------------

    from backend.user_store import save_user_tokens

    save_user_tokens(
        email=email,
        tokens={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_uri": GOOGLE_TOKEN_URL,
            "expiry": expiry,
        },
        profile={
            "name": name,
            "picture": picture,
        }
    )

    logger.info("User signed in: %s (%s)", name, email)

    # --------------------------------------------------------
    # Create JWT and redirect to frontend
    # --------------------------------------------------------

    jwt_token = create_token(
        email=email,
        name=name,
        picture=picture
    )

    redirect_url = (
        f"{FRONTEND_URL}"
        f"?token={jwt_token}"
        f"&email={email}"
        f"&name={name}"
        f"&picture={picture}"
    )

    if state == "android":
        mobile_params = urlencode({
            "token": jwt_token,
            "email": email,
            "name": name,
            "picture": picture,
        })
        redirect_url = f"{MOBILE_REDIRECT_URI}?{mobile_params}"

    return RedirectResponse(url=redirect_url)


# ============================================================
# GET CURRENT USER INFO
# ============================================================

@router.get("/api/auth/me")
async def get_me(
    email: str = Depends(get_current_user)
):
    """Get current authenticated user."""

    from backend.user_store import get_user_tokens

    user = get_user_tokens(email)

    return {
        "email": email,
        "name": user.get("name", "") if user else "",
        "picture": user.get("picture", "") if user else "",
        "authenticated": True,
        "gmail_connected": user is not None,
    }


# ============================================================
# SIGN OUT
# ============================================================

@router.post("/api/auth/logout")
async def logout(
    email: str = Depends(get_current_user)
):
    """Sign out — remove stored tokens."""

    from backend.user_store import delete_user_tokens

    delete_user_tokens(email)

    logger.info("User signed out: %s", email)

    return {"message": "Signed out.", "success": True}
