"""Core handler for Operator Console"""

from typing import Dict, Any, List
from datetime import datetime
import httpx


class OperatorHandler:
    def __init__(self, settings):
        self.settings = settings
        self.alerts: List[Dict[str, Any]] = []
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}
        self._http_client = None

    async def initialize(self):
        self._http_client = httpx.AsyncClient()

    async def create_alert(
        self,
        level: str,
        message: str,
        source: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a new alert."""
        alert = {
            "id": f"alert-{len(self.alerts)}",
            "level": level,
            "message": message,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "acknowledged": False,
            "metadata": metadata or {},
        }
        self.alerts.append(alert)
        return alert

    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        for alert in self.alerts:
            if alert["id"] == alert_id:
                alert["acknowledged"] = True
                return True
        return False

    async def get_alerts(self, unacknowledged_only: bool = False) -> List[Dict[str, Any]]:
        """Get alerts."""
        if unacknowledged_only:
            return [a for a in self.alerts if not a["acknowledged"]]
        return self.alerts

    async def request_approval(
        self,
        request_type: str,
        description: str,
        timeout_seconds: int,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Request human approval for an action."""
        approval_id = f"approval-{len(self.pending_approvals)}"

        approval = {
            "id": approval_id,
            "type": request_type,
            "description": description,
            "requested_at": datetime.now().isoformat(),
            "timeout_at": datetime.now().timestamp() + timeout_seconds,
            "status": "pending",
            "metadata": metadata or {},
        }

        self.pending_approvals[approval_id] = approval
        return approval

    async def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get pending approvals."""
        return [a for a in self.pending_approvals.values() if a["status"] == "pending"]

    async def decide_approval(self, approval_id: str, decision: str) -> Dict[str, Any]:
        """Make decision on approval request."""
        if approval_id not in self.pending_approvals:
            return {"error": "Approval not found"}

        self.pending_approvals[approval_id]["status"] = decision
        self.pending_approvals[approval_id]["decided_at"] = datetime.now().isoformat()

        return {"success": True, "decision": decision}

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for operator dashboard."""
        return {
            "alerts": await self.get_alerts(unacknowledged_only=True),
            "pending_approvals": await self.get_pending_approvals(),
            "system_status": await self._get_system_status(),
        }

    async def _get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        # Check key services
        services = {
            "safety_filter": self.settings.safety_filter_endpoint,
            "lighting_control": self.settings.lighting_endpoint,
        }

        status = {}
        for name, endpoint in services.items():
            try:
                response = await self._http_client.get(f"{endpoint}/health/ready", timeout=2.0)
                status[name] = "healthy" if response.status_code == 200 else "degraded"
            except Exception:
                status[name] = "unhealthy"

        return status

    async def close(self):
        if self._http_client:
            await self._http_client.aclose()
