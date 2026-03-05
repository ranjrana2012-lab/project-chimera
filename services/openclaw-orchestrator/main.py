from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import logging
import httpx

from config import get_settings
from tracing import setup_telemetry, instrument_fastapi
from metrics import init_service_info, record_request
from models import OrchestrateRequest, OrchestrateResponse, HealthResponse

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize tracing
tracer = setup_telemetry(settings.service_name, settings.otlp_endpoint)
init_service_info(settings.service_name, "1.0.0")

# Agent registry (will be used for readiness checks)
AGENTS = {
    "scenespeak-agent": settings.scenespeak_agent_url,
    "captioning-agent": settings.captioning_agent_url,
    "bsl-agent": settings.bsl_agent_url,
    "sentiment-agent": settings.sentiment_agent_url,
    "lighting-sound-music": settings.lighting_sound_music_url,
    "safety-filter": settings.safety_filter_url,
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    logger.info("OpenClaw Orchestrator starting up")
    yield
    logger.info("OpenClaw Orchestrator shutting down")

app = FastAPI(
    title="OpenClaw Orchestrator",
    description="Central control plane for Project Chimera - routes skills to agents",
    version="1.0.0",
    lifespan=lifespan
)

# Instrument FastAPI
instrument_fastapi(app, "openclaw-orchestrator")

@app.get("/health/live")
async def liveness():
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness():
    """Check if all agents are ready"""
    checks = {}

    async with httpx.AsyncClient(timeout=5.0) as client:
        for agent_name, agent_url in AGENTS.items():
            try:
                response = await client.get(f"{agent_url}/health/live")
                checks[agent_name] = response.status_code == 200
            except Exception as e:
                logger.warning(f"Agent {agent_name} not ready: {e}")
                checks[agent_name] = False

    all_ready = all(checks.values())
    status = "ready" if all_ready else "not_ready"

    return HealthResponse(status=status, checks=checks)

@app.post("/v1/orchestrate")
async def orchestrate(request: OrchestrateRequest):
    """Route skill request to appropriate agent"""
    import time
    start_time = time.time()

    try:
        # Determine which agent handles this skill
        agent_url = get_agent_for_skill(request.skill)

        # Call the agent
        result = await call_agent(agent_url, request.skill, request.input)

        duration = (time.time() - start_time) * 1000

        # Record metrics
        record_request(request.skill, 200, duration / 1000)

        return OrchestrateResponse(
            result=result,
            skill_used=request.skill,
            execution_time=duration / 1000,
            metadata={}
        )

    except httpx.ConnectError as e:
        logger.error(f"Agent connection failed: {e}")
        duration = (time.time() - start_time) * 1000
        record_request(request.skill, 503, duration / 1000)
        raise HTTPException(status_code=503, detail=f"Agent unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        duration = (time.time() - start_time) * 1000
        record_request(request.skill, 500, duration / 1000)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/skills")
async def list_skills():
    """List available skills"""
    skills = [
        {
            "name": "dialogue_generator",
            "description": "Generate contextual dialogue",
            "version": "1.0.0",
            "enabled": True
        },
        {
            "name": "captioning",
            "description": "Speech-to-text transcription",
            "version": "1.0.0",
            "enabled": True
        },
        {
            "name": "bsl_translation",
            "description": "Text-to-BSL gloss translation",
            "version": "1.0.0",
            "enabled": True
        },
        {
            "name": "sentiment_analysis",
            "description": "Analyze audience sentiment",
            "version": "1.0.0",
            "enabled": True
        }
    ]

    return {"skills": skills, "total": len(skills), "enabled": len(skills)}

def get_agent_for_skill(skill: str) -> str:
    """Map skill to agent URL"""
    skill_to_agent = {
        "dialogue_generator": AGENTS["scenespeak-agent"],
        "captioning": AGENTS["captioning-agent"],
        "bsl_translation": AGENTS["bsl-agent"],
        "sentiment_analysis": AGENTS["sentiment-agent"],
    }

    if skill not in skill_to_agent:
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill}")

    return skill_to_agent[skill]

async def call_agent(agent_url: str, skill: str, input_data: dict) -> dict:
    """Call agent endpoint"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{agent_url}/v1/{skill}",
            json=input_data
        )
        response.raise_for_status()
        return response.json()
