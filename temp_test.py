from gmail_reader import connect_gmail, get_inbox_emails
from email_parser import parse_email


service = connect_gmail()

emails = get_inbox_emails(
    service,
    max_results=10
)

for email in emails:

    if "Codeforces" in email["sender"]:

        result = parse_email(email)

        print("\nAI RESULT:")
        print(result)

        print(
            "\nEVENT TIMEZONE:",
            result.get("event_timezone")
        )

        break