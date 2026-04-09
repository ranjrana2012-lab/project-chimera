"""
Opinion Pipeline Orchestrator

Bridges BettaFish outputs and MiroFish inputs, providing
enriched sentiment data to Chimera services.

Data Flow:
    User Query → BettaFish (public opinion analysis)
              ↓
    Markdown Report → MiroFish (swarm simulation)
              ↓
    Prediction Data → Chimera Services (sentiment enrichment)
              ↓
    OpenClaw Bots (real-time reporting)
"""

import os
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import httpx
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add shared module to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../shared'))

try:
    from shared.middleware import SecurityHeadersMiddleware, configure_cors
    from shared.logging import setup_logging
    setup_logging()
except ImportError:
    logger.warning("Shared middleware not available, running without security features")

app = FastAPI(
    title="Opinion Pipeline Service",
    description="Orchestrates BettaFish and MiroFish for sentiment enrichment",
    version="1.0.0"
)

# Security middleware
try:
    configure_cors(app)
    app.add_middleware(SecurityHeadersMiddleware)
except Exception as e:
    logger.warning(f"Could not apply security middleware: {e}")

# Configuration
BETTAFISH_REPORT_PATH = Path(os.environ.get("BETTAFISH_REPORT_PATH", "./integrations/bettafish/reports"))
MIROFISH_API_URL = os.environ.get("MIROFISH_API_URL", "http://127.0.0.1:5001")
CHIMERA_SENTIMENT_API = os.environ.get("CHIMERA_SENTIMENT_API", "http://sentiment-agent:8004")
BETTAFISH_API_URL = os.environ.get("BETTAFISH_API_URL", "http://127.0.0.1:5000")

# Global state
latest_analysis: Optional[Dict[str, Any]] = None
simulation_active: bool = False


class OpinionAnalysisRequest(BaseModel):
    """Request public opinion analysis."""
    query: str
    platforms: list[str] = ["twitter", "reddit", "news"]
    time_range: str = "7d"  # e.g., "7d", "30d"
    max_results: int = 100


class SimulationRequest(BaseModel):
    """Request swarm simulation based on BettaFish report."""
    report_path: str
    agent_count: int = 10
    simulation_rounds: int = 3
    prediction_goal: str


class AnalysisStatus(BaseModel):
    """Status of an analysis."""
    analysis_id: str
    status: str  # pending, running, completed, failed
    progress: int  # 0-100
    report_path: Optional[str] = None
    error: Optional[str] = None


class SimulationStatus(BaseModel):
    """Status of a simulation."""
    simulation_id: str
    status: str  # pending, running, completed, failed
    progress: int  # 0-100
    prediction: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# In-memory storage for analysis/simulation status
analyses: Dict[str, AnalysisStatus] = {}
simulations: Dict[str, SimulationStatus] = {}


@app.get("/health/live")
async def liveness():
    """Liveness probe."""
    return {"status": "alive", "service": "opinion-pipeline"}


@app.get("/health/ready")
async def readiness():
    """Readiness probe."""
    # Check if BettaFish and MiroFish are accessible
    ready = True
    checks = {}

    # Check BettaFish
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BETTAFISH_API_URL}/")
            checks["bettafish"] = "accessible" if response.status_code == 200 else "error"
    except Exception as e:
        checks["bettafish"] = f"unavailable: {str(e)}"
        ready = False

    # Check MiroFish
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{MIROFISH_API_URL}/")
            checks["mirofish"] = "accessible" if response.status_code == 200 else "error"
    except Exception as e:
        checks["mirofish"] = f"unavailable: {str(e)}"
        # MiroFish might not be required for readiness

    return {"status": "ready" if ready else "not_ready", "checks": checks}


@app.get("/api/v1/status")
async def get_service_status():
    """Get overall service status."""
    return {
        "service": "opinion-pipeline",
        "latest_analysis": latest_analysis,
        "simulation_active": simulation_active,
        "bettafish_api": BETTAFISH_API_URL,
        "mirofish_api": MIROFISH_API_URL,
        "sentiment_api": CHIMERA_SENTIMENT_API
    }


@app.post("/api/v1/analyze")
async def trigger_analysis(request: OpinionAnalysisRequest, background_tasks: BackgroundTasks):
    """
    Trigger BettaFish analysis and return asynchronously.

    Process:
    1. Submit query to BettaFish
    2. Monitor progress
    3. Store generated report
    4. Return analysis ID for later retrieval
    """
    analysis_id = f"analysis_{asyncio.get_event_loop().time()}"

    # Initialize status
    analyses[analysis_id] = AnalysisStatus(
        analysis_id=analysis_id,
        status="pending",
        progress=0
    )

    # Queue background task
    background_tasks.add_task(
        run_bettafish_analysis,
        analysis_id,
        request.query,
        request.platforms,
        request.time_range
    )

    return {
        "analysis_id": analysis_id,
        "status": "pending",
        "estimated_time_minutes": 15
    }


