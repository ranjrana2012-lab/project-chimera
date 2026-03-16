"""ForumEngine: Multi-agent debate system for consensus building."""
from typing import List
import logging
import json
import re
import math

from .models import Argument, DebateResult
from agents.profile import AgentProfile, Demographics, BehavioralProfile, PoliticalLeaning
from simulation.llm_router import TieredLLMRouter, LLMBackend

logger = logging.getLogger(__name__)


class ForumEngine:
    """
    Multi-agent debate system that produces consensus through structured discussion.

    Implements the ForumEngine pattern from BettaFish for robust report generation.
    """

    def __init__(self):
        self.router = TieredLLMRouter()

    async def debate_topic(
        self,
        topic: str,
        participants: List[AgentProfile],
        rounds: int = 3
    ) -> DebateResult:
        """
        Run multi-round debate among participants.

        Round structure:
        - Round 1: Present initial positions
        - Round 2: Critique and cross-validate
        - Round 3: Refine based on feedback

        Args:
            topic: The topic to debate
            participants: List of agent profiles participating in the debate
            rounds: Number of debate rounds (default: 3)

        Returns:
            DebateResult containing all arguments, consensus score, and summary
        """
        all_arguments: List[Argument] = []

        for round_num in range(rounds):
            logger.info(f"Starting debate round {round_num + 1}/{rounds}")

            for agent in participants:
                # Get context from previous rounds
                context = self._build_context(topic, all_arguments, round_num, agent)

                # Generate agent's argument for this round
                try:
                    argument = await self._generate_argument(
                        agent=agent,
                        topic=topic,
                        context=context,
                        round_num=round_num
                    )
                    all_arguments.append(argument)
                    logger.debug(f"Generated argument from {agent.id} for round {round_num + 1}")
                except Exception as e:
                    logger.error(f"Failed to generate argument for {agent.id}: {e}")
                    # Continue with other agents even if one fails
                    continue

        # Calculate consensus and confidence
        consensus = self.calculate_consensus(all_arguments)
        confidence = self.calculate_confidence(all_arguments)

        # Generate summary with error handling
        try:
            summary = await self._generate_summary(topic, all_arguments)
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            summary = f"Debate on '{topic}' had {len(all_arguments)} arguments."

        return DebateResult(
            topic=topic,
            arguments=all_arguments,
            consensus_score=consensus,
            confidence_interval=self._calculate_interval(confidence, len(all_arguments)),
            summary=summary
        )

    def _build_context(
        self,
        topic: str,
        previous_args: List[Argument],
        round_num: int,
        agent: AgentProfile
    ) -> str:
        """
        Build debate context for agent.

        Args:
            topic: The debate topic
            previous_args: Arguments from previous rounds
            round_num: Current round number
            agent: The agent who will receive this context

        Returns:
            Formatted context string
        """
        if round_num == 0:
            return f"""Topic: {topic}

You are participating in the first round of a debate.
Please present your initial position on this topic.

Your persona: {agent.mbti.value}
Your political leaning: {agent.political_leaning.value}
Your behavioral traits:
- Openness: {agent.behavioral.openness}
- Conscientiousness: {agent.behavioral.conscientiousness}
- Extraversion: {agent.behavioral.extraversion}
- Agreeableness: {agent.behavioral.agreeableness}
- Neuroticism: {agent.behavioral.neuroticism}

Present your argument (1-2 sentences) responding as JSON with fields:
{{
  "content": "your argument",
  "stance": 0.9,  // -1.0 (oppose) to 1.0 (support)
  "reasoning": "brief explanation"
}}"""

        # Build context from previous arguments
        context = f"""Topic: {topic}

You are in round {round_num + 1} of the debate.

Your persona: {agent.mbti.value}
Your political leaning: {agent.political_leaning.value}

Previous arguments from other participants:
"""

        # Show a subset of previous arguments to avoid context overflow
        sample_size = max(1, len(previous_args) // (round_num + 1))
        for arg in previous_args[-sample_size:]:
            stance_desc = "supports" if arg.stance > 0.3 else "opposes" if arg.stance < -0.3 else "neutral on"
            context += f"- {arg.agent_id} {stance_desc} the topic: {arg.content}\n"

        context += f"""
Please respond to the previous arguments (1-2 sentences).
You may:
- Reinforce your position
- Critique opposing views
- Find common ground
- Refine your stance

Respond as JSON with fields:
{{
  "content": "your argument",
  "stance": 0.9,  // -1.0 (oppose) to 1.0 (support)
  "reasoning": "brief explanation"
}}"""

        return context

    async def _generate_argument(
        self,
        agent: AgentProfile,
        topic: str,
        context: str,
        round_num: int
    ) -> Argument:
        """
        Generate argument from agent using LLM.

        Args:
            agent: The agent profile generating the argument
            topic: The debate topic
            context: The debate context including previous arguments
            round_num: Current round number

        Returns:
            Argument object with content, stance, and reasoning
        """
        prompt = context

        # Call LLM via router with dynamic backend selection
        response = await self.router.call_llm(
            prompt=prompt
            # Let router use its tiered logic for backend selection
        )

        # Parse JSON response
        data = self._parse_json_response(response)

        # Validate stance is in valid range
        stance = float(data.get("stance", 0.0))
        stance = max(-1.0, min(1.0, stance))

        return Argument(
            agent_id=agent.id,
            content=data.get("content", ""),
            stance=stance,
            reasoning=data.get("reasoning", "")
        )

    def _parse_json_response(self, response: str) -> dict:
        """
        Parse JSON from LLM response, handle markdown code blocks.

        Args:
            response: Raw LLM response string

        Returns:
            Parsed dictionary with content, stance, and reasoning
        """
        # Try raw JSON first
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try extracting from generic code block
        match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Fallback: try to find JSON-like structure
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass

        logger.warning(f"Failed to parse JSON from LLM response: {response[:200]}")
        return {"content": response, "stance": 0.0, "reasoning": ""}

    def calculate_consensus(self, arguments: List[Argument]) -> float:
        """
        Calculate consensus score from arguments (0-1).

        Higher score indicates more agreement among participants.

        Args:
            arguments: List of arguments from the debate

        Returns:
            Consensus score between 0.0 (no consensus) and 1.0 (full consensus)
        """
        if not arguments:
            return 0.0

        # Average absolute stance indicates agreement level
        # If everyone has similar stance direction, consensus is high
        stances = [arg.stance for arg in arguments]
        avg_stance = sum(stances) / len(stances)

        # Variance from mean indicates disagreement
        variance = sum((s - avg_stance) ** 2 for s in stances) / len(stances)

        # Lower variance = higher consensus (invert)
        consensus = 1.0 / (1.0 + variance)
        return consensus

    def calculate_confidence(self, arguments: List[Argument]) -> float:
        """
        Measure agreement level among agents (0-1).

        Higher confidence = agents agree more. Based on pairwise stance comparison.

        Args:
            arguments: List of arguments to analyze

        Returns:
            Confidence score between 0.0 (no agreement) and 1.0 (full agreement)
        """
        if len(arguments) < 2:
            return 0.5

        # Calculate pairwise agreement
        agreements = 0
        total_pairs = 0

        for i, arg1 in enumerate(arguments):
            for arg2 in arguments[i+1:]:
                # Agreement = 1 - absolute difference in stance
                agreement = 1.0 - abs(arg1.stance - arg2.stance)
                agreements += agreement
                total_pairs += 1

        return agreements / total_pairs if total_pairs > 0 else 0.5

    def _calculate_interval(
        self,
        confidence: float,
        n: int
    ) -> tuple[float, float]:
        """
        Calculate confidence interval using Wilson score approximation.

        Args:
            confidence: Point estimate of confidence
            n: Sample size (number of arguments)

        Returns:
            Tuple of (lower_bound, upper_bound) for confidence interval
        """
        if n < 2:
            return (0.0, 1.0)

        # Simple interval based on confidence and sample size
        # As n increases, interval narrows
        margin = 1.96 / math.sqrt(n) * (1 - confidence)
        lower = max(0.0, confidence - margin)
        upper = min(1.0, confidence + margin)
        return (lower, upper)

    async def _generate_summary(
        self,
        topic: str,
        arguments: List[Argument]
    ) -> str:
        """
        Generate debate summary.

        Args:
            topic: The debate topic
            arguments: All arguments from the debate

        Returns:
            Summary string describing the debate outcome
        """
        if not arguments:
            return f"No arguments were generated for the topic '{topic}'."

        # Count positions
        support = sum(1 for a in arguments if a.stance > 0.3)
        oppose = sum(1 for a in arguments if a.stance < -0.3)
        neutral = len(arguments) - support - oppose

        consensus = self.calculate_consensus(arguments)

        summary_parts = [
            f"Debate on '{topic}' involved {len(arguments)} arguments across {len(set(a.agent_id for a in arguments))} participants.",
            f"{support} supported, {oppose} opposed, {neutral} neutral.",
            f"Final consensus score: {consensus:.2f}"
        ]

        return " ".join(summary_parts)
