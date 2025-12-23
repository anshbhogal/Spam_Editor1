import base64
from googleapiclient.discovery import build
from gmail.auth import gmail_auth

def get_gmail_service():
    creds = gmail_auth()
    return build("gmail", "v1", credentials=creds)

def extract_text(payload):
    parts = payload.get("parts", [])
    for part in parts:
        if part["mimeType"] == "text/plain":
            data = part["body"]["data"]
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    return ""

def fetch_email(msg_id):
    service = get_gmail_service()
    msg = service.users().messages().get(
        userId="me", id=msg_id, format="full"
    ).execute()

    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    body = extract_text(msg["payload"])

    return {
        "id": msg_id,
        "subject": headers.get("Subject", ""),
        "from": headers.get("From", ""),
        "text": body,
    }
