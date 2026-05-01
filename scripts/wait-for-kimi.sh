#!/bin/bash
# Wait for Kimi vLLM service to be healthy

set -e

VLLM_ENDPOINT="${KIMI_VLLM_ENDPOINT:-http://localhost:8012}"
MAX_WAIT="${MAX_WAIT:-600}"  # 10 minutes default
WAIT_INTERVAL=5

echo "Waiting for Kimi vLLM at ${VLLM_ENDPOINT}..."
echo "Max wait: ${MAX_WAIT}s"

elapsed=0
while [ $elapsed -lt $MAX_WAIT ]; do
    if curl -sf "${VLLM_ENDPOINT}/health" > /dev/null 2>&1; then
        echo ""
        echo "✓ Kimi vLLM is ready!"
        exit 0
    fi

    echo -n "."
    sleep $WAIT_INTERVAL
    elapsed=$((elapsed + WAIT_INTERVAL))
done

echo ""
echo "✗ Timeout waiting for Kimi vLLM"
exit 1
