#!/bin/bash
# Download DistilBERT model for Sentiment Agent

set -e

MODEL_NAME="distilbert-base-uncased-finetuned-sst-2-english"
CACHE_DIR="./models_cache"

echo "Downloading $MODEL_NAME..."
mkdir -p "$CACHE_DIR"

python3 << EOF
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import torch

print(f"Downloading {MODEL_NAME}...")
tokenizer = DistilBertTokenizer.from_pretrained("$MODEL_NAME", cache_dir="$CACHE_DIR")
model = DistilBertForSequenceClassification.from_pretrained("$MODEL_NAME", cache_dir="$CACHE_DIR")
print("Download complete!")
print(f"Model cached to: $CACHE_DIR")
EOF

echo "Model download complete"
