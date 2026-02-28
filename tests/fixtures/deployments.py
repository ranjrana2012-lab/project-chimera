"""k3s deployment helpers for testing."""
import time
import subprocess
from typing import List


class K3sHelper:
    """Helper for k3s cluster operations."""

    NAMESPACE = "live"

    @staticmethod
    def get_pods() -> List[dict]:
        """Get all pods in the live namespace."""
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", K3sHelper.NAMESPACE, "-o", "json"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return []
        import json
        data = json.loads(result.stdout)
        return data.get("items", [])

    @staticmethod
    def get_pod_name(service: str) -> str:
        """Get the pod name for a service."""
        pods = K3sHelper.get_pods()
        for pod in pods:
            if pod["metadata"]["name"].startswith(service):
                return pod["metadata"]["name"]
        return ""

    @staticmethod
    def restart_service(service: str) -> bool:
        """Restart a service deployment."""
        result = subprocess.run(
            ["kubectl", "rollout", "restart", f"deployment/{service}", "-n", K3sHelper.NAMESPACE],
            capture_output=True,
            text=True
        )
        return result.returncode == 0

    @staticmethod
    def wait_for_service_ready(service: str, timeout: int = 60) -> bool:
        """Wait for a service to be ready."""
        start = time.time()
        while time.time() - start < timeout:
            pods = K3sHelper.get_pods()
            for pod in pods:
                if pod["metadata"]["name"].startswith(service):
                    if pod["status"]["phase"] == "Running":
                        return True
            time.sleep(2)
        return False

    @staticmethod
    def port_forward(service: str, local_port: int, service_port: int = None) -> subprocess.Popen:
        """Start port forwarding for a service."""
        if service_port is None:
            service_port = local_port
        return subprocess.Popen(
            ["kubectl", "port-forward", "-n", K3sHelper.NAMESPACE,
             f"svc/{service}", f"{local_port}:{service_port}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    @staticmethod
    def check_service_health(url: str) -> bool:
        """Check if a service is healthy."""
        try:
            import requests
            response = requests.get(f"{url}/health/live", timeout=2)
            return response.status_code == 200
        except:
            return False
