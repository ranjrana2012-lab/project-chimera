# services/nemoclaw-orchestrator/agents/adapters.py
import httpx
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

from llm.privacy_router import PrivacyRouter, RouterConfig

logger = logging.getLogger(__name__)


class AgentAdapter(ABC):
    """Base adapter for all agents"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.Client(timeout=30.0)

    @property
    @abstractmethod
    def requires_llm(self) -> bool:
        """Whether this agent requires LLM routing"""
        pass

    @abstractmethod
    async def execute(self, skill: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a skill on this agent"""
        pass

    def __del__(self):
        """Clean up HTTP client"""
        if hasattr(self, 'client'):
            self.client.close()


class SceneSpeakAdapter(AgentAdapter):
    """Adapter for SceneSpeak agent (LLM-based)"""

    def __init__(self, base_url: str, privacy_router: PrivacyRouter):
        super().__init__(base_url)
        self.privacy_router = privacy_router

    @property
    def requires_llm(self) -> bool:
        return True

    async def execute(self, skill: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SceneSpeak skill using LLM"""
        prompt = input_data.get('prompt', '')
        max_tokens = input_data.get('max_tokens', 512)
        temperature = input_data.get('temperature', 0.7)

        try:
            # Route through PrivacyRouter
            response = self.privacy_router.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return {
                "text": response.get("text", ""),
                "backend": response.get("backend", "unknown"),
                "model": response.get("model", "")
            }
        except Exception as e:
            logger.error(f"SceneSpeak execution failed: {e}")
            raise


class SentimentAdapter(AgentAdapter):
    """Adapter for Sentiment agent (direct HTTP)"""

    def __init__(self, base_url: str):
        super().__init__(base_url)

    @property
    def requires_llm(self) -> bool:
        return False

    async def execute(self, skill: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute sentiment analysis via HTTP"""
        try:
            response = self.client.post(
                f"{self.base_url}/api/v1/{skill}",
                json=input_data
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Sentiment agent HTTP error: {e}")
            raise


class CaptioningAdapter(AgentAdapter):
    """Adapter for Captioning agent (direct HTTP)"""

    def __init__(self, base_url: str):
        super().__init__(base_url)

    @property
    def requires_llm(self) -> bool:
        return False

    async def execute(self, skill: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute captioning via HTTP"""
        try:
            response = self.client.post(
                f"{self.base_url}/api/v1/{skill}",
                json=input_data
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Captioning agent HTTP error: {e}")
            raise


class BSLAdapter(AgentAdapter):
    """Adapter for BSL (British Sign Language) agent (direct HTTP)"""

    def __init__(self, base_url: str):
        super().__init__(base_url)

    @property
    def requires_llm(self) -> bool:
        return False

    async def execute(self, skill: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute BSL translation via HTTP"""
        try:
            response = self.client.post(
                f"{self.base_url}/api/v1/{skill}",
                json=input_data
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"BSL agent HTTP error: {e}")
            raise


class LightingSoundMusicAdapter(AgentAdapter):
    """Adapter for Lighting/Sound/Music agent (direct HTTP)"""

    def __init__(self, base_url: str):
        super().__init__(base_url)

    @property
    def requires_llm(self) -> bool:
        return False

    async def execute(self, skill: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute lighting/sound/music control via HTTP"""
        try:
            response = self.client.post(
                f"{self.base_url}/api/v1/{skill}",
                json=input_data
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Lighting/Sound/Music agent HTTP error: {e}")
            raise


class SafetyFilterAdapter(AgentAdapter):
    """Adapter for Safety Filter agent (direct HTTP)"""

    def __init__(self, base_url: str):
        super().__init__(base_url)

    @property
    def requires_llm(self) -> bool:
        return False

    async def execute(self, skill: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute safety filtering via HTTP"""
        try:
            response = self.client.post(
                f"{self.base_url}/api/v1/{skill}",
                json=input_data
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Safety Filter agent HTTP error: {e}")
            raise


class MusicGenerationAdapter(AgentAdapter):
    """Adapter for Music Generation agent (direct HTTP)"""

    def __init__(self, base_url: str):
        super().__init__(base_url)

    @property
    def requires_llm(self) -> bool:
        return False

    async def execute(self, skill: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute music generation via HTTP"""
        try:
            response = self.client.post(
                f"{self.base_url}/api/v1/{skill}",
                json=input_data
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Music Generation agent HTTP error: {e}")
            raise


class AutonomousAdapter(AgentAdapter):
    """Adapter for Autonomous agent (LLM-based)"""

    def __init__(self, base_url: str, privacy_router: PrivacyRouter):
        super().__init__(base_url)
        self.privacy_router = privacy_router

    @property
    def requires_llm(self) -> bool:
        return True

    async def execute(self, skill: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute autonomous agent skill using LLM"""
        prompt = input_data.get('prompt', '')
        max_tokens = input_data.get('max_tokens', 512)
        temperature = input_data.get('temperature', 0.7)

        try:
            # Route through PrivacyRouter
            response = self.privacy_router.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return {
                "text": response.get("text", ""),
                "backend": response.get("backend", "unknown"),
                "model": response.get("model", "")
            }
        except Exception as e:
            logger.error(f"Autonomous agent execution failed: {e}")
            raise
