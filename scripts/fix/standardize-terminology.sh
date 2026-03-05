#!/bin/bash
# Standardize terminology across documentation

echo "Standardizing terminology..."

# Ensure consistent service names
find docs -name "*.md" -type f -exec sed -i 's/scenespeak-agent/SceneSpeak Agent/g' {} \;
find docs -name "*.md" -type f -exec sed -i 's/sentiment-agent/Sentiment Agent/g' {} \;
find docs -name "*.md" -type f -exec sed -i 's/captioning-agent/Captioning Agent/g' {} \;
find docs -name "*.md" -type f -exec sed -i 's/bsl-agent/BSL Agent/g' {} \;

# Ensure consistent component naming
find docs -name "*.md" -type f -exec sed -i 's/Alertmanager/AlertManager/g' {} \;
find docs -name "*.md" -type f -exec sed -i 's/Prometheus/Prometheus/g' {} \;

echo "Terminology standardized"
