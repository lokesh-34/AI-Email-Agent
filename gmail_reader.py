from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import os
import base64


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

CREDENTIALS_FILE = os.path.join(
    BASE_DIR,
    "credentials.json"
)

TOKEN_FILE = os.path.join(
    BASE_DIR,
    "token.json"
)


# ============================================================
# GOOGLE SCOPES
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar"
]


# ============================================================
# CONNECT TO GOOGLE
# ============================================================

def connect_gmail(creds=None):

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

    file_creds = None

    if os.path.exists(TOKEN_FILE):

        file_creds = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )


    # --------------------------------------------------------
    # Refresh / OAuth
    # --------------------------------------------------------

    if not file_creds or not file_creds.valid:

        if (
            file_creds
            and file_creds.expired
            and file_creds.refresh_token
        ):

            file_creds.refresh(
                Request()
            )

        else:

            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                SCOPES
            )

            file_creds = flow.run_local_server(
                port=0
            )


        # Save token

        with open(
            TOKEN_FILE,
            "w"
        ) as token:

            token.write(
                file_creds.to_json()
            )


    # --------------------------------------------------------
    # Gmail service
    # --------------------------------------------------------

    service = build(
        "gmail",
        "v1",
        credentials=file_creds
    )

    return service


def get_email(service, message_id):

    message = service.users().messages().get(
        userId="me",
        id=message_id,
        format="full"
    ).execute()

    return message


def get_header(headers, name):

    for header in headers:

        if header["name"].lower() == name.lower():
            return header["value"]

    return ""


def get_email_body(payload):

    mime_type = payload.get("mimeType")

    body = payload.get("body", {})
    data = body.get("data")

    # Plain text email
    if data and mime_type == "text/plain":

        return base64.urlsafe_b64decode(data).decode("utf-8")


    # HTML email
    if data and mime_type == "text/html":

        html = base64.urlsafe_b64decode(data).decode("utf-8")

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        return soup.get_text(
            separator="\n",
            strip=True
        )


    # Multipart email
    parts = payload.get("parts", [])

    for part in parts:

        text = get_email_body(part)

        if text:
            return text


    return ""
def get_inbox_emails(service, max_results=10):

    results = service.users().messages().list(
        userId="me",
        labelIds=["INBOX"],
        maxResults=max_results
    ).execute()

    messages = results.get("messages", [])

    emails = []

    for message in messages:

        email = get_email(
            service,
            message["id"]
        )

        headers = email["payload"]["headers"]

        subject = get_header(
            headers,
            "Subject"
        )

        sender = get_header(
            headers,
            "From"
        )

        date = get_header(
            headers,
            "Date"
        )

        body = get_email_body(
            email["payload"]
        )

        emails.append({
            "message_id": message["id"],
            "sender": sender,
            "subject": subject,
            "body": body,
            "date": date
        })

    return emails


def get_email_for_agent(service, message_id):

    email = get_email(
        service,
        message_id
    )

    headers = email["payload"]["headers"]

    subject = get_header(
        headers,
        "Subject"
    )

    sender = get_header(
        headers,
        "From"
    )

    date = get_header(
        headers,
        "Date"
    )

    body = get_email_body(
        email["payload"]
    )

    return {
        "message_id": message_id,
        "sender": sender,
        "subject": subject,
        "body": body,
        "date": date
    }


def get_latest_email(service):

    results = service.users().messages().list(
        userId="me",
        labelIds=["INBOX"],
        maxResults=1
    ).execute()

    messages = results.get("messages", [])

    if not messages:
        return None

    message_id = messages[0]["id"]

    email = get_email(
        service,
        message_id
    )

    headers = email["payload"]["headers"]

    subject = get_header(
        headers,
        "Subject"
    )

    sender = get_header(
        headers,
        "From"
    )

    date = get_header(
        headers,
        "Date"
    )

    body = get_email_body(
        email["payload"]
    )

    return {
        "message_id": message_id,
        "sender": sender,
        "subject": subject,
        "body": body,
        "date": date
    }


if __name__ == "__main__":

    service = connect_gmail()

    email = get_latest_email(service)

    if email:

        print("\nSUBJECT:", email["subject"])
        print("FROM:", email["sender"])
        print("\nBODY:")
        print(email["body"])

    else:

        print("No emails found.")