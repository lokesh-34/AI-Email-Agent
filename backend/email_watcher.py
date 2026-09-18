# ============================================================
# EMAIL WATCHER — AUTOMATIC EMAIL PROCESSING
# ============================================================
#
# Background service that automatically polls Gmail for new
# emails and processes them through the AI pipeline.
#
# Runs as an asyncio background task inside FastAPI.
# Polls every POLL_INTERVAL seconds for all registered users.
# ============================================================

import os
import asyncio
import logging

from datetime import datetime

logger = logging.getLogger(__name__)

# Poll interval in seconds (default: 60 seconds)
POLL_INTERVAL = int(os.getenv("EMAIL_POLL_INTERVAL", "60"))


# ============================================================
# WATCHER STATE
# ============================================================

_watcher_running = False
_watcher_task = None


# ============================================================
# GET ALL REGISTERED USERS
# ============================================================

def _get_all_user_emails():
    """Get all registered user emails from MongoDB."""
    try:
        from backend.user_store import users_collection
        users = users_collection.find(
            {"access_token": {"$exists": True}},
            {"email": 1}
        )
        return [u["email"] for u in users]
    except Exception as e:
        logger.error("Failed to get user list: %s", str(e))
        return []


# ============================================================
# PROCESS NEW EMAILS FOR ONE USER
# ============================================================

def _process_user_emails(user_email):
    """
    Process new emails for a single user.

    Fetches the latest 5 emails and processes them.
    The pipeline's built-in deduplication (task_exists)
    ensures already-processed emails are skipped.
    """

    try:
        from backend.user_store import get_user_google_creds
        from main import process_emails

        creds = get_user_google_creds(user_email)

        result = process_emails(
            max_results=5,
            creds=creds
        )

        new_tasks = result.get("tasks_created", 0)
        new_events = result.get("events_created", 0)
        new_drafts = result.get("drafts_created", 0)

        if new_tasks or new_events or new_drafts:
            logger.info(
                "[Watcher] New items for %s: "
                "%d tasks, %d events, %d drafts",
                user_email,
                new_tasks,
                new_events,
                new_drafts
            )

            # Send push notifications
            _send_push_summary(
                user_email,
                new_tasks,
                new_events,
                new_drafts
            )

        return result

    except ValueError as e:
        logger.warning(
            "[Watcher] Credentials issue for %s: %s",
            user_email, str(e)
        )
    except Exception as e:
        logger.error(
            "[Watcher] Error processing emails for %s: %s",
            user_email, str(e)
        )

    return None


# ============================================================
# BACKGROUND POLLING LOOP
# ============================================================

async def _poll_loop():
    """
    Async background loop that polls Gmail for all users.

    Runs every POLL_INTERVAL seconds. Each cycle:
    1. Gets all registered users from MongoDB
    2. Fetches their latest emails
    3. Processes any new ones through the AI pipeline
    """

    global _watcher_running

    logger.info(
        "[Watcher] Email watcher started "
        "(polling every %ds)",
        POLL_INTERVAL
    )

    while _watcher_running:

        try:
            user_emails = _get_all_user_emails()

            if user_emails:
                logger.info(
                    "[Watcher] Checking emails for %d user(s)...",
                    len(user_emails)
                )

                for email in user_emails:
                    # Run sync processing in a thread
                    # to avoid blocking the event loop
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        _process_user_emails,
                        email
                    )

        except Exception as e:
            logger.error(
                "[Watcher] Poll cycle error: %s", str(e)
            )

        # Wait for next poll cycle
        await asyncio.sleep(POLL_INTERVAL)

    logger.info("[Watcher] Email watcher stopped.")


# ============================================================
# START / STOP
# ============================================================

async def start_watcher():
    """Start the background email watcher."""

    global _watcher_running, _watcher_task

    if _watcher_running:
        logger.info("[Watcher] Already running.")
        return

    _watcher_running = True
    _watcher_task = asyncio.create_task(_poll_loop())

    logger.info("[Watcher] Email watcher task created.")


async def stop_watcher():
    """Stop the background email watcher."""

    global _watcher_running, _watcher_task

    _watcher_running = False

    if _watcher_task:
        _watcher_task.cancel()

        try:
            await _watcher_task
        except asyncio.CancelledError:
            pass

        _watcher_task = None

    logger.info("[Watcher] Email watcher stopped.")


def is_watcher_running():
    """Check if the watcher is currently running."""
    return _watcher_running


# ============================================================
# PUSH NOTIFICATION HELPER
# ============================================================

def _send_push_summary(user_email, tasks, events, drafts):
    """Send a push notification summarizing new items."""

    try:
        from backend.push_notifications import (
            send_push_notification
        )

        parts = []
        if tasks:
            parts.append(
                f"{tasks} task{'s' if tasks > 1 else ''}"
            )
        if events:
            parts.append(
                f"{events} event{'s' if events > 1 else ''}"
            )
        if drafts:
            parts.append(
                f"{drafts} draft{'s' if drafts > 1 else ''}"
            )

        body = "New: " + ", ".join(parts)

        send_push_notification(
            user_email=user_email,
            title="📬 New Email Activity",
            body=body,
            data={
                "type": "watcher_summary",
                "tasks": str(tasks),
                "events": str(events),
                "drafts": str(drafts),
            }
        )

    except Exception as e:
        logger.error(
            "[Watcher] Push notification error: %s",
            str(e)
        )
