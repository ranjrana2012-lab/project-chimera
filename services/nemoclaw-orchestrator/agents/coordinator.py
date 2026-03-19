# services/nemoclaw-orchestrator/agents/coordinator.py
import asyncio
from typing import Dict, Any, Optional
import logging

from policy.engine import PolicyEngine, PolicyAction, PolicyViolationError
from llm.privacy_router import PrivacyRouter, RouterConfig

from .adapters import (
    AgentAdapter,
    SceneSpeakAdapter,
    SentimentAdapter,
    CaptioningAdapter,
    BSLAdapter,
    LightingSoundMusicAdapter,
    SafetyFilterAdapter,
    MusicGenerationAdapter,
    AutonomousAdapter
)

logger = logging.getLogger(__name__)


class AgentCoordinator:
    """
    Central coordinator for all Project Chimera agents

    Manages communication with 8 existing agents through OpenShell guardrails:
    - LLM agents: SceneSpeak, Autonomous (routed through PrivacyRouter)
    - Direct agents: Sentiment, Captioning, BSL, LightingSoundMusic, SafetyFilter, MusicGeneration

    Flow for each agent call:
    1. Policy check (ALLOW/DENY/SANITIZE)
    2. Sanitize input (if SANITIZE)
    3. Call agent
    4. Filter output
    """

    # Agent name mappings
    AGENT_NAMES = {
        "scenespeak": "SceneSpeak",
        "sentiment": "Sentiment",
        "captioning": "Captioning",
        "bsl": "BSL",
        "lighting-sound-music": "LightingSoundMusic",
        "safety-filter": "SafetyFilter",
        "music-generation": "MusicGeneration",
        "autonomous": "Autonomous"
    }

    def __init__(self, settings, policy_engine: PolicyEngine):
        """
        Initialize AgentCoordinator

        Args:
            settings: Application settings with agent URLs
            policy_engine: Policy engine for input/output filtering
        """
        self.settings = settings
        self.policy_engine = policy_engine

        # Initialize PrivacyRouter for LLM-dependent agents
        router_config = RouterConfig(
            dgx_endpoint=settings.dgx_endpoint,
            local_ratio=settings.local_ratio,
            cloud_fallback_enabled=settings.cloud_fallback_enabled,
            nemotron_model=settings.nemotron_model
        )
        self.privacy_router = PrivacyRouter(router_config)

        # Initialize all adapters
        self.adapters: Dict[str, AgentAdapter] = self._initialize_adapters()

        logger.info(f"AgentCoordinator initialized with {len(self.adapters)} adapters")

    def _initialize_adapters(self) -> Dict[str, AgentAdapter]:
        """Initialize all agent adapters"""
        adapters = {}

        # LLM-dependent agents (use PrivacyRouter)
        adapters["scenespeak"] = SceneSpeakAdapter(
            self.settings.scenespeak_agent_url,
            self.privacy_router
        )
        adapters["autonomous"] = AutonomousAdapter(
            self.settings.autonomous_agent_url,
            self.privacy_router
        )

        # Direct HTTP agents
        adapters["sentiment"] = SentimentAdapter(
            self.settings.sentiment_agent_url
        )
        adapters["captioning"] = CaptioningAdapter(
            self.settings.captioning_agent_url
        )
        adapters["bsl"] = BSLAdapter(
            self.settings.bsl_agent_url
        )
        adapters["lighting-sound-music"] = LightingSoundMusicAdapter(
            self.settings.lighting_sound_music_url
        )
        adapters["safety-filter"] = SafetyFilterAdapter(
            self.settings.safety_filter_url
        )
        adapters["music-generation"] = MusicGenerationAdapter(
            self.settings.music_generation_url
        )

        return adapters

    def call_agent(
        self,
        agent: str,
        skill: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call an agent with policy filtering

        Args:
            agent: Agent name (e.g., "scenespeak", "sentiment")
            skill: Skill/method to call
            input_data: Input parameters for the skill

        Returns:
            Agent response (filtered through policy)

        Raises:
            PolicyViolationError: If policy check denies the request
            ValueError: If agent is unknown
        """
        # Validate agent
        if agent not in self.adapters:
            raise ValueError(f"Unknown agent: {agent}. Available agents: {list(self.adapters.keys())}")

        adapter = self.adapters[agent]

        # Step 1: Policy check
        policy_result = self.policy_engine.check_input(
            agent=agent,
            skill=skill,
            input_data=input_data
        )

        logger.debug(f"Policy check for {agent}.{skill}: {policy_result.action.value} - {policy_result.reason}")

        # Handle DENY
        if policy_result.action == PolicyAction.DENY:
            raise PolicyViolationError(
                message=f"Request denied by policy: {policy_result.reason}",
                code="POLICY_DENY"
            )

        # Step 2: Sanitize input (if needed)
        processed_input = input_data
        if policy_result.action == PolicyAction.SANITIZE:
            processed_input = asyncio.run(self.policy_engine.sanitize_input(input_data))
            logger.debug(f"Input sanitized: {policy_result.reason}")

        # Step 3: Call agent
        try:
            response = asyncio.run(adapter.execute(skill, processed_input))
        except Exception as e:
            logger.error(f"Agent {agent} execution failed: {e}")
            raise

        # Step 4: Filter output
        filtered_response = asyncio.run(self.policy_engine.filter_output(agent, response))

        return filtered_response

    def get_adapter(self, agent: str) -> AgentAdapter:
        """
        Get an adapter by name

        Args:
            agent: Agent name

        Returns:
            AgentAdapter instance

        Raises:
            ValueError: If agent is unknown
        """
        if agent not in self.adapters:
            raise ValueError(f"Unknown agent: {agent}")
        return self.adapters[agent]

    def list_agents(self) -> list[str]:
        """
        List all available agents

        Returns:
            List of agent names
        """
        return list(self.adapters.keys())

    def close(self):
        """Clean up resources"""
        if hasattr(self, 'privacy_router'):
            self.privacy_router.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
