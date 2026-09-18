# ============================================================
# NOTIFICATION ROUTES
# ============================================================

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from datetime import datetime

from fastapi import APIRouter, HTTPException

from database import (
    get_pending_tasks,
    get_high_priority_tasks,
    get_all_drafts
)

router = APIRouter()


@router.get("/api/notifications")
async def get_notifications():
    """
    Derive notifications from tasks and drafts.

    Prioritizes:
    - High priority tasks
    - Tasks with upcoming deadlines
    - Tasks requiring replies
    - Tasks with calendar events
    - Pending drafts
    """

    try:
        notifications = []
        today = datetime.now().strftime("%Y-%m-%d")

        # ================================================
        # HIGH PRIORITY TASKS
        # ================================================

        high_tasks = get_high_priority_tasks()

        for task in high_tasks:
            notifications.append({
                "id": f"task-{task.get('message_id')}",
                "title": task.get("title", ""),
                "description": task.get("action", ""),
                "priority": "high",
                "category": task.get("category"),
                "type": "task",
                "date": task.get("deadline"),
                "action": task.get("action"),
                "message_id": task.get("message_id"),
                "draft_id": None
            })

        # ================================================
        # REPLY-REQUIRED TASKS
        # ================================================

        pending_tasks = get_pending_tasks()

        for task in pending_tasks:

            # Skip already-added high priority tasks
            if task.get("priority") == "high":
                continue

            if task.get("reply_required"):
                notifications.append({
                    "id": f"reply-{task.get('message_id')}",
                    "title": f"Reply needed: {task.get('title', '')}",
                    "description": task.get(
                        "ai_explanation",
                        "This email requires a reply."
                    ),
                    "priority": "medium",
                    "category": task.get("category"),
                    "type": "reply",
                    "date": task.get("deadline"),
                    "action": "Review and send reply",
                    "message_id": task.get("message_id"),
                    "draft_id": None
                })

            # Upcoming deadline
            elif (
                task.get("deadline")
                and task["deadline"] >= today
                and task["deadline"] <= (
                    datetime.now().strftime("%Y-%m-%d")
                )
            ):
                notifications.append({
                    "id": f"deadline-{task.get('message_id')}",
                    "title": f"Deadline: {task.get('title', '')}",
                    "description": task.get("action", ""),
                    "priority": "medium",
                    "category": task.get("category"),
                    "type": "deadline",
                    "date": task.get("deadline"),
                    "action": task.get("action"),
                    "message_id": task.get("message_id"),
                    "draft_id": None
                })

            # Calendar events
            elif task.get("event_required"):
                notifications.append({
                    "id": f"event-{task.get('message_id')}",
                    "title": task.get(
                        "event_title",
                        task.get("title", "")
                    ),
                    "description": (
                        f"{task.get('event_date', '')} "
                        f"{task.get('event_start_time', '')}"
                    ),
                    "priority": task.get("priority", "medium"),
                    "category": task.get("category"),
                    "type": "event",
                    "date": task.get("event_date"),
                    "action": "View event",
                    "message_id": task.get("message_id"),
                    "draft_id": None
                })

        # ================================================
        # PENDING DRAFTS
        # ================================================

        drafts = get_all_drafts(status="draft")

        for draft in drafts:
            notifications.append({
                "id": f"draft-{draft.get('draft_id')}",
                "title": f"Draft reply: {draft.get('subject', '')}",
                "description": f"To: {draft.get('recipient', '')}",
                "priority": "medium",
                "category": None,
                "type": "draft",
                "date": draft.get("created_at"),
                "action": "Review and send",
                "message_id": draft.get("message_id"),
                "draft_id": draft.get("draft_id")
            })

        # Sort: high priority first, then by date
        priority_order = {
            "high": 0,
            "medium": 1,
            "low": 2
        }

        notifications.sort(
            key=lambda n: (
                priority_order.get(
                    n.get("priority", "low"),
                    2
                ),
                n.get("date") or "9999-12-31"
            )
        )

        return notifications

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch notifications: {str(e)}"
        )
