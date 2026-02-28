"""Mutation testing integration with mutmut."""
import asyncio
from typing import Dict, Any

class MutationTestRunner:
    """Run mutation tests using mutmut."""

    def __init__(self, baseline_branch: str = "main"):
        self.baseline_branch = baseline_branch

    async def run_mutation_tests(
        self,
        service: str,
        threshold: float = 95.0
    ) -> Dict[str, Any]:
        """Run mutation tests for a service."""

        # Run mutmut
        proc = await asyncio.create_subprocess_exec(
            "mutmut",
            "run",
            "--paths-to-mutate=services/" + service,
            f"--threshold={threshold}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()

        # Parse results
        output = stdout.decode()

        # Extract mutation score
        # Look for line like "Mutation score: 98.23%"
        score = 0.0
        for line in output.split("\n"):
            if "Mutation score:" in line:
                score_str = line.split(":")[-1].strip().replace("%", "")
                try:
                    score = float(score_str)
                except ValueError:
                    pass
                break

        return {
            "service": service,
            "score": score,
            "threshold_met": score >= threshold,
            "output": output
        }
