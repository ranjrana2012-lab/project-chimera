"""
BSL Text2Gloss Agent - Translation Module

Implements English to BSL gloss notation translation:
- Single sentence translation
- Batch translation
- Redis caching with 24hr TTL
- Error recovery with fallbacks
- SignSpell gloss notation standard
"""

import time
import logging
import hashlib
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum

from prometheus_client import Counter, Histogram


# Configure logging
logger = logging.getLogger(__name__)


# Metrics
translation_requests = Counter(
    'bsl_translation_requests_total',
    'Total BSL translation requests',
    ['type', 'status']
)
translation_duration = Histogram(
    'bsl_translation_duration_seconds',
    'BSL translation duration'
)


class GlossFormat(Enum):
    """BSL gloss notation formats."""
    SIGN_SPELL = "singspell"
    HAMNOSYS = "hamnosys"
    SIMPLE = "simple"


@dataclass
class TranslationRequest:
    """Request for BSL translation."""
    text: str
    language: str = "en"
    gloss_format: GlossFormat = GlossFormat.SIGN_SPELL
    region: Optional[str] = None
    include_breakdown: bool = True
    include_markers: bool = True


@dataclass
class TranslationResponse:
    """Response from BSL translation."""
    request_id: str
    source_text: str
    gloss: str
    gloss_format: str
    duration: float
    confidence: float
    translation_time_ms: float
    breakdown: List[str] = field(default_factory=list)
    non_manual_markers: List[str] = field(default_factory=list)
    region: Optional[str] = None
    error: Optional[dict] = None
    from_cache: bool = False
    model_version: str = "bsl-v1.0"


