"""GSD Orchestrator - Goal-Setting and Delegation system for autonomous agent orchestration."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


# Exceptions
class PlanRejectedError(Exception):
    """Raised when a plan is rejected during the planning phase."""

    pass


class SpecViolationError(Exception):
    """Raised when code does not meet specification requirements."""

    pass


class QualityViolationError(Exception):
    """Raised when code does not meet quality standards."""

    pass


# Dataclasses
@dataclass
class Requirements:
    """Captures user requirements and constraints."""

    goal: str
    constraints: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Task:
    """A single task in the execution plan."""

    id: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"


@dataclass
class Plan:
    """Implementation plan with tasks and estimates."""

    tasks: List[Task]
    estimated_hours: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Result:
    """Result of a single task execution."""

    task_id: str
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class Results:
    """Aggregate results from plan execution."""

    results: List[Result] = field(default_factory=list)
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    total_duration_seconds: float = 0.0


class GSDOrchestrator:
    """
    Goal-Setting and Delegation Orchestrator.

    Implements the Discuss→Plan→Execute→Verify lifecycle for
    autonomous agent orchestration.
    """

    def __init__(self):
        """Initialize the GSD Orchestrator."""
        self.requirements: Optional[Requirements] = None
        self.plan: Optional[Plan] = None
        self.results: Optional[Results] = None

    def discuss_phase(self, user_input: str) -> Requirements:
        """
        Extract requirements from user input.

        Args:
            user_input: Natural language description of user goals

        Returns:
            Requirements object with goal, constraints, and acceptance criteria
        """
        # This is a simplified implementation
        # In production, this would use LLM to extract structured requirements
        requirements = Requirements(
            goal=user_input,
            constraints=[],
            acceptance_criteria=[]
        )
        self.requirements = requirements
        return requirements

    def plan_phase(self, requirements: Requirements) -> Plan:
        """
        Create implementation plan from requirements.

        Args:
            requirements: Requirements object

        Returns:
            Plan with tasks and estimates

        Raises:
            PlanRejectedError: If plan cannot be created
        """
        # This is a simplified implementation
        # In production, this would use LLM to create detailed plan
        task = Task(
            id="1",
            description=f"Implement: {requirements.goal}",
            dependencies=[]
        )
        plan = Plan(
            tasks=[task],
            estimated_hours=1.0
        )
        self.plan = plan
        return plan

    def execute_phase(self, plan: Plan) -> Results:
        """
        Execute plan with verification.

        Args:
            plan: Plan to execute

        Returns:
            Results from execution
        """
        results = Results()
        results.total_tasks = len(plan.tasks)

        for task in plan.tasks:
            # Execute task (simplified)
            result = Result(
                task_id=task.id,
                success=True,
                output=f"Completed: {task.description}",
                duration_seconds=1.0
            )
            results.results.append(result)
            results.successful_tasks += 1
            results.total_duration_seconds += result.duration_seconds

        self.results = results
        return results

    async def verify_phase(
        self,
        results: Results,
        requirements: Requirements,
        plan: Plan
    ) -> Dict[str, Any]:
        """
        VMAO Verify phase: Check execution results against requirements.

        This implements the Verify component of the Plan-Execute-Verify-Replan cycle.

        Args:
            results: Execution results to verify
            requirements: Original requirements
            plan: Plan that was executed

        Returns:
            Verification report with status and suggestions
        """
        try:
            from vmao_verifier import get_verifier, VerificationStatus

            verifier = get_verifier()

            # Verify overall results
            verification_report = {
                "total_tasks": results.total_tasks,
                "successful_tasks": results.successful_tasks,
                "failed_tasks": results.failed_tasks,
                "overall_status": "passed",
                "issues": [],
                "suggestions": [],
                "task_verifications": []
            }

            # Check success rate
            success_rate = results.successful_tasks / results.total_tasks if results.total_tasks > 0 else 0
            if success_rate < 0.8:
                verification_report["overall_status"] = "failed"
                verification_report["issues"].append(
                    f"Success rate ({success_rate:.1%}) below threshold (80%)"
                )

            # Verify individual task results
            for result in results.results:
                try:
                    # Import here to avoid circular dependency
                    from vmao_verifier import VerificationResult

                    task_verification = await verifier.verify_execution_result(
                        result=result,
                        requirements=requirements,
                        plan=plan
                    )

                    verification_report["task_verifications"].append({
                        "task_id": result.task_id,
                        "status": task_verification.status.value,
                        "confidence": task_verification.confidence,
                        "issues": task_verification.issues,
                        "suggestions": task_verification.suggestions
                    })

                    # Collect issues and suggestions
                    verification_report["issues"].extend(task_verification.issues)
                    verification_report["suggestions"].extend(task_verification.suggestions)

                    # Update overall status if needed
                    if task_verification.status == VerificationStatus.FAILED:
                        verification_report["overall_status"] = "failed"
                    elif task_verification.status == VerificationStatus.NEEDS_REPLAN:
                        if verification_report["overall_status"] == "passed":
                            verification_report["overall_status"] = "needs_replan"

                except Exception as e:
                    logger.error(f"Error verifying task {result.task_id}: {e}")
                    verification_report["issues"].append(f"Task {result.task_id} verification failed: {str(e)}")

            logger.info(
                f"Verification phase complete: {verification_report['overall_status']} "
                f"({results.successful_tasks}/{results.total_tasks} tasks passed)"
            )

            return verification_report

        except ImportError:
            logger.warning("VMAO verifier not available, skipping verification")
            return {
                "total_tasks": results.total_tasks,
                "successful_tasks": results.successful_tasks,
                "failed_tasks": results.failed_tasks,
                "overall_status": "skipped",
                "issues": ["VMAO verifier not available"],
                "suggestions": [],
                "task_verifications": []
            }

    async def execute_with_verification(
        self,
        plan: Plan,
        requirements: Requirements
    ) -> tuple[Results, Dict[str, Any]]:
        """
        Execute plan with VMAO-style verification.

        Implements Execute→Verify cycle with potential replanning.

        Args:
            plan: Plan to execute
            requirements: Requirements to verify against

        Returns:
            Tuple of (Results, VerificationReport)
        """
        # Execute phase
        results = self.execute_phase(plan)

        # Verify phase
        verification_report = await self.verify_phase(results, requirements, plan)

        return results, verification_report

    def verify_spec_compliance(self, code: str, requirements: Requirements) -> bool:
        """
        Verify code meets specification requirements.

        Args:
            code: Code to verify
            requirements: Requirements to check against

        Returns:
            True if compliant

        Raises:
            SpecViolationError: If code does not meet spec
        """
        # Simplified implementation
        # In production, would use LLM to verify compliance
        if not code:
            raise SpecViolationError("Code is empty or None")
        return True

    def verify_code_quality(self, code: str) -> bool:
        """
        Verify code meets quality standards.

        Args:
            code: Code to verify

        Returns:
            True if quality standards met

        Raises:
            QualityViolationError: If code does not meet quality standards
        """
        # Simplified implementation
        # In production, would run linters, type checkers, etc.
        if not code:
            raise QualityViolationError("Code is empty or None")
        return True

    def write_requirements(self, requirements: Requirements, filepath: str) -> None:
        """
        Write requirements to external state file.

        Args:
            requirements: Requirements to write
            filepath: Path to write REQUIREMENTS.md

        Raises:
            IOError: If file cannot be written
        """
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)

            content = f"""# Requirements

