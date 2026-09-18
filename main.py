import logging

from gmail_reader import connect_gmail, get_inbox_emails
from email_parser import parse_email
from task_manager import create_task

from database import (
    save_task,
    task_exists,
    get_task_by_message_id,
    update_calendar_event_id,
    save_draft,
    draft_exists_for_message,
    create_draft_from_ai,
    ensure_indexes
)

from google_calendar import create_event_from_parsed_email


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# PROCESS EMAILS
# ============================================================

def process_emails(max_results=10, creds=None):
    """
    Main email processing pipeline.

    Fetches Gmail emails, parses them with AI,
    creates tasks, calendar events, and reply drafts.

    Returns a summary of what was processed.
    """

    logger.info("Starting email processing pipeline...")

    ensure_indexes()

    service = connect_gmail(creds=creds)

    emails = get_inbox_emails(
        service,
        max_results=max_results
    )

    if not emails:
        logger.info("No emails found.")
        return {
            "processed": 0,
            "tasks_created": 0,
            "events_created": 0,
            "drafts_created": 0,
            "errors": 0
        }

    stats = {
        "processed": 0,
        "tasks_created": 0,
        "events_created": 0,
        "drafts_created": 0,
        "errors": 0
    }

    for email in emails:

        try:

            stats["processed"] += 1

            logger.info(
                "Processing email: %s (from: %s)",
                email["subject"],
                email["sender"]
            )

            # ------------------------------------------------
            # PARSE EMAIL WITH AI
            # ------------------------------------------------

            result = parse_email(email)

            logger.info(
                "AI Analysis: category=%s, "
                "action_required=%s, "
                "event_required=%s, "
                "reply_required=%s",
                result.get("category"),
                result.get("action_required"),
                result.get("event_required"),
                result.get("reply_required")
            )

            # ------------------------------------------------
            # SKIP NON-ACTIONABLE EMAILS
            # ------------------------------------------------

            if (
                not result.get("action_required")
                and not result.get("event_required", False)
                and not result.get("reply_required", False)
            ):
                logger.info(
                    "No action, event, or reply required. "
                    "Skipping."
                )
                continue

            message_id = email["message_id"]

            # ------------------------------------------------
            # CHECK EXISTING TASK
            # ------------------------------------------------

            existing_task = get_task_by_message_id(
                message_id
            )

            if existing_task:

                logger.info(
                    "Task already exists for message %s",
                    message_id
                )

                # ----------------------------------------
                # Handle missing calendar event
                # ----------------------------------------

                calendar_event_id = existing_task.get(
                    "calendar_event_id"
                )

                event_required = existing_task.get(
                    "event_required",
                    False
                )

                if calendar_event_id:
                    logger.info(
                        "Calendar event already exists: %s",
                        calendar_event_id
                    )

                elif event_required:
                    _create_calendar_event(
                        result,
                        message_id,
                        stats,
                        creds=creds
                    )

                # ----------------------------------------
                # Handle missing draft
                # ----------------------------------------

                if (
                    result.get("reply_required")
                    and not draft_exists_for_message(
                        message_id
                    )
                ):
                    _create_reply_draft(
                        result,
                        message_id,
                        stats
                    )

                continue

            # ------------------------------------------------
            # CREATE NEW TASK
            # ------------------------------------------------

            task = create_task(
                result,
                email
            )

            save_task(task)
            stats["tasks_created"] += 1

            logger.info(
                "Task created: %s (priority: %s)",
                task["title"],
                task["priority"]
            )

            # ------------------------------------------------
            # CALENDAR EVENT
            # ------------------------------------------------

            if result.get("event_required"):
                _create_calendar_event(
                    result,
                    message_id,
                    stats,
                    creds=creds
                )

            # ------------------------------------------------
            # REPLY DRAFT
            # ------------------------------------------------

            if result.get("reply_required"):
                _create_reply_draft(
                    result,
                    message_id,
                    stats
                )

            logger.info(
                "Finished processing email: %s",
                email["subject"]
            )

        except Exception as e:

            stats["errors"] += 1

            logger.error(
                "Error processing email '%s': %s",
                email.get("subject", "unknown"),
                str(e),
                exc_info=True
            )

    logger.info(
        "Pipeline complete. "
        "Processed: %d, Tasks: %d, Events: %d, "
        "Drafts: %d, Errors: %d",
        stats["processed"],
        stats["tasks_created"],
        stats["events_created"],
        stats["drafts_created"],
        stats["errors"]
    )

    return stats


# ============================================================
# HELPER: CREATE CALENDAR EVENT
# ============================================================

def _create_calendar_event(result, message_id, stats, creds=None):
    """Create a Google Calendar event and update MongoDB."""

    try:

        calendar_result = create_event_from_parsed_email(
            result,
            creds=creds
        )

        if calendar_result["created"]:

            event = calendar_result["event"]
            event_id = event["event_id"]

            updated = update_calendar_event_id(
                message_id,
                event_id
            )

            if updated:
                stats["events_created"] += 1
                logger.info(
                    "Calendar event created: %s (%s)",
                    event["title"],
                    event_id
                )
            else:
                logger.warning(
                    "Calendar event created but "
                    "MongoDB update failed."
                )

        else:
            logger.info(
                "Calendar event not created: %s",
                calendar_result["reason"]
            )

    except Exception as e:

        logger.error(
            "Calendar creation error: %s",
            str(e)
        )


# ============================================================
# HELPER: CREATE REPLY DRAFT
# ============================================================

def _create_reply_draft(result, message_id, stats):
    """Create an email reply draft and save to MongoDB."""

    try:

        if draft_exists_for_message(message_id):
            logger.info(
                "Draft already exists for message %s",
                message_id
            )
            return

        if not result.get("reply_draft"):
            logger.info(
                "No reply draft content from AI."
            )
            return

        draft = create_draft_from_ai(
            message_id,
            result
        )

        save_draft(draft)
        stats["drafts_created"] += 1

        logger.info(
            "Reply draft created: %s (to: %s)",
            draft["draft_id"],
            draft["recipient"]
        )

    except Exception as e:

        logger.error(
            "Draft creation error: %s",
            str(e)
        )


# ============================================================
# MAIN
# ============================================================

def main():
    process_emails(max_results=10)


if __name__ == "__main__":
    main()