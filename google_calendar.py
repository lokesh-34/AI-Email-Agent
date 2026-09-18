# ============================================================
# GOOGLE CALENDAR
# ============================================================

import os

from datetime import (
    datetime,
    timedelta,
    timezone
)

from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

TOKEN_FILE = os.path.join(
    BASE_DIR,
    "token.json"
)


# ============================================================
# SCOPES
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar"
]


# ============================================================
# DEFAULT TIMEZONE
# ============================================================

LOCAL_TIMEZONE = ZoneInfo(
    "Asia/Kolkata"
)


# ============================================================
# TIMEZONE CONVERSION
# ============================================================

def get_timezone(timezone_name):

    if not timezone_name:

        # No timezone explicitly mentioned.
        # Our system assumes India because the
        # Calendar is configured for Asia/Kolkata.

        return LOCAL_TIMEZONE


    timezone_name = timezone_name.strip()


    # --------------------------------------------------------
    # Common timezone aliases
    # --------------------------------------------------------

    timezone_map = {

        "IST": "Asia/Kolkata",

        "UTC": "UTC",

        "GMT": "GMT",

        "EST": "America/New_York",

        "EDT": "America/New_York",

        "CST": "America/Chicago",

        "CDT": "America/Chicago",

        "MST": "America/Denver",

        "MDT": "America/Denver",

        "PST": "America/Los_Angeles",

        "PDT": "America/Los_Angeles"
    }


    mapped_timezone = timezone_map.get(
        timezone_name.upper()
    )


    if mapped_timezone:

        return ZoneInfo(
            mapped_timezone
        )


    # --------------------------------------------------------
    # Try IANA timezone directly
    # --------------------------------------------------------

    try:

        return ZoneInfo(
            timezone_name
        )

    except Exception:

        # Unknown timezone.
        # Safely fall back to India.

        print(
            f"Warning: Unknown timezone "
            f"'{timezone_name}'. "
            f"Using Asia/Kolkata."
        )

        return LOCAL_TIMEZONE


# ============================================================
# CONNECT TO GOOGLE CALENDAR
# ============================================================

