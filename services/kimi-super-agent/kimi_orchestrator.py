"""Main gRPC server for Kimi K2.6 super-agent."""

import asyncio
import logging
import os
import signal
from typing import Dict, Any
import grpc
from dotenv import load_dotenv

try:
    from .proto import kimi_pb2, kimi_pb2_grpc
    from .kimi_client import KimiClient
    from .capability_detector import CapabilityDetector
    from .agent_coordinator import AgentCoordinator
except ImportError:  # pragma: no cover - supports direct script execution
    from proto import kimi_pb2, kimi_pb2_grpc
    from kimi_client import KimiClient
    from capability_detector import CapabilityDetector
    from agent_coordinator import AgentCoordinator

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class KimiSuperAgentServicer(kimi_pb2_grpc.KimiSuperAgentServicer):
    """gRPC servicer for Kimi super-agent."""

    def __init__(self):
        self.kimi_client = KimiClient()
        self.capability_detector = CapabilityDetector()
        self.agent_coordinator = AgentCoordinator()
        logger.info("KimiSuperAgentServicer initialized")

    async def Delegate(
        self,
        request: kimi_pb2.DelegationRequest,
        context: grpc.aio.ServicerContext
    ) -> kimi_pb2.DelegationResponse:
        """Handle delegation request from Nemo Claw."""
        request_id = request.request_id
        logger.info(f"Received delegation request: {request_id}")

        start_time = asyncio.get_event_loop().time()

        # Build internal request format
        internal_request = {
            "user_input": request.user_input,
            "multimodal_content": [
                {
                    "type": kimi_pb2.ContentType.Name(content.type),
                    "data": content.data,
                    "mime_type": content.mime_type,
                    "metadata": dict(content.metadata)
                }
                for content in request.multimodal_content
            ]
        }

        # Detect required capability
        hint = self.capability_detector.detect(internal_request)
        logger.info(f"Detected capability: {kimi_pb2.CapabilityHint.Name(hint)}")

        # Check if Kimi should handle this
        delegated_to_kimi = hint != kimi_pb2.CapabilityHint.NONE

        if not delegated_to_kimi:
            # Simple request, return without Kimi processing
            return kimi_pb2.DelegationResponse(
                request_id=request_id,
                response="Request does not require Kimi capabilities",
                metadata=kimi_pb2.ResponseMetadata(
                    tokens_processed=0,
                    processing_time_ms=0,
                    delegated_to_kimi=False
                )
            )

        # Process with Kimi K2.6
        vllm_request = {
            "messages": [
                {"role": "user", "content": request.user_input}
            ],
            "max_tokens": int(os.getenv("KIMI_MAX_TOKENS", "64"))
        }

        try:
            vllm_response = await self.kimi_client.generate(vllm_request)

            response_text = vllm_response["choices"][0]["message"]["content"]
            tokens_used = vllm_response.get("usage", {}).get("total_tokens", 0)

            # Build agent invocations list (empty for Kimi-only responses)
            agent_invocations = []

            metadata = kimi_pb2.ResponseMetadata(
                tokens_processed=tokens_used,
                processing_time_ms=int((asyncio.get_event_loop().time() - start_time) * 1000),
                delegated_to_kimi=True,
                model_version=os.getenv("KIMI_MODEL_NAME", "moonshotai/Kimi-K2.6")
            )

            return kimi_pb2.DelegationResponse(
                request_id=request_id,
                response=response_text,
                agents_used=agent_invocations,
                metadata=metadata
            )

        except Exception as e:
            processing_time_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
            logger.error(
                f"Error processing request {request_id}: {e}",
                extra={
                    "request_id": request_id,
                    "error_type": type(e).__name__,
                    "processing_time_ms": processing_time_ms
                }
            )
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Processing error: {str(e)}")
            return kimi_pb2.DelegationResponse(
                request_id=request_id,
                response="Error processing request",
                metadata=kimi_pb2.ResponseMetadata(
                    tokens_processed=0,
                    processing_time_ms=processing_time_ms,
                    delegated_to_kimi=True,
                    model_version=os.getenv("KIMI_MODEL_NAME", "moonshotai/Kimi-K2.6")
                )
            )

    async def HealthCheck(
        self,
        request: kimi_pb2.HealthCheckRequest,
        context: grpc.aio.ServicerContext
    ) -> kimi_pb2.HealthCheckResponse:
        """Health check endpoint."""
        is_healthy = await self.kimi_client.health_check()

        return kimi_pb2.HealthCheckResponse(
            healthy=is_healthy,
            message="OK" if is_healthy else "vLLM unhealthy"
        )


async def serve() -> None:
    """Start gRPC server."""
    port = int(os.getenv("KIMI_GRPC_PORT", "50052"))
    host = os.getenv("KIMI_GRPC_HOST", "0.0.0.0")

    server = grpc.aio.server(
        maximum_concurrent_rpcs=int(os.getenv("KIMI_MAX_CONCURRENT_REQUESTS", "5"))
    )

    kimi_pb2_grpc.add_KimiSuperAgentServicer_to_server(
        KimiSuperAgentServicer(),
        server
    )

    server_address = f"{host}:{port}"
    server.add_insecure_port(server_address)

    logger.info(f"Starting Kimi Super-Agent server on {server_address}")
    await server.start()
    logger.info("Server started successfully")

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    registered_signals = []

    for shutdown_signal in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(shutdown_signal, stop_event.set)
            registered_signals.append(shutdown_signal)
        except (NotImplementedError, RuntimeError):
            pass

    wait_task = asyncio.create_task(server.wait_for_termination())
    stop_task = asyncio.create_task(stop_event.wait())

    try:
        done, pending = await asyncio.wait(
            {wait_task, stop_task},
            return_when=asyncio.FIRST_COMPLETED,
        )

        if stop_task in done:
            logger.info("Shutting down server")
            await server.stop(0)
        elif wait_task in done:
            await wait_task
    finally:
        for task in (wait_task, stop_task):
            if not task.done():
                task.cancel()

        for shutdown_signal in registered_signals:
            loop.remove_signal_handler(shutdown_signal)


if __name__ == "__main__":
    asyncio.run(serve())
