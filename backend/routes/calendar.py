# ============================================================
# CALENDAR ROUTES
# ============================================================

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi import APIRouter, HTTPException, Depends

from google_calendar import get_upcoming_calendar_events
from backend.routes.auth import get_current_user
from backend.user_store import get_user_google_creds

router = APIRouter()


@router.get("/api/calendar/events")
async def get_calendar_events(
    max_results: int = 20,
    user_email: str = Depends(get_current_user)
):
    """Get upcoming Google Calendar events."""

    try:
        creds = get_user_google_creds(user_email)

        events = get_upcoming_calendar_events(
            max_results=max_results,
            creds=creds
        )
        return events

    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch calendar events: {str(e)}"
        )
