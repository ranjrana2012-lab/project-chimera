"""BSL Gloss Translator - Main translation service."""

import logging
from typing import Dict, Any
from .translator import BSLTranslator
from .gloss_formatter import GlossFormatter, GlossFormat

logger = logging.getLogger(__name__)


class GlossTranslator:
    """Main BSL gloss translation service.

    Combines the translation engine with gloss formatting capabilities
    to provide complete English-to-BSL gloss translation.
    """

    def __init__(self, settings):
        """Initialize the gloss translator.

        Args:
            settings: Service configuration settings
        """
        self.settings = settings
        self.device = settings.device
        self.model_name = settings.model_name
        self.default_format = GlossFormat(settings.gloss_format.lower())

        # Initialize components
        self.translator = BSLTranslator(
            model_name=self.model_name,
            device=self.device
        )
        self.formatter = GlossFormatter(default_format=self.default_format)

    async def load_model(self) -> None:
        """Load the translation model."""
        try:
            await self.translator.load_model()
            logger.info(f"BSL model loaded: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load BSL model: {e}")
            raise

    async def translate_to_gloss(
        self,
        text: str,
        gloss_format: str = None,
        max_length: int = 512
    ) -> Dict[str, Any]:
        """Translate English text to BSL gloss notation.

        Args:
            text: English text to translate
            gloss_format: Desired gloss format (optional)
            max_length: Maximum length for translation

        Returns:
            Dictionary with gloss, breakdown, and metadata
        """
        try:
            # Get base translation
            translation_result = await self.translator.translate(
                text=text,
                max_length=max_length
            )

            # Format the gloss
            format = GlossFormat(gloss_format.lower()) if gloss_format else self.default_format
            formatted_gloss = self.formatter.format_gloss(
                translation_result["gloss"],
                format=format
            )

            # Create breakdown
            breakdown = self.formatter.create_breakdown(
                formatted_gloss,
                text,
                translation_result["confidence"]
            )

            return {
                "gloss": formatted_gloss,
                "breakdown": breakdown,
                "confidence": translation_result["confidence"],
                "model_used": translation_result.get("model_used", self.model_name),
                "format": format.value
            }

        except Exception as e:
            logger.error(f"Translation error: {e}")
            raise

    async def translate_batch(
        self,
        texts: list[str],
        gloss_format: str = None,
        max_length: int = 512
    ) -> list[Dict[str, Any]]:
        """Translate multiple texts to BSL gloss notation.

        Args:
            texts: List of English texts
            gloss_format: Desired gloss format
            max_length: Maximum length per translation

        Returns:
            List of translation results
        """
        try:
            # Get batch translations
            translations = await self.translator.translate_batch(
                texts=texts,
                max_length=max_length
            )

            # Format each translation
            results = []
            format = GlossFormat(gloss_format.lower()) if gloss_format else self.default_format

            for i, translation in enumerate(translations):
                formatted_gloss = self.formatter.format_gloss(
                    translation["gloss"],
                    format=format
                )

                breakdown = self.formatter.create_breakdown(
                    formatted_gloss,
                    texts[i],
                    translation["confidence"]
                )

                results.append({
                    "gloss": formatted_gloss,
                    "breakdown": breakdown,
                    "confidence": translation["confidence"],
                    "model_used": translation.get("model_used", self.model_name),
                    "format": format.value
                })

            return results

        except Exception as e:
            logger.error(f"Batch translation error: {e}")
            raise

    async def close(self) -> None:
        """Clean up resources."""
        await self.translator.close()
        logger.info("Gloss translator resources cleaned up")
