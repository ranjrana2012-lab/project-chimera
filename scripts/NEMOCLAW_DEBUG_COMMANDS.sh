#!/bin/bash
# NemoClaw Debug Commands for DGX Spark
# Use this script to gather information for troubleshooting

echo "=== NemoClaw DGX Spark Debug Information ==="
echo ""

echo "1. System Information"
echo "-------------------"
echo "Architecture: $(uname -m)"
echo "Kernel: $(uname -r)"
echo "OS: $(cat /etc/os-release | grep PRETTY_NAME)"
echo ""

echo "2. Cgroup Information"
echo "--------------------"
echo "Cgroup Version: $(docker info 2>/dev/null | grep "Cgroup Version" | awk '{print $3}')"
echo "Cgroup Driver: $(docker info 2>/dev/null | grep "Cgroup Driver" | awk '{print $3}')"
echo ""

echo "3. Docker Configuration"
echo "-----------------------"
cat /etc/docker/daemon.json 2>/dev/null || echo "No daemon.json found"
echo ""

echo "4. OpenShell Containers"
echo "-----------------------"
docker ps -a --filter "name=openshell" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "5. k3s Pod Status (if gateway running)"
echo "---------------------------------------"
if docker ps | grep -q openshell-cluster-nemoclaw; then
    docker exec openshell-cluster-nemoclaw kubectl get pods -A 2>/dev/null || echo "kubectl not available"
else
    echo "No gateway container running"
fi
echo ""

echo "6. CoreDNS Status"
echo "-----------------"
if docker ps | grep -q openshell-cluster-nemoclaw; then
    docker exec openshell-cluster-nemoclash kubectl get pods -n kube-system -l k8s-app=kube-dns 2>/dev/null || echo "CoreDNS pods not found"
fi
echo ""

echo "7. Recent Gateway Logs"
echo "-----------------------"
if docker ps | grep -q openshell-cluster-nemoclaw; then
    docker logs openshell-cluster-nemoclaw --tail 20 2>&1 | grep -E "ERROR|WARN|Failed" || echo "No recent errors"
fi
echo ""

echo "8. Port Status"
echo "---------------"
echo "Port 8080: $(ss -tlnp | grep :8080 > /dev/null && echo "IN USE" || echo "FREE")"
echo "Port 18789: $(ss -tlnp | grep :18789 > /dev/null && echo "IN USE" || echo "FREE")"
echo ""

echo "9. NemoClaw Version"
echo "-------------------"
nemoclaw --version 2>/dev/null || echo "NemoClaw not in PATH"
echo ""

echo "10. OpenShell Version"
echo "---------------------"
openshell --version 2>/dev/null || echo "OpenShell not in PATH"
echo ""

echo "=== End of Debug Information ==="
echo ""
echo "To save this output:"
echo "  $0 > nemoclaw-debug-$(date +%Y%m%d).txt"