def connect_calendar(creds=None):

    # --------------------------------------------------------
    # Per-user credentials (from MongoDB)
    # --------------------------------------------------------

    if creds is not None:

        service = build(
            "calendar",
            "v3",
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


    if not file_creds.valid:

        raise RuntimeError(
            "Google credentials are not valid. "
            "Run OAuth again."
        )


    service = build(
        "calendar",
        "v3",
        credentials=file_creds
    )


    return service


# ============================================================
# CREATE EVENT FROM PARSED EMAIL
# ============================================================

def create_event_from_parsed_email(
    parsed_email,
    creds=None
):

    # --------------------------------------------------------
    # Check whether an event is required
    # --------------------------------------------------------

    if not parsed_email.get(
        "event_required",
        False
    ):

        return {
            "created": False,
            "reason": "No calendar event required"
        }


    # --------------------------------------------------------
    # Extract event information
    # --------------------------------------------------------

    event_title = parsed_email.get(
        "event_title"
    )

    event_date = parsed_email.get(
        "event_date"
    )

    start_time = parsed_email.get(
        "event_start_time"
    )

    end_time = parsed_email.get(
        "event_end_time"
    )

    event_timezone = parsed_email.get(
        "event_timezone"
    )

    location = parsed_email.get(
        "event_location"
    ) or ""

    description = parsed_email.get(
        "event_description"
    ) or ""


    # --------------------------------------------------------
    # Validate required information
    # --------------------------------------------------------

    if not event_date:

        return {
            "created": False,
            "reason": "Event date is missing"
        }


    if not start_time:

        return {
            "created": False,
            "reason": "Event start time is missing"
        }


    # --------------------------------------------------------
    # Determine source timezone
    # --------------------------------------------------------

    source_timezone = get_timezone(
        event_timezone
    )


    # --------------------------------------------------------
    # Parse start time
    # --------------------------------------------------------

    try:

        start_datetime = datetime.strptime(

            f"{event_date} {start_time}",

            "%Y-%m-%d %H:%M"

        )

    except ValueError:

        return {
            "created": False,
            "reason": "Invalid event date or start time"
        }


    # --------------------------------------------------------
    # Attach source timezone
    # --------------------------------------------------------

    start_datetime = start_datetime.replace(
        tzinfo=source_timezone
    )


    # --------------------------------------------------------
    # Parse end time
    # --------------------------------------------------------

    if end_time:

        try:

            end_datetime = datetime.strptime(

                f"{event_date} {end_time}",

                "%Y-%m-%d %H:%M"

            )

        except ValueError:

            return {
                "created": False,
                "reason": "Invalid event end time"
            }


        end_datetime = end_datetime.replace(
            tzinfo=source_timezone
        )


    else:

        # ----------------------------------------------------
        # No end time → default 1 hour
        # ----------------------------------------------------

        end_datetime = (
            start_datetime
            + timedelta(hours=1)
        )


    # --------------------------------------------------------
    # Handle events crossing midnight
    # --------------------------------------------------------

    if end_datetime <= start_datetime:

        end_datetime = (
            end_datetime
            + timedelta(days=1)
        )


    # ========================================================
    # PAST EVENT CHECK
    # ========================================================

    now_utc = datetime.now(
        timezone.utc
    )


    start_utc = start_datetime.astimezone(
        timezone.utc
    )


    if start_utc <= now_utc:

        return {
            "created": False,
            "reason": "Event is already in the past"
        }


    # ========================================================
    # CONVERT TO LOCAL TIMEZONE
    # ========================================================

    start_local = start_datetime.astimezone(
        LOCAL_TIMEZONE
    )

    end_local = end_datetime.astimezone(
        LOCAL_TIMEZONE
    )


    # --------------------------------------------------------
    # Convert to ISO format
    # --------------------------------------------------------

    start_iso = start_local.isoformat()

    end_iso = end_local.isoformat()


    print(
        "\nTimezone conversion:"
    )

    print(
        "Original:",
        start_datetime.isoformat()
    )

    print(
        "India:",
        start_iso
    )


    # ========================================================
    # CREATE GOOGLE CALENDAR EVENT
    # ========================================================

    result = create_calendar_event(

        title=event_title,

        start_datetime=start_iso,

        end_datetime=end_iso,

        description=description,

        location=location,

        creds=creds
    )


    return {

        "created": True,

        "reason": "Calendar event created",

        "event": result
    }


# ============================================================
# CREATE CALENDAR EVENT
# ============================================================

def create_calendar_event(

    title,

    start_datetime,

    end_datetime,

    description="",

    location="",

    creds=None
):

    service = connect_calendar(creds=creds)


    event = {

        "summary": title,

        "description": description,

        "location": location,

        "start": {

            "dateTime": start_datetime,

            "timeZone": "Asia/Kolkata"
        },

        "end": {

            "dateTime": end_datetime,

            "timeZone": "Asia/Kolkata"
        }
    }


    created_event = service.events().insert(

        calendarId="primary",

        body=event

    ).execute()


    return {

        "event_id": created_event.get(
            "id"
        ),

        "title": created_event.get(
            "summary"
        ),

        "start": created_event.get(
            "start",
            {}
        ).get(
            "dateTime"
        ),

        "end": created_event.get(
            "end",
            {}
        ).get(
            "dateTime"
        ),

        "html_link": created_event.get(
            "htmlLink"
        )
    }


# ============================================================
# GET UPCOMING CALENDAR EVENTS
# ============================================================

def get_upcoming_calendar_events(
    max_results=10,
    creds=None
):

    service = connect_calendar(creds=creds)


    now = datetime.now(
        timezone.utc
    ).isoformat()


    events_result = service.events().list(

        calendarId="primary",

        timeMin=now,

        maxResults=max_results,

        singleEvents=True,

        orderBy="startTime"

    ).execute()


    events = events_result.get(
        "items",
        []
    )


    results = []


    for event in events:

        start = event.get(
            "start",
            {}
        )


        results.append({

            "event_id": event.get(
                "id"
            ),

            "title": event.get(
                "summary",
                ""
            ),

            "start": (

                start.get(
                    "dateTime"
                )

                or

                start.get(
                    "date"
                )
            ),

            "description": event.get(
                "description",
                ""
            ),

            "location": event.get(
                "location",
                ""
            ),

            "html_link": event.get(
                "htmlLink"
            )
        })


    return results


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\n========== GOOGLE CALENDAR TEST =========="
    )


    events = get_upcoming_calendar_events(
        max_results=10
    )


    if not events:

        print(
            "No upcoming calendar events found."
        )

    else:

        for event in events:

            print(
                "\nTitle:",
                event["title"]
            )

            print(
                "Start:",
                event["start"]
            )

            print(
                "Location:",
                event["location"]
            )