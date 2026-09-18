import json
import logging

from groq import Groq
from dotenv import load_dotenv
import os


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

logger = logging.getLogger(__name__)


# ============================================================
# EMAIL PARSER
# ============================================================

def parse_email(email):

    prompt = f"""
Analyze the following email and extract structured information.

Return a JSON object with exactly these fields:

- category:
  Classify the email into the most appropriate category.

  Examples:
  assignment, exam, job, placement, interview, meeting, invoice,
  payment, banking, delivery, subscription, account,
  event, announcement, personal, security, notification,
  marketing, newsletter, customer_support, general

- action:
  Describe what the recipient needs to do, if anything.
  If no action is required, return null.

- action_required:
  true if the recipient needs to take an action,
  otherwise false.

- deadline:
  The date/time by which the action should be completed,
  if explicitly mentioned.
  Otherwise return null.
  Format: YYYY-MM-DD

- priority:
  low, medium, or high.

- title:
  A short descriptive title for the email.

- event_required:
  true if this email contains a real scheduled event,
  meeting, interview, appointment, class, exam,
  webinar, conference, scheduled call, contest,
  or similar activity that should potentially
  appear on the user's calendar.

  Otherwise false.

- event_title:
  The title of the calendar event.
  If event_required is false, return null.

- event_date:
  The date of the event in YYYY-MM-DD format.
  If event_required is false or no event date is available,
  return null.

- event_start_time:
  The starting time in HH:MM 24-hour format.
  If unavailable, return null.

- event_end_time:
  The ending time in HH:MM 24-hour format.
  If unavailable, return null.

- event_timezone:
  The timezone explicitly associated with the event time.

  Examples:
  UTC
  GMT
  IST
  EST
  PST
  Asia/Kolkata
  America/New_York

  If the email explicitly specifies a timezone,
  extract it.

  If the email does not specify a timezone,
  return null.

- event_location:
  The physical or online location of the event.
  If unavailable, return null.

- event_description:
  A short useful description for the calendar event.
  If event_required is false, return null.

- reply_required:
  true ONLY if this email genuinely needs a reply
  from the recipient.

  Emails that typically require a reply:
  - Recruiter emails requesting confirmation
  - Interview invitations
  - Meeting invitations requesting RSVP
  - Professor emails asking a question
  - Customer support conversations
  - Personal emails asking a question
  - Job applications requesting a response
  - Emails explicitly requesting confirmation

  Emails that typically do NOT require a reply:
  - Marketing emails
  - Newsletters
  - Delivery notifications
  - Invoice/billing notifications
  - Security alerts
  - Account notifications
  - Announcements (unless response is explicitly requested)
  - Automated notifications
  - Subscription confirmations
  - Banking alerts

  Do NOT generate a reply just because action_required is true.
  Only set reply_required to true when the sender actually
  expects a written response.

- reply_type:
  The type of reply needed. Choose the most appropriate:
  interview_confirmation, meeting_acceptance, meeting_decline,
  meeting_reschedule, job_response, professor_response,
  customer_support_response, general_response,
  clarification_request, or another appropriate type.
  If reply_required is false, return null.

- reply_recipient:
  The email address to reply to.
  Extract from the From header.
  If reply_required is false, return null.

- reply_subject:
  The subject line for the reply.
  Usually "Re: <original subject>".
  If reply_required is false, return null.

- reply_draft:
  A professional, well-written reply draft.
  The reply should be appropriate for the context.
  Use a professional but friendly tone.
  Do NOT use placeholder names.
  Sign off with "Best regards" or similar.
  If reply_required is false, return null.

- ai_explanation:
  A short one-sentence explanation of why a reply is or
  is not needed, written for the user to understand.
  Example: "Reply appears necessary because the sender
  requested confirmation of interview availability."


IMPORTANT RULES:

1. Understand the actual meaning of the email,
   not just keywords.

2. Do not invent information.

3. Only set event_required to true when the email
   actually describes a scheduled event.

4. A historical mention of an event does NOT mean
   event_required is true.

5. A promotional email mentioning an event should
   normally NOT create a calendar event unless the
   recipient is clearly expected to attend.

6. If the email contains an interview, meeting,
   appointment, class, exam, webinar, conference,
   scheduled call, contest, or similar event,
   event_required should normally be true.

7. If a date is available but the time is not,
   event_start_time should be null.

8. If an end time is not explicitly available,
   event_end_time should be null.

9. If the email explicitly specifies UTC, GMT, IST,
   EST, PST, or another timezone, preserve that timezone.

10. Never assume IST when another timezone is explicitly
    stated.

11. If no timezone is mentioned, event_timezone must be null.

12. Never guess a date or time.

13. Never invent recipients, names, or meeting links.

14. If information is missing, return null.

15. Return valid JSON only.


EMAIL:

Subject:
{email["subject"]}

From:
{email["sender"]}

Body:
{email["body"]}
"""


    # ========================================================
    # GROQ REQUEST
    # ========================================================

    response = client.chat.completions.create(

        model="openai/gpt-oss-120b",

        messages=[

            {
                "role": "user",
                "content": prompt
            }

        ],

        response_format={
            "type": "json_object"
        }
    )


    # ========================================================
    # PARSE JSON
    # ========================================================

    result = response.choices[0].message.content

    data = json.loads(result)

    logger.info(
        "Email parsed: %s | category=%s | reply_required=%s",
        email.get("subject", ""),
        data.get("category"),
        data.get("reply_required")
    )

    return data