#!/bin/bash
# Download Kimi-Dev-72B Native INT4 for DGX Spark GB10

set -e

MODEL_NAME="moonshotai/Kimi-Dev-72B"
CACHE_DIR="./models/kimi"
VENV=".venv_kimi"

echo "================================================"
echo "Kimi-Dev-72B Model Download Script"
echo "================================================"
echo "Model: ${MODEL_NAME}"
echo "Cache: ${CACHE_DIR}"
echo ""

# Create cache directory
mkdir -p "${CACHE_DIR}"

# Create virtual environment
if [ ! -d "$VENV" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV"
fi

source "$VENV/bin/activate"

# Install huggingface_hub
echo "Installing huggingface_hub..."
pip install --upgrade huggingface_hub hf-transfer

# Disable fast transfer as it causes connection resets on large models
# export HF_HUB_ENABLE_HF_TRANSFER=1

# Download model
echo ""
echo "Downloading Kimi-Dev-72B (Native INT4)..."
echo "This may take 15-30 minutes depending on connection speed."
echo ""

python3 << PYTHON_SCRIPT
import os
from huggingface_hub import snapshot_download
import shutil

try:
    snapshot_download(
        repo_id="${MODEL_NAME}",
        local_dir="${CACHE_DIR}",
        local_dir_use_symlinks=False,
        resume_download=True,
        allow_patterns=["*.safetensors", "*.json", "*.tiktoken", "*.txt", "*.model", "tokenizer*"],
    )
    print("\n✓ Download complete!")
except Exception as e:
    print(f"\n✗ Error downloading model: {e}")
    exit(1)
PYTHON_SCRIPT

# Verify download
echo ""
echo "Verifying download..."
if [ -d "${CACHE_DIR}" ] && [ "$(ls -A ${CACHE_DIR})" ]; then
    echo "✓ Model files present"
    echo ""
    echo "Disk usage:"
    du -sh "${CACHE_DIR}"
    echo ""
    echo "Model contents:"
    ls -lh "${CACHE_DIR}" | head -20
    echo ""
    echo "================================================"
    echo "✓ Kimi-Dev-72B download complete!"
    echo "================================================"
    echo ""
    echo "Model location: ${CACHE_DIR}"
    echo "Next step: Start vLLM with:"
    echo "  docker compose -f docker-compose.mvp.yml -f docker-compose.dgx-spark.yml up -d kimi-vllm"
else
    echo "✗ Download verification failed"
    exit 1
fi
