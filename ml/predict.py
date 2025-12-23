import torch
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification
)

MODEL_DIR = "models/distilbert"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# 🔐 Hard rules that ALWAYS win
IMPORTANT_KEYWORDS = [
    "otp",
    "one time password",
    "verification code",
    "bank",
    "transaction",
    "debit",
    "credit",
    "login",
    "security alert",
    "suspicious activity",
    "password",
    "account access",
]

tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_DIR)
model = DistilBertForSequenceClassification.from_pretrained(MODEL_DIR)
model.to(DEVICE)
model.eval()


def rule_based_override(text: str) -> bool:
    text = text.lower()
    return any(k in text for k in IMPORTANT_KEYWORDS)


@torch.no_grad()
def predict_email(text: str) -> dict:
    # Rule-based override
    if rule_based_override(text):
        return {
            "label": "IMPORTANT",
            "confidence": 1.00,
            "source": "rule"
        }

    inputs = tokenizer(
        text,
        truncation=True,
        padding=True,
        return_tensors="pt"
    ).to(DEVICE)

    outputs = model(**inputs)
    probs = torch.softmax(outputs.logits, dim=1)
    confidence, label_id = torch.max(probs, dim=1)

    return {
        "label": "IMPORTANT" if label_id.item() == 1 else "SPAM",
        "confidence": round(confidence.item(), 3),
        "source": "ml"
    }


if __name__ == "__main__":
    test_email = "Your OTP for bank login is 458921"
    print(predict_email(test_email))
