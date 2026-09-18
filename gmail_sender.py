# ============================================================
# GMAIL SENDER
# ============================================================
#
# Sends emails via the Gmail API.
# Supports replying to existing email threads using
# In-Reply-To and References headers.
#
# SAFETY:
# This module only sends when explicitly called.
# The caller (API endpoint) must ensure user approval
# before invoking send_email().
# ============================================================

import os
import base64
import logging

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


# ============================================================
# CONFIGURATION
# ============================================================

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

TOKEN_FILE = os.path.join(
    BASE_DIR,
    "token.json"
)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar"
]


# ============================================================
# CONNECT TO GMAIL (SEND)
# ============================================================

def connect_gmail_sender(creds=None):

    # --------------------------------------------------------
    # Per-user credentials (from MongoDB)
    # --------------------------------------------------------

    if creds is not None:

        service = build(
            "gmail",
            "v1",
            credentials=creds
        )

        return service

    # --------------------------------------------------------
    # File-based credentials (CLI / legacy)
    # --------------------------------------------------------

    if not os.path.exists(TOKEN_FILE):
        raise FileNotFoundError(
            "token.json not found. "
            "Run Gmail OAuth first."
        )

    file_creds = Credentials.from_authorized_user_file(
        TOKEN_FILE,
        SCOPES
    )

    if not file_creds or not file_creds.valid:

        if (
            file_creds
            and file_creds.expired
            and file_creds.refresh_token
        ):
            file_creds.refresh(Request())

            with open(TOKEN_FILE, "w") as token:
                token.write(file_creds.to_json())
        else:
            raise RuntimeError(
                "Gmail credentials are not valid. "
                "Re-run OAuth with send scope."
            )

    service = build(
        "gmail",
        "v1",
        credentials=file_creds
    )

    return service


# ============================================================
# SEND EMAIL
# ============================================================

def send_email(
    recipient,
    subject,
    body,
    reply_to_message_id=None,
    creds=None
):
    """
    Send an email via Gmail API.

    Parameters:
        recipient:
            The email address to send to.

        subject:
            The email subject line.

        body:
            The email body text.

        reply_to_message_id:
            Optional. The Gmail message ID of the email
            being replied to. When provided, the sent email
            will be threaded with the original.

    Returns:
        dict with:
            success: bool
            gmail_message_id: str or None
            error: str or None
    """

    try:

        service = connect_gmail_sender(creds=creds)

        # ----------------------------------------------------
        # Build MIME message
        # ----------------------------------------------------

        message = MIMEMultipart()
        message["to"] = recipient
        message["subject"] = subject

        # ----------------------------------------------------
        # Reply headers for threading
        # ----------------------------------------------------

        if reply_to_message_id:

            try:
                # Get the original message to extract
                # the Message-ID header for threading
                original = service.users().messages().get(
                    userId="me",
                    id=reply_to_message_id,
                    format="metadata",
                    metadataHeaders=[
                        "Message-ID",
                        "References"
                    ]
                ).execute()

                headers = original.get(
                    "payload", {}
                ).get(
                    "headers", []
                )

                original_message_id_header = None
                original_references = None

                for header in headers:
                    name = header.get("name", "").lower()
                    if name == "message-id":
                        original_message_id_header = (
                            header.get("value")
                        )
                    elif name == "references":
                        original_references = (
                            header.get("value")
                        )

                if original_message_id_header:
                    message["In-Reply-To"] = (
                        original_message_id_header
                    )

                    if original_references:
                        message["References"] = (
                            f"{original_references} "
                            f"{original_message_id_header}"
                        )
                    else:
                        message["References"] = (
                            original_message_id_header
                        )

            except Exception as e:
                logger.warning(
                    "Could not fetch original message "
                    "headers for threading: %s",
                    str(e)
                )

        # ----------------------------------------------------
        # Attach body
        # ----------------------------------------------------

        message.attach(
            MIMEText(body, "plain")
        )

        # ----------------------------------------------------
        # Encode message
        # ----------------------------------------------------

        raw_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode("utf-8")

        # ----------------------------------------------------
        # Build send body
        # ----------------------------------------------------

        send_body = {
            "raw": raw_message
        }

        # Thread with original message
        if reply_to_message_id:
            try:
                original_msg = service.users().messages().get(
                    userId="me",
                    id=reply_to_message_id,
                    format="minimal"
                ).execute()

                thread_id = original_msg.get("threadId")

                if thread_id:
                    send_body["threadId"] = thread_id

            except Exception as e:
                logger.warning(
                    "Could not get thread ID: %s",
                    str(e)
                )

        # ----------------------------------------------------
        # Send
        # ----------------------------------------------------

        sent_message = service.users().messages().send(
            userId="me",
            body=send_body
        ).execute()

        gmail_message_id = sent_message.get("id")

        logger.info(
            "Email sent successfully. "
            "Gmail ID: %s, To: %s, Subject: %s",
            gmail_message_id,
            recipient,
            subject
        )

        return {
            "success": True,
            "gmail_message_id": gmail_message_id,
            "error": None
        }

    except Exception as e:

        logger.error(
            "Failed to send email to %s: %s",
            recipient,
            str(e)
        )

        return {
            "success": False,
            "gmail_message_id": None,
            "error": str(e)
        }
