#!/bin/bash
# Project Chimera Phase 2 - Performance Profiling Script
#
# This script profiles the performance of Phase 2 services
# and generates optimization recommendations.

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICES=("dmx-controller:8001" "audio-controller:8002" "bsl-avatar-service:8003")

# Logging
log() {
    local level="$1"
    shift
    echo -e "${level} $*"
}
info() { log "${BLUE}[INFO]${NC}", "$*"; }
success() { log "${GREEN}[SUCCESS]${NC}", "$*"; }
warning() { log "${YELLOW}[WARNING]${NC}", "$*"; }
error() { log "${RED}[ERROR]${NC}", "$*"; }

# Profile service endpoints
profile_service() {
    local service=$1
    local port=$2

    info "Profiling $service (port $port)..."

    # Test response times
    info "Testing response times..."

    for endpoint in "/health" "/api/status" "/metrics"; do
        info "  Testing $endpoint"
        curl -w "\nTime: %{time_total}s\n" -s \
            "http://localhost:$port$endpoint" || true
    done

    # Check resource usage
    info "Checking resource usage..."
    local container_name="chimera-${service//-/_}"

    if docker ps | grep -q "$container_name"; then
        docker stats "$container_name" --no-stream --format \
            "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
    fi

    echo ""
}

# Profile memory usage
profile_memory() {
    info "Profiling memory usage..."

    for service_port in "${SERVICES[@]}"; do
        IFS=':' read -r service port <<< "$service_port"

        info "Checking $service memory..."

        if docker ps | grep -q "chimera-${service//-/_}"; then
            docker stats "chimera-${service//-/_}" --no-stream --format \
                "table {{.MemUsage}}\t{{.MemPerc}}"
        fi
    done
}

# Profile CPU usage
profile_cpu() {
    info "Profiling CPU usage..."

    for service_port in "${SERVICES[@]}"; do
        IFS=':' read -r service port <<< "$service_port"

        info "Checking $service CPU..."

        if docker ps | grep -q "chimera-${service//-/_}"; then
            docker stats "chimera-${service//-/_}" --no-stream --format \
                "table {{.CPUPerc}}\t{{.Container}}\t{{.NetIO}}"
        fi
    done
}

# Generate recommendations
generate_recommendations() {
    info "Generating optimization recommendations..."

    cat << 'EOF'
=================================================================
Project Chimera Phase 2 - Performance Recommendations
=================================================================

1. Service Optimization:
   - Ensure all services run with appropriate worker counts
   - Enable HTTP/2 for service-to-service communication
   - Use connection pooling for database connections

2. Caching Strategy:
   - Implement caching for frequently accessed data
   - Use Redis for distributed caching
   - Set appropriate cache expiration times

3. Async Operations:
   - Use asyncio.gather() for parallel operations
   - Offload CPU-intensive tasks to thread pools
   - Avoid blocking I/O in async functions

4. Resource Management:
   - Set memory limits on containers (256MB per service)
   - Configure CPU quotas (20% per service)
   - Monitor resource usage continuously

5. Monitoring:
   - Set up Prometheus metrics collection
   - Configure Grafana dashboards
   - Enable alerting for performance degradation

6. Load Testing:
   - Run load tests before production deployment
   - Test with realistic traffic patterns
   - Monitor performance under load

=================================================================
EOF
}

# Main function
main() {
    echo "Project Chimera Phase 2 - Performance Profiling"
    echo "=============================================="
    echo ""

    # Profile each service
    for service_port in "${SERVICES[@]}"; do
        IFS=':' read -r service port <<< "$service_port"
        profile_service "$service" "$port"
    done

    # Profile resources
    profile_memory
    profile_cpu

    # Generate recommendations
    generate_recommendations

    success "Performance profiling complete!"
    info ""
    info "For detailed profiling, use:"
    info "  python -m cProfile -o profile.stats service.py"
    info "  python -m memory_profiler service.py"
    info "  snakeviz profile.stats"
}

# Run main function
main "$@"