async def run_bettafish_analysis(
    analysis_id: str,
    query: str,
    platforms: list[str],
    time_range: str
):
    """Run BettaFish analysis in background."""
    global latest_analysis

    try:
        analyses[analysis_id].status = "running"
        analyses[analysis_id].progress = 10

        # TODO: Implement actual BettaFish API call
        # This would involve:
        # 1. POST to BettaFish API with query
        # 2. Poll for completion
        # 3. Download generated report

        logger.info(f"Starting BettaFish analysis: {query}")

        # Simulate analysis (replace with actual API call)
        await asyncio.sleep(2)
        analyses[analysis_id].progress = 50
        await asyncio.sleep(2)
        analyses[analysis_id].progress = 90

        # Store result
        report_path = BETTAFISH_REPORT_PATH / f"{analysis_id}.md"
        analyses[analysis_id].status = "completed"
        analyses[analysis_id].progress = 100
        analyses[analysis_id].report_path = str(report_path)

        # Update latest analysis
        latest_analysis = {
            "analysis_id": analysis_id,
            "query": query,
            "report_path": str(report_path),
            "timestamp": asyncio.get_event_loop().time()
        }

        logger.info(f"BettaFish analysis complete: {analysis_id}")

    except Exception as e:
        logger.error(f"BettaFish analysis failed: {e}")
        analyses[analysis_id].status = "failed"
        analyses[analysis_id].error = str(e)


@app.post("/api/v1/simulate")
async def trigger_simulation(request: SimulationRequest):
    """
    Upload BettaFish report to MiroFish for swarm simulation.

    Process:
    1. Read BettaFish markdown report
    2. Submit to MiroFish as seed document
    3. Configure simulation parameters
    4. Trigger swarm simulation
    5. Return simulation ID
    """
    # Validate report exists
    report_path = Path(request.report_path)
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")

    simulation_id = f"sim_{asyncio.get_event_loop().time()}"

    # Initialize status
    simulations[simulation_id] = SimulationStatus(
        simulation_id=simulation_id,
        status="pending",
        progress=0
    )

    # Queue simulation
    asyncio.create_task(
        run_mirofish_simulation(
            simulation_id,
            report_path,
            request.agent_count,
            request.simulation_rounds,
            request.prediction_goal
        )
    )

    return {
        "simulation_id": simulation_id,
        "status": "pending",
        "estimated_time_minutes": 30
    }


async def run_mirofish_simulation(
    simulation_id: str,
    report_path: Path,
    agent_count: int,
    simulation_rounds: int,
    prediction_goal: str
):
    """Run MiroFish simulation in background."""
    global simulation_active, latest_analysis

    try:
        simulations[simulation_id].status = "running"
        simulations[simulation_id].progress = 10
        simulation_active = True

        # TODO: Implement actual MiroFish API call
        # This would involve:
        # 1. Upload report to MiroFish
        # 2. Configure simulation parameters
        # 3. Start simulation
        # 4. Poll for completion
        # 5. Retrieve prediction results

        logger.info(f"Starting MiroFish simulation: {prediction_goal}")

        # Simulate simulation (replace with actual API call)
        await asyncio.sleep(3)
        simulations[simulation_id].progress = 50
        await asyncio.sleep(3)
        simulations[simulation_id].progress = 90

        # Store result
        simulations[simulation_id].status = "completed"
        simulations[simulation_id].progress = 100
        simulations[simulation_id].prediction = {
            "goal": prediction_goal,
            "outcome": "positive",
            "confidence": 0.75
        }

        simulation_active = False
        logger.info(f"MiroFish simulation complete: {simulation_id}")

    except Exception as e:
        logger.error(f"MiroFish simulation failed: {e}")
        simulations[simulation_id].status = "failed"
        simulations[simulation_id].error = str(e)
        simulation_active = False


@app.get("/api/v1/analysis/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """Get BettaFish analysis status and results."""
    if analysis_id not in analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analyses[analysis_id]


@app.get("/api/v1/simulation/{simulation_id}")
async def get_simulation_status(simulation_id: str):
    """Get MiroFish simulation status and results."""
    if simulation_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return simulations[simulation_id]


@app.get("/api/v1/latest/sentiment")
async def get_latest_sentiment():
    """
    Get latest enriched sentiment data.

    Returns:
    - BettaFish public opinion analysis
    - MiroFish swarm predictions
    - Chimera sentiment-agent baseline
    """
    global latest_analysis

    if latest_analysis is None:
        raise HTTPException(status_code=404, detail="No analysis available")

    # Fetch current sentiment from Chimera
    chimera_sentiment = None
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{CHIMERA_SENTIMENT_API}/health")
            if response.status_code == 200:
                chimera_sentiment = "sentiment-agent accessible"
    except Exception as e:
        logger.warning(f"Could not reach sentiment-agent: {e}")
        chimera_sentiment = f"unavailable: {str(e)}"

    return {
        "latest_analysis": latest_analysis,
        "chimera_sentiment": chimera_sentiment,
        "services": {
            "bettafish": BETTAFISH_API_URL,
            "mirofish": MIROFISH_API_URL,
            "sentiment": CHIMERA_SENTIMENT_API
        }
    }


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Opinion Pipeline Orchestrator",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health/live",
            "ready": "/health/ready",
            "analyze": "/api/v1/analyze",
            "simulate": "/api/v1/simulate",
            "status": "/api/v1/status",
            "latest": "/api/v1/latest/sentiment"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8020)
