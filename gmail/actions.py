from googleapiclient.discovery import build
from gmail.auth import gmail_auth

def mark_important(msg_id):
    service = build("gmail", "v1", credentials=gmail_auth())
    service.users().messages().modify(
        userId="me",
        id=msg_id,
        body={
            "addLabelIds": ["STARRED", "IMPORTANT"],
            "removeLabelIds": ["SPAM"]
        }
    ).execute()

def mark_spam(msg_id):
    service = build("gmail", "v1", credentials=gmail_auth())
    service.users().messages().modify(
        userId="me",
        id=msg_id,
        body={"addLabelIds": ["SPAM"]}
    ).execute()
