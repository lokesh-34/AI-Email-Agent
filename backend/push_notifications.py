# ============================================================
# PUSH NOTIFICATIONS — FIREBASE CLOUD MESSAGING
# ============================================================
#
# Sends real-time push notifications to mobile phones
# using Firebase Cloud Messaging (FCM).
#
# Notifications are triggered when the email watcher
# processes new emails and creates tasks/drafts/events.
# ============================================================

import os
import logging

from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger(__name__)


# ============================================================
# FIREBASE INITIALIZATION
# ============================================================

_firebase_app = None


def _init_firebase():
    """Initialize Firebase Admin SDK (lazy, once)."""

    global _firebase_app

    if _firebase_app is not None:
        return _firebase_app

    try:
        import firebase_admin
        from firebase_admin import credentials

        service_account_path = os.getenv(
            "FIREBASE_SERVICE_ACCOUNT",
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "firebase-service-account.json"
            )
        )

        if not os.path.exists(service_account_path):
            logger.warning(
                "[FCM] Service account file not found: %s",
                service_account_path
            )
            return None

        cred = credentials.Certificate(service_account_path)

        _firebase_app = firebase_admin.initialize_app(cred)

        logger.info("[FCM] Firebase Admin SDK initialized.")
        return _firebase_app

    except Exception as e:
        logger.error(
            "[FCM] Failed to initialize Firebase: %s",
            str(e)
        )
        return None


# ============================================================
# SEND PUSH NOTIFICATION
# ============================================================

def send_push_notification(user_email, title, body, data=None):
    """
    Send a push notification to all devices registered
    for the given user.

    Parameters:
        user_email: User's email address
        title: Notification title
        body: Notification body text
        data: Optional dict of extra data
    """

    app = _init_firebase()
    if not app:
        logger.warning("[FCM] Firebase not initialized. Skipping push.")
        return

    try:
        from firebase_admin import messaging
        from backend.user_store import get_user_fcm_tokens

        tokens = get_user_fcm_tokens(user_email)

        if not tokens:
            logger.info(
                "[FCM] No FCM tokens for %s. Skipping.",
                user_email
            )
            return

        # Build notification
        notification = messaging.Notification(
            title=title,
            body=body,
        )

        # Build data payload
        payload = data or {}
        payload["click_action"] = os.getenv(
            "FRONTEND_URL",
            "http://localhost:5173"
        )

        # Send to each device token
        success_count = 0
        failed_tokens = []

        for token in tokens:
            try:
                message = messaging.Message(
                    notification=notification,
                    data={
                        k: str(v) for k, v in payload.items()
                    },
                    token=token,
                    webpush=messaging.WebpushConfig(
                        notification=messaging.WebpushNotification(
                            title=title,
                            body=body,
                            icon="/favicon.svg",
                        ),
                        fcm_options=messaging.WebpushFCMOptions(
                            link=os.getenv(
                                "FRONTEND_URL",
                                "http://localhost:5173"
                            )
                        ),
                    ),
                )

                messaging.send(message)
                success_count += 1

            except messaging.UnregisteredError:
                # Token is invalid/expired — remove it
                failed_tokens.append(token)
                logger.info(
                    "[FCM] Removing expired token for %s",
                    user_email
                )

            except Exception as e:
                logger.error(
                    "[FCM] Failed to send to token: %s",
                    str(e)
                )

        # Clean up invalid tokens
        if failed_tokens:
            from backend.user_store import remove_fcm_tokens
            remove_fcm_tokens(user_email, failed_tokens)

        if success_count > 0:
            logger.info(
                "[FCM] Sent %d notification(s) to %s: %s",
                success_count,
                user_email,
                title
            )

    except Exception as e:
        logger.error(
            "[FCM] Push notification error: %s", str(e)
        )


# ============================================================
# NOTIFICATION BUILDERS
# ============================================================

def notify_new_task(user_email, task):
    """Send push notification for a new task."""

    priority = task.get("priority", "medium")
    title = task.get("title", "New Task")

    icon = "🔴" if priority == "high" else (
        "🟡" if priority == "medium" else "🟢"
    )

    send_push_notification(
        user_email=user_email,
        title=f"{icon} {priority.upper()} Priority Task",
        body=title[:100],
        data={
            "type": "task",
            "priority": priority,
            "message_id": task.get("message_id", ""),
        }
    )


def notify_new_draft(user_email, draft):
    """Send push notification for a new AI draft reply."""

    recipient = draft.get("recipient", "unknown")
    subject = draft.get("subject", "")

    send_push_notification(
        user_email=user_email,
        title="📝 AI Draft Reply Ready",
        body=f"To: {recipient}\n{subject[:80]}",
        data={
            "type": "draft",
            "draft_id": draft.get("draft_id", ""),
            "message_id": draft.get("message_id", ""),
        }
    )


def notify_new_event(user_email, event):
    """Send push notification for a new calendar event."""

    title = event.get("title", "New Event")
    event_date = event.get("event_date", "")

    send_push_notification(
        user_email=user_email,
        title="📅 Calendar Event Created",
        body=f"{title}\n{event_date}",
        data={
            "type": "event",
            "event_id": event.get("event_id", ""),
        }
    )
