from uuid import UUID
from music_orchestration.schemas import UseCase
from music_orchestration.database import get_session_maker


class ApprovalPipeline:
    """Staged approval: marketing auto-approves, show requires manual"""

    def __init__(self, database=None):
        self.session_maker = database or get_session_maker()

    async def submit_for_approval(
        self,
        music_id: str,
        use_case: UseCase,
        user_id: UUID | None = None
    ) -> dict:
        """Submit music for approval based on use case"""
        if use_case == UseCase.MARKETING:
            # Auto-approve marketing content
            return {
                "music_id": music_id,
                "status": "approved",
                "auto_approved": True
            }

        # Show content requires manual approval
        return {
            "music_id": music_id,
            "status": "pending_approval",
            "auto_approved": False
        }

    async def approve(
        self,
        music_id: str,
        user_id: UUID,
        reason: str | None = None
    ) -> dict:
        """Manually approve show music"""
        async with self.session_maker() as session:
            # Update music_generations table
            # Log to music_approvals table
            pass

        return {
            "music_id": music_id,
            "status": "approved",
            "approved_by": str(user_id)
        }

    async def reject(
        self,
        music_id: str,
        user_id: UUID,
        reason: str
    ) -> dict:
        """Reject show music"""
        async with self.session_maker() as session:
            # Update music_generations table
            # Log to music_approvals table
            pass

        return {
            "music_id": music_id,
            "status": "rejected",
            "rejected_by": str(user_id),
            "reason": reason
        }

    async def get_pending_approvals(self, user_role: str) -> list[dict]:
        """Get list of pending approvals"""
        async with self.session_maker() as session:
            # Query music_generations where approval_status = 'pending_approval'
            pass

        return []
