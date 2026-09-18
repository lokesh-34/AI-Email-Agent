# ============================================================
# EMAIL ROUTES
# ============================================================

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi import APIRouter, HTTPException, Depends

from gmail_reader import connect_gmail, get_email_for_agent
from backend.routes.auth import get_current_user
from backend.user_store import get_user_google_creds

router = APIRouter()


@router.get("/api/emails/{message_id}")
async def get_email(
    message_id: str,
    user_email: str = Depends(get_current_user)
):
    """Fetch original email from Gmail."""

    try:
        creds = get_user_google_creds(user_email)
        service = connect_gmail(creds=creds)

        email = get_email_for_agent(
            service,
            message_id
        )

        if not email:
            raise HTTPException(
                status_code=404,
                detail="Email not found."
            )

        return email

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch email: {str(e)}"
        )
