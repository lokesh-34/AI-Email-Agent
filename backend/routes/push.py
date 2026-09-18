# ============================================================
# PUSH NOTIFICATION ROUTES
# ============================================================
#
# Endpoints for managing FCM device tokens and
# testing push notifications.
# ============================================================

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.routes.auth import get_current_user
from backend.user_store import (
    add_fcm_token,
    remove_single_fcm_token
)

router = APIRouter()


# ============================================================
# REQUEST MODELS
# ============================================================

class FCMTokenRequest(BaseModel):
    token: str


# ============================================================
# REGISTER DEVICE TOKEN
# ============================================================

@router.post("/api/push/register")
async def register_push_token(
    request: FCMTokenRequest,
    user_email: str = Depends(get_current_user)
):
    """
    Register an FCM device token for push notifications.

    Called by the frontend after obtaining a token
    from Firebase Cloud Messaging.
    """

    add_fcm_token(user_email, request.token)

    return {
        "success": True,
        "message": "Push notification token registered."
    }


# ============================================================
# UNREGISTER DEVICE TOKEN
# ============================================================

@router.post("/api/push/unregister")
async def unregister_push_token(
    request: FCMTokenRequest,
    user_email: str = Depends(get_current_user)
):
    """
    Remove an FCM device token.

    Called when user disables notifications or
    signs out.
    """

    remove_single_fcm_token(user_email, request.token)

    return {
        "success": True,
        "message": "Push notification token removed."
    }


# ============================================================
# TEST PUSH NOTIFICATION
# ============================================================

@router.post("/api/push/test")
async def test_push_notification(
    user_email: str = Depends(get_current_user)
):
    """
    Send a test push notification to verify setup.
    """

    from backend.push_notifications import send_push_notification

    send_push_notification(
        user_email=user_email,
        title="🔔 Test Notification",
        body="Push notifications are working! You'll receive alerts when new emails are processed.",
        data={"type": "test"}
    )

    return {
        "success": True,
        "message": "Test notification sent."
    }
