# ============================================================
# PROCESSING ROUTES
# ============================================================

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi import APIRouter, HTTPException, Depends

from main import process_emails
from backend.routes.auth import get_current_user
from backend.user_store import get_user_google_creds

router = APIRouter()


@router.post("/api/process-emails")
async def trigger_processing(
    max_results: int = 10,
    user_email: str = Depends(get_current_user)
):
    """
    Trigger email processing pipeline.

    Fetches new emails from Gmail, parses them with AI,
    creates tasks, calendar events, and reply drafts.
    """

    try:
        creds = get_user_google_creds(user_email)

        result = process_emails(
            max_results=max_results,
            creds=creds
        )
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Email processing failed: {str(e)}"
        )
