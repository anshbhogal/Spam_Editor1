import pandas as pd
import torch
from datasets import Dataset
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    Trainer,
    TrainingArguments
)

# -----------------------
# Configuration
# -----------------------
DATA_PATH = "data/emails.csv"
MODEL_NAME = "distilbert-base-uncased"
OUTPUT_DIR = "models/distilbert"

# -----------------------
# Load dataset
# -----------------------
df = pd.read_csv(DATA_PATH)
df = df[['text', 'label']]

print(f"📥 Loaded {len(df)} emails")

dataset = Dataset.from_pandas(df)

# -----------------------
# Tokenizer
# -----------------------
tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_NAME)

def tokenize(batch):
    return tokenizer(
        batch["text"],
        truncation=True,
        padding="max_length",
        max_length=256
    )

dataset = dataset.map(tokenize, batched=True)

# -----------------------
# Train/Test split
# -----------------------
dataset = dataset.train_test_split(
    test_size=0.2,
    shuffle=True,
    seed=42
)

# -----------------------
# Model
# -----------------------
model = DistilBertForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=2
)

# -----------------------
# Training args
# -----------------------
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    eval_strategy="epoch",          # 🔥 FIX
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=3,
    weight_decay=0.01,
    logging_steps=100,
    load_best_model_at_end=True,
    report_to="none",
)


# -----------------------
# Trainer
# -----------------------
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["test"]
)

# -----------------------
# Train
# -----------------------
trainer.train()

# -----------------------
# Save model
# -----------------------
trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print("✅ DistilBERT training complete")
