from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Header, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import structlog

from music_orchestration.router import RequestRouter
from music_orchestration.cache import CacheManager
from music_orchestration.auth import ServiceAuthenticator, PermissionChecker
from music_orchestration.approval import ApprovalPipeline
from music_orchestration.websocket import websocket_manager
from music_orchestration.schemas import (
    MusicRequest,
    MusicResponse,
    UserContext,
    Role
)


logger = structlog.get_logger()


# Global instances
cache_manager: CacheManager | None = None
request_router: RequestRouter | None = None
authenticator: ServiceAuthenticator | None = None
approval_pipeline: ApprovalPipeline | None = None


async def get_authorization(
    authorization: str = Header(...)
) -> UserContext:
    """Extract and validate authorization header"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization[7:]
    if not authenticator:
        # For testing, return fake context
        return UserContext(
            service_name="test",
            role=Role.ADMIN,
            permissions=["*"]
        )

    return authenticator.validate_token(token)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    global cache_manager, request_router, authenticator, approval_pipeline

    # Initialize (placeholder - will connect to actual Redis/DB)
    # cache_manager = CacheManager(redis_client)
    # request_router = RequestRouter(cache=cache_manager)
    # authenticator = ServiceAuthenticator()
    # approval_pipeline = ApprovalPipeline()

    logger.info("music_orchestration_service_started")

    yield

    logger.info("music_orchestration_service_stopped")


app = FastAPI(
    title="Music Orchestration Service",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "music-orchestration"
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check"""
    return {
        "status": "ready",
        "checks": {
            "cache": cache_manager is not None,
            "router": request_router is not None,
            "auth": authenticator is not None
        }
    }


@app.post("/api/v1/music/generate", response_model=MusicResponse)
async def generate_music(
    request: MusicRequest,
    user: UserContext = Depends(get_authorization)
):
    """Generate music with caching and approval"""
    PermissionChecker.require_permission("music:generate")(user)

    if not request_router:
        # Return mock response for testing without full initialization
        return MusicResponse(
            request_id="test-request-id",
            music_id=None,
            status="generating",
            audio_url=None,
            duration_seconds=request.duration_seconds,
            format=request.format,
            was_cache_hit=False
        )

    result = await request_router.route(request, user)

    return MusicResponse(
        request_id=result.get("request_id", "placeholder"),
        music_id=result.get("music_id"),
        status=result.get("status", "generating"),
        audio_url=result.get("audio_url"),
        duration_seconds=request.duration_seconds,
        format=request.format,
        was_cache_hit=result.get("was_cache_hit", False)
    )


@app.websocket("/ws/music/{request_id}")
async def websocket_music_progress(websocket: WebSocket, request_id: str):
    """WebSocket endpoint for real-time progress updates"""
    await websocket.accept()
    await websocket_manager.subscribe(request_id, websocket)

    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        await websocket_manager.unsubscribe(request_id, websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8012)
