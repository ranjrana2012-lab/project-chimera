"""CI/CD Gateway FastAPI application."""
from typing import Optional
from fastapi import FastAPI, Request, BackgroundTasks, Header, HTTPException
from ci_gateway.github import GitHubClient, verify_github_signature
from shared.config import settings

ci_gateway_app = FastAPI(
    title="Chimera CI/CD Gateway",
    description="Webhook integration for GitHub and GitLab",
    version="0.1.0"
)

github_client = GitHubClient(settings.github_token or "test-token")


@ci_gateway_app.post("/webhooks/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature: Optional[str] = Header(None)
):
    """Handle GitHub webhook events."""

    # Get raw payload
    payload = await request.body()

    # Verify signature (skip in test mode)
    import os
    if os.getenv("TESTING") != "true":
        if settings.github_webhook_secret:
            if not await verify_github_signature(payload, x_hub_signature or "", settings.github_webhook_secret):
                raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse event
    import json
    event_data = json.loads(payload.decode())
    event_type = request.headers.get("X-GitHub-Event", "")

    if event_type == "push":
        await handle_push(event_data)
    elif event_type == "pull_request":
        await handle_pull_request(event_data)

    return {"status": "received", "message": "Processing webhook"}


async def handle_push(event: dict):
    """Handle push event to main branch."""
    commit_sha = event["after"]
    ref = event["ref"]
    repo = event["repository"]["full_name"]

    # TODO: Start test run via orchestrator
    print(f"Push to {ref}, commit {commit_sha} in repo {repo}")


async def handle_pull_request(event: dict):
    """Handle pull request event with affected test selection."""
    pr = event["pull_request"]
    repo = event["repository"]["full_name"]

    # TODO: Start test run with affected tests only
    print(f"PR #{pr['number']} in repo {repo}")


@ci_gateway_app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ci-gateway"}
