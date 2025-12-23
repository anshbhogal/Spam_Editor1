import time
from gmail.fetcher import get_gmail_service, fetch_email
from gmail.actions import mark_important, mark_spam
from ml.predict import predict_email

CHECK_INTERVAL = 60  # seconds

def listen():
    service = get_gmail_service()
    print("📡 Listening for new emails...")

    while True:
        results = service.users().messages().list(
            userId="me",
            q="is:unread"
        ).execute()

        messages = results.get("messages", [])

        for msg in messages:
            email = fetch_email(msg["id"])
            text = f"{email['subject']} {email['text']}"

            result = predict_email(text)

            if result["label"] == "IMPORTANT":
                mark_important(msg["id"])
                print(f"⭐ IMPORTANT: {email['subject']}")
            else:
                mark_spam(msg["id"])
                print(f"🗑️ SPAM: {email['subject']}")

        time.sleep(CHECK_INTERVAL)
