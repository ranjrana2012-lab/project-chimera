"""Core handler for BSL Text2Gloss Agent."""

import time
import logging
from typing import Dict, Any

from .gloss_translator import GlossTranslator

logger = logging.getLogger(__name__)


class BSLHandler:
    """Main handler for BSL Text2Gloss translation requests.

    Manages the translation service lifecycle and coordinates
    between the FastAPI routes and the translation engine.
    """

    def __init__(self, settings):
        """Initialize the BSL handler.

        Args:
            settings: Service configuration settings
        """
        self.settings = settings
        self.translator = GlossTranslator(settings)

    async def initialize(self) -> None:
        """Initialize the translation service.

        Loads the translation model and prepares the service
        for handling requests.
        """
        try:
            await self.translator.load_model()
            logger.info("BSL Text2Gloss service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize BSL service: {e}")
            raise

    async def translate(self, text: str, **kwargs) -> Dict[str, Any]:
        """Translate text to BSL gloss notation.

        Args:
            text: English text to translate
            **kwargs: Additional translation parameters

        Returns:
            Translation result with gloss, breakdown, and metadata
        """
        start_time = time.time()

        try:
            result = await self.translator.translate_to_gloss(
                text=text,
                gloss_format=kwargs.get("gloss_format"),
                max_length=kwargs.get("max_length", 512)
            )

            return {
                "gloss": result["gloss"],
                "breakdown": result.get("breakdown", []),
                "language": "bsl",
                "confidence": result.get("confidence", 0.85),
                "latency_ms": (time.time() - start_time) * 1000,
                "format": result.get("format", "hamnosys")
            }

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise

    async def translate_batch(self, texts: list[str], **kwargs) -> list[Dict[str, Any]]:
        """Translate multiple texts to BSL gloss notation.

        Args:
            texts: List of English texts to translate
            **kwargs: Additional translation parameters

        Returns:
            List of translation results
        """
        start_time = time.time()

        try:
            results = await self.translator.translate_batch(
                texts=texts,
                gloss_format=kwargs.get("gloss_format"),
                max_length=kwargs.get("max_length", 512)
            )

            # Add latency info to each result
            latency = (time.time() - start_time) * 1000
            for result in results:
                result["latency_ms"] = latency / len(results)

            return results

        except Exception as e:
            logger.error(f"Batch translation failed: {e}")
            raise

    async def close(self) -> None:
        """Clean up resources."""
        try:
            await self.translator.close()
            logger.info("BSL Text2Gloss service shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
