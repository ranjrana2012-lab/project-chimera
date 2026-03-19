# services/nemoclaw-orchestrator/agents/coordinator.py
import asyncio
from typing import Dict, Any, Optional
import logging
import httpx

from policy.engine import PolicyEngine, PolicyAction, PolicyViolationError
from llm.privacy_router import PrivacyRouter, RouterConfig
from resilience.retry import ResilientAgentCaller, RetryConfig
from resilience.circuit_breaker import CircuitBreaker, CircuitBreakerConfig

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

        # Initialize resilience patterns
        self.retry_config = RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
            jitter=True,
            fallback_mode="graceful"
        )
        self.circuit_config = CircuitBreakerConfig(
            failure_threshold=5,
            timeout=60.0,
            success_threshold=2,
            call_timeout=30.0
        )

        # Create circuit breakers for each agent
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        for agent_name in self.AGENT_NAMES.keys():
            self.circuit_breakers[agent_name] = CircuitBreaker(
                service_name=agent_name,
                config=self.circuit_config
            )

        # Create retry callers for each agent
        self.retry_callers: Dict[str, ResilientAgentCaller] = {}
        for agent_name, display_name in self.AGENT_NAMES.items():
            agent_url = getattr(settings, f"{agent_name}_agent_url", None)
            if agent_url:
                self.retry_callers[agent_name] = ResilientAgentCaller(
                    agent_name=agent_name,
                    agent_url=agent_url,
                    retry_config=self.retry_config,
                    circuit_config=self.circuit_config
                )

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

    async def _call_agent_http(
        self,
        agent_name: str,
        agent_url: str,
        skill: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make HTTP call to agent with resilience patterns

        Args:
            agent_name: Name of the agent
            agent_url: URL of the agent service
            skill: Skill/method to call
            input_data: Input parameters

        Returns:
            Agent response

        Raises:
            AgentUnavailableError: If agent is unavailable
            CircuitBreakerOpenError: If circuit breaker is open
            RetryExhaustedError: If all retries exhausted
        """
        async def _http_call():
            """Internal async HTTP call"""
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{agent_url}/api/v1/{skill}",
                    json=input_data
                )
                response.raise_for_status()
                return response.json()

        # Use circuit breaker and retry
        circuit_breaker = self.circuit_breakers.get(agent_name)
        if not circuit_breaker:
            logger.warning(f"No circuit breaker for {agent_name}, making direct call")
            return await _http_call()

        # Check circuit state
        if circuit_breaker.state == "open":
            from errors.exceptions import CircuitBreakerOpenError
            raise CircuitBreakerOpenError(
                message=f"Circuit breaker is open for agent '{agent_name}'",
                service=agent_name,
                failure_count=circuit_breaker.stats.failure_count
            )

        # Make the call with retry logic
        try:
            result = await _http_call()
            circuit_breaker._record_success()
            return result
        except Exception as e:
            circuit_breaker._record_failure()

            # Retry logic
            retry_caller = self.retry_callers.get(agent_name)
            if retry_caller:
                return await retry_caller.call_with_retry_async(
                    _http_call
                )
            raise

    async def call_agent(
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
            processed_input = await self.policy_engine.sanitize_input(input_data)
            logger.debug(f"Input sanitized: {policy_result.reason}")

        # Step 3: Call agent with resilience patterns
        try:
            # For non-LLM agents, use circuit breaker and retry
            if not adapter.requires_llm:
                circuit_breaker = self.circuit_breakers.get(agent)
                if circuit_breaker:
                    # Check circuit state
                    if circuit_breaker.state.value == "open":
                        from errors.exceptions import CircuitBreakerOpenError
                        raise CircuitBreakerOpenError(
                            message=f"Circuit breaker is open for agent '{agent}'",
                            service=agent,
                            failure_count=circuit_breaker.stats.failure_count
                        )

                    # Execute with circuit breaker tracking
                    try:
                        response = await adapter.execute(skill, processed_input)
                        circuit_breaker._record_success()
                    except Exception as e:
                        circuit_breaker._record_failure()

                        # Use retry logic for transient failures
                        if self._is_retryable_error(e):
                            retry_caller = self.retry_callers.get(agent)
                            if retry_caller:
                                logger.warning(f"Retrying {agent} after error: {e}")
                                response = await retry_caller.call_with_retry_async(
                                    adapter.execute,
                                    skill,
                                    processed_input
                                )
                            else:
                                raise
                        else:
                            raise
                else:
                    # No circuit breaker, direct call
                    response = await adapter.execute(skill, processed_input)
            else:
                # LLM agents go through PrivacyRouter which has its own resilience
                response = await adapter.execute(skill, processed_input)
        except Exception as e:
            logger.error(f"Agent {agent} execution failed: {e}")
            raise

        # Step 4: Filter output
        filtered_response = await self.policy_engine.filter_output(agent, response)

        return filtered_response

    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Check if an error is retryable

        Args:
            error: Exception to check

        Returns:
            True if error should trigger a retry
        """
        from errors.exceptions import AgentUnavailableError
        import httpx

        return isinstance(error, (
            ConnectionError,
            TimeoutError,
            AgentUnavailableError,
            httpx.HTTPError,
            httpx.ConnectError,
            httpx.TimeoutException
        ))

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

    async def close(self):
        """Clean up resources"""
        # Close all adapters
        for adapter in self.adapters.values():
            await adapter.close()

        # Close privacy router
        if hasattr(self, 'privacy_router'):
            self.privacy_router.close()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
