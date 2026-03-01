import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4

from music_orchestration.approval import ApprovalPipeline
from music_orchestration.schemas import UseCase


@pytest.mark.asyncio
async def test_marketing_auto_approves():
    db_mock = Mock()
    db_mock.execute = AsyncMock()

    pipeline = ApprovalPipeline(database=db_mock)

    result = await pipeline.submit_for_approval(
        music_id=str(uuid4()),
        use_case=UseCase.MARKETING
    )

    assert result["status"] == "approved"
    assert result["auto_approved"] is True


@pytest.mark.asyncio
async def test_show_requires_manual_approval():
    db_mock = Mock()
    db_mock.execute = AsyncMock()

    pipeline = ApprovalPipeline(database=db_mock)

    result = await pipeline.submit_for_approval(
        music_id=str(uuid4()),
        use_case=UseCase.SHOW
    )

    assert result["status"] == "pending_approval"
    assert result["auto_approved"] is False
