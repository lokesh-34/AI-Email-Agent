from gmail_reader import connect_gmail, get_inbox_emails
from email_parser import parse_email


service = connect_gmail()

emails = get_inbox_emails(
    service,
    max_results=5
)

for i, email in enumerate(emails, 1):

    print("\n" + "=" * 50)
    print("EMAIL", i)
    print("Subject:", email["subject"])
    print("=" * 50)

    result = parse_email(email)

    print("AI RESULT:")
    print(result)