class BSLTranslator:
    """
    BSL Text2Gloss translation service.

    Features:
    - Dictionary-based translation for common phrases
    - Rule-based translation for grammatical structures
    - Fallback to template-based translation
    - Redis caching
    - Batch processing
    """

    # Common phrase dictionary
    PHRASE_DICTIONARY = {
        "hello": "HELLO[right]wave",
        "good morning": "GOOD-MORNING[space]",
        "please": "PLEASE[chest]",
        "thank you": "THANK-YOU[chest]",
        "sorry": "SORRY[space]",
        "yes": "YES[head]nod",
        "no": "NO[head]shake",
        "how are you": "HOW YOU ?q",
        "what is your name": "NAME YOUR WHAT?q",
        "my name is": "NAME MY",
        "i understand": "UNDERSTAND I",
        "i don't understand": "UNDERSTAND I NOT neg",
        "look": "LOOK[head-point]",
        "listen": "LISTEN[ears]"
    }

    # Grammatical word order rules
    GRAMMAR_RULES = {
        "question": "TIME TOPIC COMMENT",
        "conditional": "CONDITION CLAUSE MAIN",
        "topic-comment": "TOPIC COMMENT"
    }

    def __init__(self, redis_client=None, cache_ttl: int = 86400):
        """
        Initialize BSL translator.

        Args:
            redis_client: Optional Redis client for caching
            cache_ttl: Cache TTL in seconds (default 24 hours)
        """
        self.redis = redis_client
        self.cache_ttl = cache_ttl
        self.degraded_mode = redis_client is None

    def translate(self, request: TranslationRequest) -> TranslationResponse:
        """
        Translate English text to BSL gloss notation.

        Args:
            request: Translation request

        Returns:
            Translation response with gloss notation
        """
        start_time = time.time()
        request_id = f"bsl_{int(time.time() * 1000)}"

        try:
            # Try cache first
            cache_key = self._get_cache_key(request.text, request.gloss_format)
            cached = self._get_from_cache(cache_key)

            if cached:
                translation_duration.observe(0)
                translation_requests.labels(type="single", status="cache_hit").inc()
                return TranslationResponse(
                    request_id=request_id,
                    source_text=request.text,
                    gloss=cached,
                    gloss_format=request.gloss_format.value,
                    duration=1.0,
                    confidence=1.0,
                    translation_time_ms=0,
                    from_cache=True,
                    model_version="bsl-v1.0"
                )

            # Perform translation
            gloss = self._translate_text(request)

            # Cache the result
            if not self.degraded_mode:
                self._cache_translation(cache_key, gloss)

            duration = time.time() - start_time
            translation_duration.observe(duration)
            translation_requests.labels(type="single", status="success").inc()

            return TranslationResponse(
                request_id=request_id,
                source_text=request.text,
                gloss=gloss,
                gloss_format=request.gloss_format.value,
                duration=len(request.split()) * 0.5,  # Estimate: 0.5s per word
                confidence=0.85,
                translation_time_ms=duration * 1000,
                breakdown=self._create_breakdown(gloss),
                model_version="bsl-v1.0",
                from_cache=False,
                degraded=self.degraded_mode
            )

        except Exception as e:
            logger.error(f"Translation error: {e}")
            translation_requests.labels(type="single", status="error").inc()

            # Return fallback gloss
            return self._fallback_translation(request_id, request.text, str(e))

    def translate_batch(
        self,
        requests: List[TranslationRequest]
    ) -> List[TranslationResponse]:
        """
        Translate multiple texts in batch.

        Args:
            requests: List of translation requests

        Returns:
            List of translation responses
        """
        results = []

        for req in requests:
            result = self.translate(req)
            results.append(result)

        return results

    def _translate_text(self, request: TranslationRequest) -> str:
        """Perform actual translation using dictionary and rules."""
        text = request.text.lower().strip()

        # Check phrase dictionary first
        if text in self.PHRASE_DICTIONARY:
            return self.PHRASE_DICTIONARY[text]

        # Word-by-word translation with rules
        words = text.split()
        gloss_words = []

        for word in words:
            # Check dictionary
            if word in self.PHRASE_DICTIONARY:
                gloss_words.append(self.PHRASE_DICTIONARY[word])
            else:
                # Finger-spelt word
                gloss_words.append(self._finger_spell(word))

        return " ".join(gloss_words)

    def _finger_spell(self, word: str) -> str:
        """Convert a word to finger-spelling notation."""
        # Finger-spell each letter
        return " ".join([f"FS-{letter.upper()}" for letter in word])

    def _create_breakdown(self, gloss: str) -> List[str]:
        """Break gloss into individual signs."""
        return gloss.split()

    def _fallback_translation(
        self,
        request_id: str,
        text: str,
        error: str
    ) -> TranslationResponse:
        """Return fallback gloss on translation failure."""
        # Finger-spell everything as fallback
        fallback_gloss = " ".join([f"FS-{c.upper()}" for c in text])

        return TranslationResponse(
            request_id=request_id,
            source_text=text,
            gloss=fallback_gloss,
            gloss_format="singspell",
            duration=len(text) * 0.3,
            confidence=0.5,
            translation_time_ms=0,
            error={"code": "TRANSLATION_ERROR", "message": error},
            model_version="bsl-v1.0"
        )

    def _get_cache_key(self, text: str, gloss_format: GlossFormat) -> str:
        """Generate cache key for translation."""
        content = f"{text}:{gloss_format.value}"
        return f"bsl:{hashlib.md5(content.encode()).hexdigest()}"

    def _get_from_cache(self, cache_key: str) -> Optional[str]:
        """Get translation from cache."""
        if not self.redis:
            return None

        try:
            cached = self.redis.get(cache_key)
            if cached:
                return cached.decode()
        except Exception as e:
            logger.warning(f"Redis get failed: {e}. Entering degraded mode.")
            self.degraded_mode = True

        return None

    def _cache_translation(self, cache_key: str, gloss: str):
        """Cache translation result."""
        if not self.redis:
            return

        try:
            self.redis.setex(cache_key, self.cache_ttl, gloss.encode())
        except Exception as e:
            logger.warning(f"Redis set failed: {e}. Entering degraded mode.")
            self.degraded_mode = True


def translate_and_enrich(
    text: str,
    redis_client=None,
    gloss_format: GlossFormat = GlossFormat.SIGN_SPELL
) -> dict:
    """
    Convenience function to translate text to BSL gloss.

    Args:
        text: English text to translate
        redis_client: Optional Redis client
        gloss_format: Gloss notation format

    Returns:
        Translation result as dictionary
    """
    translator = BSLTranslator(redis_client)
    request = TranslationRequest(text=text, gloss_format=gloss_format)

    result = translator.translate(request)

    return {
        "source_text": result.source_text,
        "gloss": result.gloss,
        "gloss_format": result.gloss_format,
        "duration": result.duration,
        "confidence": result.confidence,
        "translation_time_ms": result.translation_time_ms,
        "breakdown": result.breakdown,
        "from_cache": result.from_cache,
        "error": result.error
    }
