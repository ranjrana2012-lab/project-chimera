#!/bin/bash
set -e

REGISTRY="localhost:30500"
VERSION="latest"

SERVICES=(
    "openclaw-orchestrator"
    "scenespeak-agent"
    "captioning-agent"
    "bsl-text2gloss-agent"
    "sentiment-agent"
    "lighting-control"
    "safety-filter"
    "operator-console"
)

echo "⏳ [3/7] Building all service images..."

for service in "${SERVICES[@]}"; do
    echo "⏳ Building $service..."
    [ ! -d "services/$service" ] && echo "⚠️  Service directory not found: services/$service" && continue
    docker build -t $REGISTRY/project-chimera/$service:$VERSION services/$service/
    echo "⏳ Pushing $service..."
    docker push $REGISTRY/project-chimera/$service:$VERSION
    echo "✅ $service built and pushed"
done

echo "✅ [3/7] All images built"
docker images | grep project-chimera
