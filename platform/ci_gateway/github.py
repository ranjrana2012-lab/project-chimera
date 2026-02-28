"""GitHub webhook integration."""
import hmac
import hashlib
from typing import Optional
import httpx


async def verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature."""
    if not signature:
        return False

    hash_algorithm, github_signature = signature.split("=", 1)
    if hash_algorithm != "sha256":
        return False

    mac = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    )

    expected_signature = mac.hexdigest()
    return hmac.compare_digest(expected_signature, github_signature)


class GitHubClient:
    """Client for GitHub API interactions."""

    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

    async def update_commit_status(
        self,
        repo: str,
        sha: str,
        status: str,
        description: str,
        target_url: Optional[str] = None
    ):
        """Update commit status in GitHub."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/repos/{repo}/statuses/{sha}",
                json={
                    "state": status,
                    "description": description,
                    "target_url": target_url,
                    "context": "chimera-quality-platform"
                },
                headers=self.headers
            )
            response.raise_for_status()

    async def create_pull_request_comment(
        self,
        repo: str,
        pr_number: int,
        body: str
    ):
        """Create a comment on a pull request."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/repos/{repo}/issues/{pr_number}/comments",
                json={"body": body},
                headers=self.headers
            )
            response.raise_for_status()

    async def get_changed_files(
        self,
        repo: str,
        base: str,
        head: str
    ) -> list[str]:
        """Get list of changed files between two commits."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{repo}/compare/{base}...{head}",
                headers=self.headers
            )
            response.raise_for_status()

            data = response.json()
            return [file["filename"] for file in data.get("files", [])]
