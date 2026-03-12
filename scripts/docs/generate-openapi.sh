#!/bin/bash
# Generate merged OpenAPI spec from all services

set -e

OUTPUT_FILE="docs/api/openapi.yaml"
SERVICES=(
    "OpenClaw Orchestrator:http://localhost:8000"
    "SceneSpeak Agent:http://localhost:8001"
    "Captioning Agent:http://localhost:8002"
    "BSL Agent:http://localhost:8003"
    "Sentiment Agent:http://localhost:8004"
    "Lighting-Sound-Music:http://localhost:8005"
    "Safety Filter:http://localhost:8006"
    "Operator Console:http://localhost:8007"
    "Music Generation:http://localhost:8011"
)

echo "Generating OpenAPI specification..."

# Start the file with header
cat > "$OUTPUT_FILE" << 'EOF'
openapi: 3.0.3
info:
  title: Project Chimera API
  description: |
    API specification for Project Chimera - An AI-powered live theatre platform.

    This merged specification includes endpoints from all microservices.
  version: 1.0.0
  contact:
    name: Project Chimera Team
  license:
    name: MIT

servers:
  - url: http://localhost:8000
    description: OpenClaw Orchestrator
  - url: http://localhost:8001
    description: SceneSpeak Agent
  - url: http://localhost:8002
    description: Captioning Agent
  - url: http://localhost:8003
    description: BSL Agent
  - url: http://localhost:8004
    description: Sentiment Agent
  - url: http://localhost:8005
    description: Lighting-Sound-Music
  - url: http://localhost:8006
    description: Safety Filter
  - url: http://localhost:8007
    description: Operator Console
  - url: http://localhost:8011
    description: Music Generation

tags:
  - name: orchestrator
    description: OpenClaw Orchestrator endpoints
  - name: scenespeak
    description: SceneSpeak Agent endpoints
  - name: captioning
    description: Captioning Agent endpoints
  - name: bsl
    description: BSL Agent endpoints
  - name: sentiment
    description: Sentiment Agent endpoints
  - name: lighting
    description: Lighting/Sound/Music endpoints
  - name: safety
    description: Safety Filter endpoints
  - name: console
    description: Operator Console endpoints
  - name: music
    description: Music Generation endpoints

paths:
EOF

# Append paths from each service
for service in "${SERVICES[@]}"; do
    NAME="${service%%:*}"
    URL="${service##*:}"

    echo "Fetching OpenAPI from $NAME at $URL"

    if response=$(curl -s "$URL/openapi.json"); then
        # Use Python to parse and append paths
        echo "$response" | python3 -c "
import json, sys
data = json.load(sys.stdin)
paths = data.get('paths', {})
for path, methods in paths.items():
    print(f'  {path}:')
    for method, details in methods.items():
        print(f'    {method}:')
        summary = details.get('summary', '')
        if summary:
            # Escape colons and special characters
            summary = summary.replace(':', '\\:')
            print(f'      summary: {summary}')
        description = details.get('description', '')
        if description:
            # Escape special characters
            desc = description.replace('\\n', ' ').replace(':', '\\:')
            print(f'      description: {desc}')
        operation_id = details.get('operationId', '')
        if operation_id:
            print(f'      operationId: {operation_id}')
        tags = details.get('tags', [])
        if tags:
            print(f'      tags:')
            for tag in tags:
                print(f'        - {tag}')
        responses = details.get('responses', {})
        if responses:
            print(f'      responses:')
            for code, resp in responses.items():
                print(f'        \"{code}\":')
                resp_desc = resp.get('description', '')
                if resp_desc:
                    print(f'          description: {resp_desc}')
        # Add blank line for readability
        print()
" >> "$OUTPUT_FILE" 2>/dev/null || echo "# Error processing $NAME"
    else
        echo "# Warning: Could not fetch from $NAME ($URL)" >> "$OUTPUT_FILE"
    fi
done

echo ""
echo "OpenAPI spec generated at $OUTPUT_FILE"
echo "Total lines: $(wc -l < "$OUTPUT_FILE")"
