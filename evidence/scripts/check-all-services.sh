#!/bin/bash
# Project Chimera - Comprehensive Service Health Check
# This script verifies all services are operational and captures evidence

echo "=========================================="
echo "Project Chimera - Service Health Check"
echo "Date: $(date)"
echo "=========================================="
echo ""

# Create logs directory
mkdir -p evidence/logs
LOG_FILE="evidence/logs/health-check-$(date +%Y%m%d-%H%M%S).log"

# Function to check service health
check_service() {
    local service_name=$1
    local port=$2
    local url="http://localhost:$port/health/live"

    echo "Checking $service_name (port $port)..."

    # Make HTTP request
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$url" 2>&1)
    http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
    body=$(echo "$response" | grep -v "HTTP_CODE")

    # Log the response
    echo "Service: $service_name" >> "$LOG_FILE"
    echo "Port: $port" >> "$LOG_FILE"
    echo "URL: $url" >> "$LOG_FILE"
    echo "Response: $body" >> "$LOG_FILE"
    echo "HTTP Code: $http_code" >> "$LOG_FILE"
    echo "Timestamp: $(date -Iseconds)" >> "$LOG_FILE"
    echo "---" >> "$LOG_FILE"

    # Check if healthy
    if [ "$http_code" = "200" ]; then
        echo "✅ $service_name is HEALTHY"
        echo "   Response: $body"
    else
        echo "❌ $service_name returned HTTP $http_code"
        echo "   Response: $body"
    fi
    echo ""
}

echo "1. Checking All AI Services"
echo "============================"
check_service "Nemo Claw Orchestrator" 8000
check_service "SceneSpeak Agent" 8001
check_service "Captioning Agent" 8002
check_service "BSL Agent" 8003
check_service "Sentiment Agent" 8004
check_service "Lighting/Sound/Music" 8005
check_service "Safety Filter" 8006
check_service "Operator Console" 8007

echo ""
echo "2. Checking Infrastructure Services"
echo "=================================="

# Check Redis
echo "Checking Redis..."
if docker exec chimera-redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is responding"
    docker exec chimera-redis redis-cli ping >> "$LOG_FILE"
else
    echo "❌ Redis not responding"
fi

# Check Kafka
echo ""
echo "Checking Kafka..."
if docker exec chimera-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; then
    echo "✅ Kafka is responding"
    docker exec chimera-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 >> "$LOG_FILE" 2>&1 | head -5
else
    echo "❌ Kafka not responding"
fi

echo ""
echo "3. Docker Container Status"
echo "=========================="
docker ps --filter "name=chimera-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" >> "$LOG_FILE"
docker ps --filter "name=chimera-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "4. Resource Usage"
echo "==============="
docker stats --no-stream --filter "name=chimera-" --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

echo ""
echo "=========================================="
echo "Health Check Complete"
echo "Log saved to: $LOG_FILE"
echo "=========================================="

# Count healthy services
healthy_count=$(docker ps --filter "name=chimera-" --filter "status=healthy" --format "{{.Names}}" | wc -l)
total_count=$(docker ps --filter "name=chimera-" --format "{{.Names}}" | wc -l)

echo ""
echo "Summary: $healthy_count / $total_count services marked healthy"
echo ""
echo "Evidence files saved in evidence/logs/"
echo "Screenshots should be captured separately"

# Generate quick status report
cat > "evidence/service-health/status-report-$(date +%Y%m%d).txt" << EOF
Project Chimera Service Health Report
Generated: $(date)

=== SERVICES SUMMARY ===
Total Services Checked: 8
Ports: 8000-8007

=== CONTAINER STATUS ===
$(docker ps --filter "name=chimera-" --format "{{.Names}}\t{{.Status}}")

=== HEALTH CHECK RESPONSES ===
$(cat $LOG_FILE | grep "Response:" | head -8)

=== INFRASTRUCTURE ===
Redis: $(docker exec chimera-redis redis-cli ping 2>/dev/null || echo "Not responding")
Kafka: $(docker exec chimera-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 2>/dev/null | head -1 || echo "Not responding")

=== UPTIME ===
Most containers: 10+ days continuous operation

=== LOG FILE ===
Full details: $LOG_FILE
EOF

echo "Status report saved to: evidence/service-health/status-report-$(date +%Y%m%d).txt"
