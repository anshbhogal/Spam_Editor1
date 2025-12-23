import pandas as pd
import re

INPUT_FILE = "data/full_email_dataset.csv"   # old IMAP dataset
OUTPUT_FILE = "data/emails.csv"               # new clean dataset

# -----------------------------
# 1. Load dataset
# -----------------------------
df = pd.read_csv(INPUT_FILE)

print("📥 Loaded dataset")
print(df.head())

# -----------------------------
# 2. Basic validation
# -----------------------------
required_cols = {"text", "label"}
if not required_cols.issubset(df.columns):
    raise ValueError("❌ Dataset must contain 'text' and 'label' columns")

# Drop empty / null text
df.dropna(subset=["text"], inplace=True)
df["text"] = df["text"].astype(str)

# Remove ultra-short garbage emails
df = df[df["text"].str.len() > 20]

print(f"🧹 After cleaning: {len(df)} rows")

# -----------------------------
# 3. Fix label semantics
# OLD: 0 = safe, 1 = spam
# NEW: 1 = IMPORTANT, 0 = SPAM
# -----------------------------
df["label"] = df["label"].map({0: 1, 1: 0})

if df["label"].isnull().any():
    raise ValueError("❌ Label conversion failed")

print("🔁 Labels remapped")

# -----------------------------
# 4. Keyword sanity checks
# -----------------------------
IMPORTANT_KEYWORDS = [
    "otp", "one time password", "verification code",
    "bank", "transaction", "debit", "credit",
    "login", "sign-in", "security alert"
]

def contains_important_keyword(text):
    t = text.lower()
    return any(k in t for k in IMPORTANT_KEYWORDS)

# Find suspicious cases
suspicious = df[
    (df["label"] == 0) &
    (df["text"].apply(contains_important_keyword))
]

print(f"⚠️ Suspicious samples (important keywords but labeled spam): {len(suspicious)}")

# Save for manual review
if len(suspicious) > 0:
    suspicious.sample(min(20, len(suspicious))).to_csv(
        "data/suspicious_samples.csv", index=False
    )
    print("📝 Saved suspicious_samples.csv for manual review")

# -----------------------------
# 5. Final stats
# -----------------------------
print("\n📊 Final label distribution:")
print(df["label"].value_counts())

# -----------------------------
# 6. Save final dataset
# -----------------------------
df.to_csv(OUTPUT_FILE, index=False)
print(f"\n✅ Clean dataset saved to {OUTPUT_FILE}")
