import pandas as pd
from imap_tools import MailBox, AND
from bs4 import BeautifulSoup
import re
import time
import os
import sys
import ssl
from dotenv import load_dotenv

# ===================== LOAD ENV =====================
load_dotenv()

EMAIL_USER = os.getenv("GMAIL_USER")
EMAIL_PASS = os.getenv("GMAIL_APP_PASS")

if not EMAIL_USER or not EMAIL_PASS:
    raise RuntimeError("❌ Missing Gmail credentials. Check .env file.")

# ===================== CONFIG =====================
IMAP_SERVER = "imap.gmail.com"
FILENAME = "full_email_dataset.csv"
PROCESSED_UIDS_FILE = "processed_uids.txt"

BATCH_SIZE = 50
FETCH_DELAY = 0.1

# ===================== UTILITIES =====================
def clean_text(html):
    if not html:
        return ""
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(separator=" ")
    return re.sub(r"\s+", " ", text).strip()

def load_processed_uids():
    if not os.path.exists(PROCESSED_UIDS_FILE):
        return set()
    with open(PROCESSED_UIDS_FILE, "r") as f:
        return set(f.read().splitlines())

def save_processed_uid(uid):
    with open(PROCESSED_UIDS_FILE, "a") as f:
        f.write(str(uid) + "\n")

def save_batch(batch):
    if not batch:
        return
    df = pd.DataFrame(batch)
    write_header = not os.path.exists(FILENAME)
    df.to_csv(FILENAME, mode="a", index=False, header=write_header)

def get_row_count():
    if not os.path.exists(FILENAME):
        return 0
    with open(FILENAME, "r", encoding="utf-8") as f:
        return max(sum(1 for _ in f) - 1, 0)

# ===================== CORE FETCH =====================
def fetch_category(category, label):
    print(f"\n📂 CATEGORY: {category.upper()}")
    print(f"📊 Existing rows: {get_row_count()}")

    processed_uids = load_processed_uids()
    gmail_query = f'X-GM-RAW "category:{category}"'

    while True:
        try:
            print("🔌 Connecting to Gmail...")
            with MailBox(IMAP_SERVER).login(EMAIL_USER, EMAIL_PASS) as mailbox:
                mailbox.folder.set("INBOX")

                uids = list(mailbox.uids(criteria=gmail_query))
                uids.reverse()

                print(f"📨 Emails found: {len(uids)}")

                batch = []
                processed = 0

                for uid in uids:
                    if str(uid) in processed_uids:
                        continue

                    try:
                        try:
                            msg = next(mailbox.fetch(criteria=AND(uid=uid)))
                        except StopIteration:
                            save_processed_uid(uid)
                            continue

                        body = msg.text or msg.html or ""
                        clean_body = clean_text(body)

                        if len(clean_body) < 30:
                            save_processed_uid(uid)
                            continue

                        full_text = f"{msg.subject or ''} {clean_body}"

                        batch.append({
                            "text": full_text,
                            "label": label,
                            "category": category,
                            "from": msg.from_,
                            "date": msg.date.strftime("%Y-%m-%d") if msg.date else ""
                        })

                        save_processed_uid(uid)
                        processed += 1
                        time.sleep(FETCH_DELAY)

                        if len(batch) >= BATCH_SIZE:
                            save_batch(batch)
                            batch.clear()
                            sys.stdout.write(f"\r💾 Saved {processed} emails...")
                            sys.stdout.flush()

                    except Exception as e:
                        if "ssl" in str(e).lower() or "socket" in str(e).lower():
                            raise e
                        print(f"\n⚠️ Skipped UID {uid}: {repr(e)}")

                if batch:
                    save_batch(batch)

                print(f"\n✅ Finished {category}")
                return

        except (TimeoutError, ssl.SSLError, ssl.SSLEOFError) as e:
            print(f"\n🔴 Connection dropped: {e}")
            print("⏳ Reconnecting in 10 seconds...")
            time.sleep(10)

        except Exception as e:
            print(f"\n❌ Fatal error: {repr(e)}")
            return

# ===================== MAIN =====================
def main():
    fetch_category("primary", label=0)
    fetch_category("updates", label=0)
    fetch_category("promotions", label=1)
    fetch_category("social", label=1)

    if not os.path.exists(FILENAME):
        print("\n⚠️ No dataset created. Exiting.")
        return

    print("\n🧹 Deduplicating dataset...")
    df = pd.read_csv(FILENAME)
    df.drop_duplicates(subset=["text"], inplace=True)
    df.to_csv(FILENAME, index=False)

    print("🎉 JOB COMPLETE")
    print(f"📁 Final dataset size: {len(df)} rows")

if __name__ == "__main__":
    main()
