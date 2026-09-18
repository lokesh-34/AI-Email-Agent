# ============================================================
# DRAFT ROUTES
# ============================================================

import sys
import os
import logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi import APIRouter, HTTPException, Depends

from backend.models import DraftUpdate, MessageResponse
from backend.routes.auth import get_current_user
from backend.user_store import get_user_google_creds

from database import (
    get_all_drafts,
    get_draft_by_id,
    update_draft,
    approve_draft,
    reject_draft,
    mark_draft_sent
)

from gmail_sender import send_email

router = APIRouter()
logger = logging.getLogger(__name__)


def clean_draft_for_api(draft):
    """Remove MongoDB _id from draft."""
    if draft is None:
        return None

    draft.pop("_id", None)
    return draft


@router.get("/api/drafts")
async def list_drafts(status: str = None):
    """Get all drafts, optionally filtered by status."""

    try:
        drafts = get_all_drafts(status=status)
        return [
            clean_draft_for_api(draft)
            for draft in drafts
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch drafts: {str(e)}"
        )


@router.get("/api/drafts/{draft_id}")
async def get_draft(draft_id: str):
    """Get a single draft by draft_id."""

    try:
        draft = get_draft_by_id(draft_id)

        if not draft:
            raise HTTPException(
                status_code=404,
                detail="Draft not found."
            )

        return clean_draft_for_api(draft)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch draft: {str(e)}"
        )


@router.put("/api/drafts/{draft_id}")
async def update_draft_endpoint(
    draft_id: str,
    updates: DraftUpdate
):
    """Update a draft (recipient, subject, body)."""

    try:
        draft = get_draft_by_id(draft_id)

        if not draft:
            raise HTTPException(
                status_code=404,
                detail="Draft not found."
            )

        if draft.get("status") == "sent":
            raise HTTPException(
                status_code=400,
                detail="Cannot edit a sent draft."
            )

        update_data = {}

        if updates.recipient is not None:
            update_data["recipient"] = updates.recipient

        if updates.subject is not None:
            update_data["subject"] = updates.subject

        if updates.body is not None:
            update_data["body"] = updates.body

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No fields to update."
            )

        success = update_draft(draft_id, update_data)

        if success:
            updated = get_draft_by_id(draft_id)
            return clean_draft_for_api(updated)
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to update draft."
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update draft: {str(e)}"
        )


@router.post("/api/drafts/{draft_id}/approve")
async def approve_draft_endpoint(draft_id: str):
    """Approve a draft for sending."""

    try:
        draft = get_draft_by_id(draft_id)

        if not draft:
            raise HTTPException(
                status_code=404,
                detail="Draft not found."
            )

        if draft.get("status") == "sent":
            return {
                "message": "Draft has already been sent.",
                "success": True
            }

        if draft.get("status") == "approved":
            return {
                "message": "Draft is already approved.",
                "success": True
            }

        success = approve_draft(draft_id)

        if success:
            return {
                "message": "Draft approved.",
                "success": True
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to approve draft."
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve draft: {str(e)}"
        )


@router.post("/api/drafts/{draft_id}/send")
async def send_draft_endpoint(
    draft_id: str,
    user_email: str = Depends(get_current_user)
):
    """
    Send an approved draft via Gmail.

    SAFETY: This is the only endpoint that sends email.
    It requires explicit user action through the frontend.

    DUPLICATE PROTECTION: Will not send if status is 'sent'.
    """

    try:
        draft = get_draft_by_id(draft_id)

        if not draft:
            raise HTTPException(
                status_code=404,
                detail="Draft not found."
            )

        # ============================================
        # DUPLICATE SEND PROTECTION
        # ============================================

        if draft.get("status") == "sent":
            return {
                "message": "Email already sent.",
                "success": True,
                "gmail_message_id": draft.get(
                    "gmail_message_id"
                )
            }

        if draft.get("status") == "rejected":
            raise HTTPException(
                status_code=400,
                detail="Cannot send a rejected draft. "
                       "Create a new draft instead."
            )

        # ============================================
        # VALIDATE DRAFT HAS REQUIRED FIELDS
        # ============================================

        recipient = draft.get("recipient")
        subject = draft.get("subject")
        body = draft.get("body")

        if not recipient:
            raise HTTPException(
                status_code=400,
                detail="Draft has no recipient."
            )

        if not body:
            raise HTTPException(
                status_code=400,
                detail="Draft has no body."
            )

        # ============================================
        # SEND VIA GMAIL
        # ============================================

        creds = get_user_google_creds(user_email)

        result = send_email(
            recipient=recipient,
            subject=subject or "",
            body=body,
            reply_to_message_id=draft.get("message_id"),
            creds=creds
        )

        if result["success"]:

            gmail_message_id = result["gmail_message_id"]

            mark_draft_sent(
                draft_id,
                gmail_message_id
            )

            logger.info(
                "Email sent via draft %s. "
                "Gmail ID: %s",
                draft_id,
                gmail_message_id
            )

            return {
                "message": "Email sent successfully.",
                "success": True,
                "gmail_message_id": gmail_message_id
            }

        else:
            raise HTTPException(
                status_code=500,
                detail=f"Gmail send failed: "
                       f"{result.get('error', 'Unknown error')}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to send draft %s: %s",
            draft_id,
            str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send email: {str(e)}"
        )


@router.post("/api/drafts/{draft_id}/reject")
async def reject_draft_endpoint(draft_id: str):
    """Reject a draft."""

    try:
        draft = get_draft_by_id(draft_id)

        if not draft:
            raise HTTPException(
                status_code=404,
                detail="Draft not found."
            )

        if draft.get("status") == "sent":
            raise HTTPException(
                status_code=400,
                detail="Cannot reject a sent draft."
            )

        success = reject_draft(draft_id)

        if success:
            return {
                "message": "Draft rejected.",
                "success": True
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to reject draft."
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reject draft: {str(e)}"
        )
