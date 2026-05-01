"""Integration tests for Kimi K2.6 super-agent."""

import pytest
import grpc
import sys
import os

# Add the kimi-super-agent service directory to path for proto imports
kimi_service_path = os.path.join(os.path.dirname(__file__), '../../services/kimi-super-agent')
if kimi_service_path not in sys.path:
    sys.path.insert(0, kimi_service_path)

from proto import kimi_pb2, kimi_pb2_grpc


@pytest.mark.integration
class TestKimiSuperAgentIntegration:
    """End-to-end integration tests for Kimi super-agent."""

    @pytest.fixture
    async def grpc_channel(self):
        """Create gRPC channel to super-agent."""
        channel = grpc.aio.insecure_channel("localhost:50052")
        yield channel
        await channel.close()

    @pytest.fixture
    def stub(self, grpc_channel):
        """Create gRPC stub."""
        return kimi_pb2_grpc.KimiSuperAgentStub(grpc_channel)

    @pytest.mark.asyncio
    async def test_health_check(self, stub):
        """Test health check endpoint."""
        request = kimi_pb2.HealthCheckRequest()
        response = await stub.HealthCheck(request)

        assert response.healthy is True
        assert response.message == "OK"

    @pytest.mark.asyncio
    async def test_delegate_long_context(self, stub):
        """Test delegation of long context request."""
        request = kimi_pb2.DelegationRequest(
            request_id="test-long-1",
            user_input="A" * 10000,
            capability_hint=kimi_pb2.CapabilityHint.LONG_CONTEXT
        )

        response = await stub.Delegate(request)

        assert response.request_id == "test-long-1"
        assert response.metadata.delegated_to_kimi is True
        assert len(response.response) > 0

    @pytest.mark.asyncio
    async def test_delegate_multimodal(self, stub):
        """Test delegation of multimodal request."""
        # Create test image data
        test_image = b"fake_image_data"

        content = kimi_pb2.MultimodalContent(
            type=kimi_pb2.ContentType.IMAGE,
            data=test_image,
            mime_type="image/png"
        )

        request = kimi_pb2.DelegationRequest(
            request_id="test-mm-1",
            user_input="Describe this image",
            multimodal_content=[content],
            capability_hint=kimi_pb2.CapabilityHint.MULTIMODAL
        )

        response = await stub.Delegate(request)

        assert response.request_id == "test-mm-1"
        assert response.metadata.delegated_to_kimi is True

    @pytest.mark.asyncio
    async def test_no_delegation_simple_request(self, stub):
        """Test that simple requests are not delegated."""
        request = kimi_pb2.DelegationRequest(
            request_id="test-simple-1",
            user_input="Hello, how are you?",
            capability_hint=kimi_pb2.CapabilityHint.NONE
        )

        response = await stub.Delegate(request)

        assert response.request_id == "test-simple-1"
        assert response.metadata.delegated_to_kimi is False
