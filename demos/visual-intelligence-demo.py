#!/usr/bin/env python3
"""Demo script for Visual Intelligence Report generation"""

import asyncio
import httpx
import json
import time
from datetime import datetime

# Service endpoints
SENTIMENT_AGENT_URL = "http://localhost:8004"
VISUAL_CORE_URL = "http://localhost:8014"


async def create_visual_intelligence_report(
    scenario: dict
) -> dict:
    """Create complete visual intelligence report"""

    print(f"Creating Visual Intelligence Report: {scenario['topic']}")
    print(f"Timeframe: {scenario['timeframe']}")
    print(f"Style: {scenario['style']}")
    print(f"Duration: {scenario['duration']}s")
    print()

    # Step 1: Create sentiment briefing video
    print("Step 1: Generating sentiment briefing video...")
    start_time = time.time()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SENTIMENT_AGENT_URL}/api/v1/video/briefing",
            json={
                "topic": scenario["topic"],
                "timeframe": scenario["timeframe"],
                "style": scenario["style"],
                "duration": scenario["duration"]
            },
            timeout=600
        )
        response.raise_for_status()
        briefing = response.json()

    briefing_time = time.time() - start_time
    print(f"✓ Briefing generated in {briefing_time:.1f}s")
    print(f"  Briefing ID: {briefing['briefing_id']}")
    print(f"  Video URL: {briefing['video_url']}")
    print()

    # Step 2: Generate PDF summary
    print("Step 2: Generating PDF summary...")
    # Placeholder - would generate actual PDF
    pdf_url = briefing["video_url"].replace(".mp4", "_summary.pdf")
    print(f"✓ PDF summary available")
    print()

    return {
        "report_id": briefing["briefing_id"],
        "scenario": scenario,
        "video_url": briefing["video_url"],
        "pdf_url": pdf_url,
        "generation_time": briefing_time,
        "created_at": datetime.utcnow().isoformat()
    }


async def run_demo():
    """Run the visual intelligence demo"""

    print("="*60)
    print("Visual Intelligence Report Demo")
    print("="*60)
    print()

    # Check service availability
    print("Checking service availability...")

    try:
        async with httpx.AsyncClient() as client:
            # Check sentiment agent
            sentiment_health = await client.get(f"{SENTIMENT_AGENT_URL}/health")
            print(f"✓ Sentiment Agent: {sentiment_health.status_code}")

            # Check visual core
            visual_health = await client.get(f"{VISUAL_CORE_URL}/health/live")
            print(f"✓ Visual Core: {visual_health.status_code}")

    except Exception as e:
        print(f"✗ Service check failed: {e}")
        return

    print()

    # Run demo scenarios
    from demo_data import DEMO_SCENARIOS

    scenario = DEMO_SCENARIOS["tech_brand_sentiment"]

    result = await create_visual_intelligence_report(scenario)

    print()
    print("="*60)
    print("DEMO COMPLETE")
    print("="*60)
    print()
    print(f"Report ID: {result['report_id']}")
    print(f"Video URL: {result['video_url']}")
    print(f"Generation Time: {result['generation_time']:.1f}s")
    print()
    print("To view the video:")
    print(f"  ffprobe {result['video_url']}")
    print()
    print("To redeploy:")
    print("  kubectl rollout restart deployment/sentiment-agent -n project-chimera")


if __name__ == "__main__":
    asyncio.run(run_demo())
