#!/bin/bash
# scripts/silence-alerts.sh
# Silence AlertManager alerts for maintenance windows

set -e

ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://localhost:9093}"
DURATION="${1:-1h}"
COMMENT="${2:-Maintenance window}"
MATCHERS=""

usage() {
    cat << EOF
Usage: $0 [duration] [comment] [matchers...]

Silence AlertManager alerts for a maintenance window.

Arguments:
  duration   Silence duration (e.g., 5m, 1h, 2h). Default: 1h
  comment    Description of the maintenance. Default: "Maintenance window"
  matchers   Alert matchers in key=value format (e.g., service=scenespeak)

Environment Variables:
  ALERTMANAGER_URL  AlertManager URL. Default: http://localhost:9093

Examples:
  $0 2h "Deploying v1.2.3" service=scenespeak
  $0 30m "Database maintenance" service=postgres severity=critical
  ALERTMANAGER_URL=http://alertmanager:9093 $0 1h "System upgrade"

Output:
  Silence ID and end time are printed on success
  View silences at: \$ALERTMANAGER_URL/#/silences
EOF
    exit 1
}

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    usage
fi

shift 2
MATCHERS=("$@")

# Check if matchers provided
if [[ ${#MATCHERS[@]} -eq 0 ]]; then
    echo "Warning: No matchers provided. This will silence ALL alerts."
    echo "Press Ctrl+C to cancel or Enter to continue..."
    read
fi

# Build silence payload
MATCHER_DATA=""
for matcher in "${MATCHERS[@]}"; do
    IFS='=' read -r name value <<< "$matcher"
    MATCHER_DATA="$MATCHER_DATA{\"name\":\"$name\",\"value\":\"$value\",\"isRegex\":false},"
done

# Calculate end time
# Try GNU date first, then BSD date
END_TIME=$(date -u -d "+$DURATION" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -v+${DURATION} +"%Y-%m-%dT%H:%M:%SZ")

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "Error: jq is required but not installed. Install with: apt install jq / brew install jq"
    exit 1
fi

# Check if curl is available
if ! command -v curl &> /dev/null; then
    echo "Error: curl is required but not installed."
    exit 1
fi

# Create silence
echo "Creating silence for $DURATION..."
echo "Comment: $COMMENT"
if [[ ${#MATCHERS[@]} -gt 0 ]]; then
    echo "Matchers: ${MATCHERS[*]}"
fi
echo ""

SILENCE_ID=$(curl -s -X POST "$ALERTMANAGER_URL/api/v2/silences" \
  -H 'Content-Type: application/json' \
  -d "{
    \"matchers\": [${MATCHER_DATA%,}],
    \"startsAt\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",
    \"endsAt\": \"$END_TIME\",
    \"createdBy\": \"$(whoami)\",
    \"comment\": \"$COMMENT\"
  }" | jq -r '.silenceID // empty')

# Check if silence was created successfully
if [[ -z "$SILENCE_ID" ]]; then
    echo "Error: Failed to create silence"
    echo "Check AlertManager is accessible at: $ALERTMANAGER_URL"
    exit 1
fi

echo "✓ Silence created successfully"
echo "Silence ID: $SILENCE_ID"
echo "Ends at: $END_TIME"
echo "View: $ALERTMANAGER_URL/#/silences"
