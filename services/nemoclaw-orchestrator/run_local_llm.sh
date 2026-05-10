#!/bin/bash
# Simple local LLM server using llama.cpp

MODEL_PATH="${CHIMERA_MODEL_PATH:-$HOME/Project_Chimera_Downloads/LLM Models/mythomax-l2-13b-gguf/mythomax-l2-13b.Q4_K_M.gguf}"

# Check if model exists
if [ ! -f "$MODEL_PATH" ]; then
    echo "Model not found at $MODEL_PATH"
    echo "Using Llama-3-70B instead..."
    MODEL_PATH="${CHIMERA_FALLBACK_MODEL_PATH:-$HOME/Project_Chimera_Downloads/LLM Models/meta-llama3-70b-instruct-gguf/Meta-Llama-3-70B-Instruct-Q4_K_M.gguf}"
fi

# Check if llama.cpp is installed
if ! command -v llama-server &> /dev/null; then
    echo "llama-server not found. Installing llama.cpp..."
    git clone https://github.com/ggerganov/llama.cpp /tmp/llama.cpp
    cd /tmp/llama.cpp
    make
    sudo cp llama-server /usr/local/bin/
fi

# Start llama-server
echo "Starting local LLM server with model: $MODEL_PATH"
llama-server \
    -m "$MODEL_PATH" \
    -ngl 99 \
    -c 2048 \
    --port 8002 \
    --host 0.0.0.0 \
    --log-format text
