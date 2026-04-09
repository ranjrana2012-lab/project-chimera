#!/usr/bin/env python3
"""
Chimera Core - Monolithic Demonstrator

Project Chimera Phase 1: Local-First AI Framework Proof-of-Concept

This single, self-contained Python script demonstrates the core adaptive routing
logic that underpins the entire Chimera framework. It bypasses the distributed
microservices architecture to provide a clear, linear proof-of-concept.

Core Flow:
    1. Text Input → Sentiment Analysis (DistilBERT ML model)
    2. Sentiment → Adaptive Dialogue Generation (GLM-4.7 API or Ollama fallback)
    3. Output → Terminal with full state trace

Author: Project Chimera Technical Lead
Date: 2026-04-09
Version: 1.0.0 (Monolithic Proof-of-Concept)
"""

import os
import sys
import time
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

# Add paths to import from existing services
sys.path.insert(0, str(Path(__file__).parent.parent / "sentiment-agent" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scenespeak-agent"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("chimera_core")

# ============================================================================
# Configuration
# ============================================================================

@dataclass
class ChimeraConfig:
    """Configuration for Chimera Core demonstrator."""

    # Sentiment Analysis
    sentiment_model_path: Optional[str] = None  # Uses HuggingFace cache if None
    sentiment_device: str = "cpu"  # cpu, cuda, mps

    # Dialogue Generation
    glm_api_key: Optional[str] = None
    glm_api_base: str = "https://open.bigmodel.cn/api/paas/v4/"
    local_llm_url: str = "http://localhost:11434"
    local_llm_model: str = "llama3.2"
    prefer_local: bool = False

    # Adaptive Routing
    sentiment_threshold_positive: float = 0.6
    sentiment_threshold_negative: float = 0.4
    adaptation_enabled: bool = True

    @classmethod
    def from_env(cls) -> "ChimeraConfig":
        """Load configuration from environment variables."""
        return cls(
            sentiment_model_path=os.getenv("SENTIMENT_MODEL_PATH"),
            sentiment_device=os.getenv("SENTIMENT_DEVICE", "cpu"),
            glm_api_key=os.getenv("GLM_API_KEY"),
            glm_api_base=os.getenv("GLM_API_BASE", "https://open.bigmodel.cn/api/paas/v4/"),
            local_llm_url=os.getenv("LOCAL_LLM_URL", "http://localhost:11434"),
            local_llm_model=os.getenv("LOCAL_LLM_MODEL", "llama3.2"),
            prefer_local=os.getenv("PREFER_LOCAL", "false").lower() == "true",
            adaptation_enabled=os.getenv("ADAPTATION_ENABLED", "true").lower() == "true",
        )


# Load configuration
config = ChimeraConfig.from_env()

# ============================================================================
# Data Models
# ============================================================================

@dataclass
class SentimentResult:
    """Result from sentiment analysis."""
    sentiment: str  # positive, negative, neutral
    score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    emotions: Dict[str, float]  # joy, surprise, neutral, sadness, anger, fear
    model: str = "distilbert-sentiment"
    latency_ms: int = 0


@dataclass
class DialogueResult:
    """Result from dialogue generation."""
    dialogue: str
    tokens_used: int
    model: str
    source: str  # api, local, local-fallback, mock
    latency_ms: int
    adaptive_context: Optional[Dict[str, Any]] = None


@dataclass
class AdaptiveState:
    """The complete adaptive state of the system."""
    input_text: str
    sentiment: SentimentResult
    dialogue: DialogueResult
    adaptation: Optional[Dict[str, Any]] = None
    timestamp: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "input": self.input_text,
            "sentiment": {
                "label": self.sentiment.sentiment,
                "score": self.sentiment.score,
                "confidence": self.sentiment.confidence,
                "emotions": self.sentiment.emotions,
                "model": self.sentiment.model,
                "latency_ms": self.sentiment.latency_ms
            },
            "dialogue": {
                "text": self.dialogue.dialogue,
                "tokens_used": self.dialogue.tokens_used,
                "model": self.dialogue.model,
                "source": self.dialogue.source,
                "latency_ms": self.dialogue.latency_ms,
                "adaptive_context": self.dialogue.adaptive_context
            },
            "adaptation": self.adaptation
        }


# ============================================================================
# Sentiment Analysis Module
# ============================================================================

class SentimentAnalyzer:
    """
    Sentiment analysis using DistilBERT ML model.

    This module analyzes text to determine emotional sentiment, supporting
    the adaptive routing logic.
    """

    def __init__(self, config: ChimeraConfig):
        self.config = config
        self.model_loaded = False
        self._model = None

    def analyze(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of input text.

        Args:
            text: Input text to analyze

        Returns:
            SentimentResult with sentiment classification
        """
        start_time = time.time()

        if not text or not text.strip():
            return SentimentResult(
                sentiment="neutral",
                score=0.0,
                confidence=0.5,
                emotions={"joy": 0.0, "surprise": 0.0, "neutral": 1.0,
                         "sadness": 0.0, "anger": 0.0, "fear": 0.0},
                latency_ms=0
            )

        # Try to load and use ML model
        try:
            if not self.model_loaded:
                self._load_model()
                self.model_loaded = True

            if self._model:
                result = self._model.analyze(text)
                latency_ms = int((time.time() - start_time) * 1000)
                return SentimentResult(
                    sentiment=result["sentiment"],
                    score=result["score"],
                    confidence=result["confidence"],
                    emotions=result["emotions"],
                    latency_ms=latency_ms
                )
        except Exception as e:
            logger.warning(f"ML model analysis failed: {e}, using fallback")

        # Fallback to keyword-based analysis
        return self._fallback_analysis(text, start_time)

    def _load_model(self):
        """Load DistilBERT model from HuggingFace."""
        try:
            from sentiment_agent.ml_model import SentimentModel
            self._model = SentimentModel(
                cache_dir=self.config.sentiment_model_path,
                device=self.config.sentiment_device
            )
            self._model.load()
            logger.info("DistilBERT model loaded successfully")
        except ImportError:
            logger.warning("Sentiment model module not available, using fallback")
        except Exception as e:
            logger.warning(f"Failed to load ML model: {e}")

    def _fallback_analysis(self, text: str, start_time: float) -> SentimentResult:
        """
        Fallback keyword-based sentiment analysis.

        Used when ML model is unavailable.
        """
        text_lower = text.lower()

        positive_words = [
            "good", "great", "love", "amazing", "excellent", "happy", "joy",
            "wonderful", "fantastic", "brilliant", "beautiful", "excited"
        ]
        negative_words = [
            "bad", "hate", "terrible", "awful", "sad", "angry", "poor",
            "horrible", "disappointed", "frustrated", "upset", "worried"
        ]

        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        latency_ms = int((time.time() - start_time) * 1000)

        if positive_count > negative_count:
            return SentimentResult(
                sentiment="positive",
                score=0.6,
                confidence=0.5,
                emotions={"joy": 0.6, "surprise": 0.2, "neutral": 0.1,
                         "sadness": 0.0, "anger": 0.0, "fear": 0.0},
                model="keyword-fallback",
                latency_ms=latency_ms
            )
        elif negative_count > positive_count:
            return SentimentResult(
                sentiment="negative",
                score=-0.6,
                confidence=0.5,
                emotions={"joy": 0.0, "surprise": 0.1, "neutral": 0.1,
                         "sadness": 0.5, "anger": 0.3, "fear": 0.1},
                model="keyword-fallback",
                latency_ms=latency_ms
            )
        else:
            return SentimentResult(
                sentiment="neutral",
                score=0.0,
                confidence=0.5,
                emotions={"joy": 0.0, "surprise": 0.0, "neutral": 1.0,
                         "sadness": 0.0, "anger": 0.0, "fear": 0.0},
                model="keyword-fallback",
                latency_ms=latency_ms
            )


# ============================================================================
# Dialogue Generation Module
# ============================================================================

class DialogueGenerator:
    """
    Dialogue generation with adaptive prompting.

    Generates contextually appropriate dialogue based on sentiment analysis,
    demonstrating the adaptive routing capability.
    """

    def __init__(self, config: ChimeraConfig):
        self.config = config
        self._local_llm_available = None

    async def generate(
        self,
        prompt: str,
        sentiment: SentimentResult,
        adaptation_enabled: bool = True
    ) -> DialogueResult:
        """
        Generate dialogue with optional adaptive context based on sentiment.

        Args:
            prompt: Base prompt for generation
            sentiment: Sentiment analysis result for adaptation
            adaptation_enabled: Whether to use adaptive prompts (default: True)

        Returns:
            DialogueResult with generated text and metadata
        """
        start_time = time.time()

        # Build prompt (adaptive or standard)
        if adaptation_enabled:
            final_prompt = self._build_adaptive_prompt(prompt, sentiment)
        else:
            final_prompt = f"User input: {prompt}\n\nResponse:"

        # Try local LLM first if preferred
        if self.config.prefer_local:
            result = await self._try_local_llm(final_prompt, sentiment, adaptation_enabled, start_time)
            if result:
                return result

        # Try GLM API if key available
        if self.config.glm_api_key:
            result = await self._try_glm_api(final_prompt, sentiment, adaptation_enabled, start_time)
            if result:
                return result

        # Fallback to local LLM
        result = await self._try_local_llm(final_prompt, sentiment, adaptation_enabled, start_time)
        if result:
            return result

        # Final fallback to mock response
        return self._mock_response(prompt, sentiment, adaptation_enabled, start_time)

    def _build_adaptive_prompt(self, prompt: str, sentiment: SentimentResult) -> str:
        """
        Build an adaptive prompt based on sentiment analysis.

        This is the core of the adaptive routing logic - the system adjusts
        its dialogue generation based on detected emotional state.
        """
        adaptation_instruction = ""

        if sentiment.sentiment == "positive":
            adaptation_instruction = (
                "The user is in a positive, engaged emotional state. "
                "Respond with enthusiasm, energy, and forward-looking dialogue. "
                "Build on their positive momentum."
            )
        elif sentiment.sentiment == "negative":
            adaptation_instruction = (
                "The user is experiencing negative emotions. "
                "Respond with empathy, support, and reassurance. "
                "Acknowledge their feelings constructively."
            )
        else:  # neutral
            adaptation_instruction = (
                "The user is in a neutral state. "
                "Respond with clear, informative dialogue. "
                "Maintain professional but approachable tone."
            )

        return f"{adaptation_instruction}\n\nUser input: {prompt}\n\nResponse:"

    async def _try_local_llm(
        self,
        prompt: str,
        sentiment: SentimentResult,
        adaptation_enabled: bool,
        start_time: float
    ) -> Optional[DialogueResult]:
        """Try to generate dialogue using local LLM (Ollama)."""
        try:
            import httpx

            # Build Ollama API request
            payload = {
                "model": self.config.local_llm_model,
                "prompt": prompt,
                "stream": False
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.config.local_llm_url}/api/generate",
                    json=payload
                )

                if response.status_code == 200:
                    data = response.json()
                    latency_ms = int((time.time() - start_time) * 1000)

                    adaptive_context = {"sentiment": sentiment.sentiment} if adaptation_enabled else None

                    return DialogueResult(
                        dialogue=data.get("response", "").strip(),
                        tokens_used=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                        model=self.config.local_llm_model,
                        source="local",
                        latency_ms=latency_ms,
                        adaptive_context=adaptive_context
                    )
                else:
                    logger.warning(f"Local LLM returned status {response.status_code}")
                    return None

        except Exception as e:
            logger.debug(f"Local LLM unavailable: {e}")
            return None

    async def _try_glm_api(
        self,
        prompt: str,
        sentiment: SentimentResult,
        adaptation_enabled: bool,
        start_time: float
    ) -> Optional[DialogueResult]:
        """Try to generate dialogue using GLM 4.7 API."""
        try:
            import httpx

            payload = {
                "model": "glm-4",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.7
            }

            headers = {
                "Authorization": f"Bearer {self.config.glm_api_key}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.config.glm_api_base}chat/completions",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()

                latency_ms = int((time.time() - start_time) * 1000)

                adaptive_context = {"sentiment": sentiment.sentiment} if adaptation_enabled else None

                return DialogueResult(
                    dialogue=data["choices"][0]["message"]["content"].strip(),
                    tokens_used=data["usage"]["total_tokens"],
                    model="glm-4",
                    source="api",
                    latency_ms=latency_ms,
                    adaptive_context=adaptive_context
                )

        except Exception as e:
            logger.warning(f"GLM API failed: {e}")
            return None

    def _mock_response(
        self,
        prompt: str,
        sentiment: SentimentResult,
        adaptation_enabled: bool,
        start_time: float
    ) -> DialogueResult:
        """Generate a mock response when no LLM is available."""
        latency_ms = int((time.time() - start_time) * 1000)

        if adaptation_enabled:
            # Adaptive responses based on sentiment
            if sentiment.sentiment == "positive":
                response = (
                    "That's wonderful to hear! Your positive energy is contagious. "
                    "Let's build on this momentum together!"
                )
            elif sentiment.sentiment == "negative":
                response = (
                    "I understand things may be difficult right now. "
                    "Let's work through this together - you're not alone."
                )
            else:
                response = (
                    "Thank you for your input. Let me help you with that."
                )
        else:
            # Standard non-adaptive response
            response = "Thank you for your input. I have received your message."

        adaptive_context = {"sentiment": sentiment.sentiment} if adaptation_enabled else None

        return DialogueResult(
            dialogue=response,
            tokens_used=0,
            model="mock",
            source="fallback",
            latency_ms=latency_ms,
            adaptive_context=adaptive_context
        )


# ============================================================================
# Adaptive Routing Engine
# ============================================================================

class AdaptiveRoutingEngine:
    """
    Core adaptive routing logic.

    This engine coordinates sentiment analysis and dialogue generation,
    applying adaptive rules based on emotional state.
    """

    def __init__(self, config: ChimeraConfig):
        self.config = config
        self.sentiment_analyzer = SentimentAnalyzer(config)
        self.dialogue_generator = DialogueGenerator(config)

    async def process(self, input_text: str) -> AdaptiveState:
        """
        Process input through the adaptive routing pipeline.

        Pipeline:
            1. Analyze sentiment of input
            2. Generate adaptive dialogue based on sentiment
            3. Apply adaptive routing rules
            4. Return complete state

        Args:
            input_text: User input text

        Returns:
            AdaptiveState with complete processing trace
        """
        timestamp = datetime.now().isoformat()

        logger.info("=" * 60)
        logger.info("CHIMERA CORE: Adaptive Routing Pipeline")
        logger.info("=" * 60)
        logger.info(f"Input: {input_text[:100]}{'...' if len(input_text) > 100 else ''}")
        logger.info("")

        # Step 1: Sentiment Analysis
        logger.info("[STEP 1] Sentiment Analysis...")
        sentiment = self.sentiment_analyzer.analyze(input_text)
        logger.info(f"  → Sentiment: {sentiment.sentiment.upper()}")
        logger.info(f"  → Score: {sentiment.score:+.2f}")
        logger.info(f"  → Confidence: {sentiment.confidence:.2f}")
        logger.info(f"  → Latency: {sentiment.latency_ms}ms")
        logger.info("")

        # Step 2: Adaptive Dialogue Generation
        logger.info("[STEP 2] Adaptive Dialogue Generation...")
        dialogue = await self.dialogue_generator.generate(input_text, sentiment, self.config.adaptation_enabled)
        logger.info(f"  → Source: {dialogue.source.upper()}")
        logger.info(f"  → Model: {dialogue.model}")
        logger.info(f"  → Tokens: {dialogue.tokens_used}")
        logger.info(f"  → Latency: {dialogue.latency_ms}ms")
        logger.info("")

        # Step 3: Adaptive Routing Rules
        adaptation = None
        if self.config.adaptation_enabled:
            logger.info("[STEP 3] Adaptive Routing Rules...")
            adaptation = self._apply_adaptive_rules(sentiment, dialogue)
            logger.info(f"  → Routing: {adaptation['routing_strategy']}")
            logger.info(f"  → Context: {adaptation['context_mode']}")
            logger.info("")

        # Build complete state
        state = AdaptiveState(
            input_text=input_text,
            sentiment=sentiment,
            dialogue=dialogue,
            adaptation=adaptation,
            timestamp=timestamp
        )

        logger.info("=" * 60)
        logger.info("OUTPUT:")
        logger.info("-" * 60)
        logger.info(dialogue.dialogue)
        logger.info("-" * 60)
        logger.info("")

        return state

    def _apply_adaptive_rules(
        self,
        sentiment: SentimentResult,
        dialogue: DialogueResult
    ) -> Dict[str, Any]:
        """
        Apply adaptive routing rules based on sentiment and dialogue.

        This demonstrates the core innovation: the system routes responses
        differently based on detected emotional state.
        """
        if sentiment.sentiment == "positive":
            return {
                "routing_strategy": "momentum_build",
                "context_mode": "expansive",
                "tone_adjustment": "enthusiastic",
                "next_action": "capitalize_on_engagement"
            }
        elif sentiment.sentiment == "negative":
            return {
                "routing_strategy": "supportive_care",
                "context_mode": "empathetic",
                "tone_adjustment": "reassuring",
                "next_action": "provide_support"
            }
        else:
            return {
                "routing_strategy": "standard_response",
                "context_mode": "neutral",
                "tone_adjustment": "professional",
                "next_action": "await_clarification"
            }


# ============================================================================
# Main Interface
# ============================================================================

async def interactive_mode(engine: AdaptiveRoutingEngine):
    """Run interactive mode where user can input text."""
    print("\n" + "=" * 60)
    print(" CHIMERA CORE - Monolithic Demonstrator")
    print(" Project Chimera Phase 1: Local-First AI Framework")
    print("=" * 60)
    print("\nCommands:")
    print("  <text>       - Analyze text with adaptive routing")
    print("  demo         - Run demo inputs")
    print("  compare <text> - Show adaptive vs non-adaptive comparison")
    print("  quit         - Exit")
    print("-" * 60)

    while True:
        try:
            user_input = input("\n> ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                print("\nExiting Chimera Core. Goodbye!")
                break

            if user_input.lower() == "demo":
                print("\nRunning demo inputs...")
                demo_inputs = [
                    "I'm so excited about this project! It's going to be amazing!",
                    "I'm really frustrated with how things are going.",
                    "Can you tell me more about the system?"
                ]
                for demo_input in demo_inputs:
                    print(f"\n[DEMO] Processing: {demo_input}")
                    state = await engine.process(demo_input)
                    print(f"Adaptive State: {json.dumps(state.to_dict(), indent=2)}\n")
                    time.sleep(1)
                continue

            # Check for compare command
            if user_input.lower().startswith("compare "):
                compare_text = user_input[8:].strip()
                if compare_text:
                    result = await comparison_mode(engine, compare_text)
                    print(f"\n[COMPARISON COMPLETE]")
                    print(json.dumps(result, indent=2))
                else:
                    print("Usage: compare <text to analyze>")
                continue

            # Process user input normally
            state = await engine.process(user_input)

            # Show adaptive state
            print("\n[ADAPTIVE STATE]")
            print(json.dumps(state.to_dict(), indent=2))

        except KeyboardInterrupt:
            print("\n\nInterrupted. Exiting...")
            break
        except Exception as e:
            logger.error(f"Error processing input: {e}")


async def single_mode(engine: AdaptiveRoutingEngine, input_text: str):
    """Run in single-input mode."""
    state = await engine.process(input_text)
    return state


async def comparison_mode(engine: AdaptiveRoutingEngine, input_text: str):
    """
    Run comparison mode showing adaptive vs non-adaptive responses.

    This demonstrates the core innovation: how the system adapts its response
    based on detected emotional state.
    """
    print("\n" + "=" * 80)
    print(" COMPARISON MODE: Adaptive vs Non-Adaptive")
    print("=" * 80)
    print(f"Input: {input_text}")
    print("-" * 80)

    # First, run WITH adaptation enabled
    print("\n[WITH ADAPTATION]")
    print("-" * 40)
    adaptive_config = ChimeraConfig(
        sentiment_model_path=config.sentiment_model_path,
        sentiment_device=config.sentiment_device,
        glm_api_key=config.glm_api_key,
        glm_api_base=config.glm_api_base,
        local_llm_url=config.local_llm_url,
        local_llm_model=config.local_llm_model,
        prefer_local=config.prefer_local,
        adaptation_enabled=True  # ADAPTATION ON
    )
    adaptive_engine = AdaptiveRoutingEngine(adaptive_config)
    adaptive_state = await adaptive_engine.process(input_text)

    # Then, run WITHOUT adaptation
    print("\n[WITHOUT ADAPTATION]")
    print("-" * 40)
    non_adaptive_config = ChimeraConfig(
        sentiment_model_path=config.sentiment_model_path,
        sentiment_device=config.sentiment_device,
        glm_api_key=config.glm_api_key,
        glm_api_base=config.glm_api_base,
        local_llm_url=config.local_llm_url,
        local_llm_model=config.local_llm_model,
        prefer_local=config.prefer_local,
        adaptation_enabled=False  # ADAPTATION OFF
    )
    non_adaptive_engine = AdaptiveRoutingEngine(non_adaptive_config)
    non_adaptive_state = await non_adaptive_engine.process(input_text)

    # Show comparison summary
    print("\n" + "=" * 80)
    print(" COMPARISON SUMMARY")
    print("=" * 80)

    sentiment_label = adaptive_state.sentiment.sentiment.upper()
    print(f"\nDetected Sentiment: {sentiment_label}")
    print(f"  Score: {adaptive_state.sentiment.score:+.3f}")
    print(f"  Confidence: {adaptive_state.sentiment.confidence:.3f}")

    print(f"\nAdaptive Response:")
    print(f"  Strategy: {adaptive_state.adaptation['routing_strategy']}")
    print(f"  Context: {adaptive_state.adaptation['context_mode']}")
    print(f"  Tone: {adaptive_state.adaptation['tone_adjustment']}")
    print(f"  Output: \"{adaptive_state.dialogue.dialogue}\"")

    print(f"\nNon-Adaptive Response:")
    print(f"  Strategy: {non_adaptive_state.adaptation['routing_strategy'] if non_adaptive_state.adaptation else 'none'}")
    print(f"  Context: {non_adaptive_state.adaptation['context_mode'] if non_adaptive_state.adaptation else 'none'}")
    print(f"  Tone: {non_adaptive_state.adaptation['tone_adjustment'] if non_adaptive_state.adaptation else 'neutral'}")
    print(f"  Output: \"{non_adaptive_state.dialogue.dialogue}\"")

    print("\n" + "=" * 80)
    print(" KEY DIFFERENCE")
    print("=" * 80)
    print(f"The adaptive system detects {sentiment_label} sentiment and adjusts its")
    print(f"response strategy to '{adaptive_state.adaptation['routing_strategy']}'")
    print(f"with a '{adaptive_state.adaptation['tone_adjustment']}' tone.")
    print()
    print("The non-adaptive system uses the same standard response regardless of")
    print("emotional state, demonstrating the value of adaptive routing.")
    print("=" * 80 + "\n")

    return {
        "adaptive": adaptive_state.to_dict(),
        "non_adaptive": non_adaptive_state.to_dict(),
        "comparison": {
            "sentiment_detected": sentiment_label,
            "adaptive_strategy": adaptive_state.adaptation['routing_strategy'],
            "non_adaptive_strategy": non_adaptive_state.adaptation['routing_strategy'] if non_adaptive_state.adaptation else 'none',
            "key_difference": f"Adaptive system adjusts to {sentiment_label} emotion, non-adaptive uses standard response"
        }
    }


def print_banner():
    """Print startup banner with system info."""
    print("\n" + "=" * 60)
    print(" CHIMERA CORE v1.0.0")
    print(" Monolithic Demonstrator - Project Chimera Phase 1")
    print("=" * 60)
    print(f" Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Adaptation: {'ENABLED' if config.adaptation_enabled else 'DISABLED'}")
    print(f" Prefer Local LLM: {config.prefer_local}")
    print(f" GLM API: {'CONFIGURED' if config.glm_api_key else 'NOT CONFIGURED'}")
    print(f" Local LLM URL: {config.local_llm_url}")
    print("=" * 60 + "\n")


async def main():
    """Main entry point."""
    print_banner()

    # Initialize engine
    engine = AdaptiveRoutingEngine(config)

    # Check for command line arguments
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()

        if cmd == "compare" and len(sys.argv) > 2:
            # Comparison mode
            input_text = " ".join(sys.argv[2:])
            result = await comparison_mode(engine, input_text)
            print("\n[COMPLETE]")
            print(json.dumps(result, indent=2))
        elif cmd == "demo":
            # Demo mode
            demo_inputs = [
                "I'm so excited about this project! It's going to be amazing!",
                "I'm really frustrated with how things are going.",
                "Can you tell me more about the system?"
            ]
            for demo_input in demo_inputs:
                state = await engine.process(demo_input)
                time.sleep(1)
        else:
            # Single input mode
            input_text = " ".join(sys.argv[1:])
            state = await single_mode(engine, input_text)
            print("\n[COMPLETE]")
            print(json.dumps(state.to_dict(), indent=2))
    else:
        # Interactive mode
        await interactive_mode(engine)


if __name__ == "__main__":
    asyncio.run(main())
