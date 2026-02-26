"""Review queue for flagged content"""

import uuid
from typing import Dict, Any, List
from datetime import datetime, timedelta


class ReviewQueue:
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.items: Dict[str, Dict[str, Any]] = {}

    async def add(self, content: str, result: Dict[str, Any]) -> str:
        """Add item to review queue."""
        item_id = str(uuid.uuid4())

        self.items[item_id] = {
            "id": item_id,
            "content": content,
            "result": result,
            "timestamp": datetime.now().isoformat(),
            "decision": None,
        }

        # Prune old items
        await self._prune()

        return item_id

    async def get_items(self) -> List[Dict[str, Any]]:
        """Get all items in queue."""
        return list(self.items.values())

    async def decide(self, item_id: str, decision: str) -> bool:
        """Record decision for an item."""
        if item_id in self.items:
            self.items[item_id]["decision"] = decision
            return True
        return False

    async def _prune(self):
        """Remove old items."""
        cutoff = datetime.now() - timedelta(hours=1)
        to_remove = [
            k for k, v in self.items.items()
            if datetime.fromisoformat(v["timestamp"]) < cutoff
        ]
        for k in to_remove:
            del self.items[k]
