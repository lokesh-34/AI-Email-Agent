# ============================================================
# USER STORE
# ============================================================
#
# Per-user Google OAuth token storage in MongoDB.
#
# Each user's Google OAuth tokens (access_token, refresh_token)
# are stored in the 'users' collection, keyed by email.
# ============================================================

import os
import sys
import logging

from datetime import datetime

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()

logger = logging.getLogger(__name__)

MONGODB_URI = os.getenv("MONGODB_URI")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


# ============================================================
# MONGODB CONNECTION
# ============================================================

client = MongoClient(
    MONGODB_URI,
    server_api=ServerApi(
        version="1",
        strict=False,
        deprecation_errors=True
    )
)

db = client["academic_agent"]
users_collection = db["users"]


# ============================================================
# ENSURE INDEXES
# ============================================================

def ensure_user_indexes():
    """Create indexes on users collection."""
    try:
        users_collection.create_index(
            "email",
            unique=True
        )
        logger.info("User indexes ensured.")
    except Exception as e:
        logger.warning(
            "User index warning: %s", str(e)
        )


# ============================================================
# SAVE USER TOKENS
# ============================================================

def save_user_tokens(email, tokens, profile=None):
    """
    Save or update a user's Google OAuth tokens.

    Parameters:
        email: User's email address
        tokens: dict with access_token, refresh_token,
                token_uri, expiry, etc.
        profile: Optional dict with name, picture, etc.
    """

    update_data = {
        "email": email,
        "access_token": tokens.get("access_token"),
        "refresh_token": tokens.get("refresh_token"),
        "token_uri": tokens.get(
            "token_uri",
            "https://oauth2.googleapis.com/token"
        ),
        "expiry": tokens.get("expiry"),
        "updated_at": datetime.utcnow().isoformat(),
    }

    if profile:
        update_data["name"] = profile.get("name", "")
        update_data["picture"] = profile.get("picture", "")

    users_collection.update_one(
        {"email": email},
        {
            "$set": update_data,
            "$setOnInsert": {
                "created_at": datetime.utcnow().isoformat()
            }
        },
        upsert=True
    )

    logger.info("Tokens saved for user: %s", email)


# ============================================================
# GET USER TOKENS
# ============================================================

def get_user_tokens(email):
    """Get a user's stored tokens."""

    user = users_collection.find_one({"email": email})

    if not user:
        return None

    return user


# ============================================================
# DELETE USER TOKENS
# ============================================================

def delete_user_tokens(email):
    """Delete a user's tokens (sign out / revoke)."""

    result = users_collection.delete_one({"email": email})
    return result.deleted_count > 0


# ============================================================
# GET GOOGLE CREDENTIALS FOR USER
# ============================================================

def get_user_google_creds(email):
    """
    Load user's Google OAuth credentials from MongoDB.

    Returns a google.oauth2.credentials.Credentials object
    ready to use with Google API clients.

    Automatically refreshes expired tokens.
    """

    user = get_user_tokens(email)

    if not user:
        raise ValueError(
            f"No Google credentials found for {email}. "
            "Please sign in with Google first."
        )

    access_token = user.get("access_token")
    refresh_token = user.get("refresh_token")
    token_uri = user.get(
        "token_uri",
        "https://oauth2.googleapis.com/token"
    )
    expiry = user.get("expiry")

    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=SCOPES
    )

    # --------------------------------------------------------
    # Refresh if expired
    # --------------------------------------------------------

    if creds.expired and creds.refresh_token:

        try:
            creds.refresh(Request())

            # Save refreshed tokens back to MongoDB
            save_user_tokens(email, {
                "access_token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri": token_uri,
                "expiry": (
                    creds.expiry.isoformat()
                    if creds.expiry else None
                ),
            })

            logger.info(
                "Refreshed tokens for user: %s", email
            )

        except Exception as e:
            logger.error(
                "Failed to refresh tokens for %s: %s",
                email, str(e)
            )
            raise ValueError(
                "Google credentials expired and could not "
                "be refreshed. Please sign in again."
            )

    return creds


# ============================================================
# FCM TOKEN MANAGEMENT
# ============================================================

def add_fcm_token(email, fcm_token):
    """Add an FCM device token for a user."""

    users_collection.update_one(
        {"email": email},
        {"$addToSet": {"fcm_tokens": fcm_token}}
    )

    logger.info(
        "FCM token registered for user: %s", email
    )


def get_user_fcm_tokens(email):
    """Get all FCM tokens for a user."""

    user = users_collection.find_one(
        {"email": email},
        {"fcm_tokens": 1}
    )

    if not user:
        return []

    return user.get("fcm_tokens", [])


def remove_fcm_tokens(email, tokens_to_remove):
    """Remove specific FCM tokens for a user."""

    users_collection.update_one(
        {"email": email},
        {"$pullAll": {"fcm_tokens": tokens_to_remove}}
    )

    logger.info(
        "Removed %d FCM token(s) for user: %s",
        len(tokens_to_remove),
        email
    )


def remove_single_fcm_token(email, fcm_token):
    """Remove a single FCM token for a user."""

    users_collection.update_one(
        {"email": email},
        {"$pull": {"fcm_tokens": fcm_token}}
    )