## Goal
{requirements.goal}

## Constraints
"""
            for constraint in requirements.constraints:
                content += f"- {constraint}\n"

            content += "\n## Acceptance Criteria\n"
            for criteria in requirements.acceptance_criteria:
                content += f"- {criteria}\n"

            content += f"\n*Generated: {requirements.timestamp}*\n"

            path.write_text(content)
        except (OSError, PermissionError) as e:
            raise IOError(f"Failed to write requirements to {filepath}: {e}")

    def write_plan(self, plan: Plan, filepath: str) -> None:
        """
        Write plan to external state file.

        Args:
            plan: Plan to write
            filepath: Path to write PLAN.md

        Raises:
            IOError: If file cannot be written
        """
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)

            content = f"""# Implementation Plan

## Overview
- Total Tasks: {len(plan.tasks)}
- Estimated Hours: {plan.estimated_hours}

## Tasks
"""
            for task in plan.tasks:
                deps = ", ".join(task.dependencies) if task.dependencies else "None"
                content += f"""
### Task {task.id}: {task.description}
- Status: {task.status}
- Dependencies: {deps}
"""

            content += f"\n*Generated: {plan.timestamp}*\n"

            path.write_text(content)
        except (OSError, PermissionError) as e:
            raise IOError(f"Failed to write plan to {filepath}: {e}")
