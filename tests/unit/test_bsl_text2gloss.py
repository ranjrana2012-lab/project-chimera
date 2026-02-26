"""Unit tests for BSL gloss handler"""

import pytest
from services.bsl_text2gloss_agent.src.core.gloss_translator import GlossTranslator


@pytest.mark.unit
class TestGlossTranslator:
    """Test cases for GlossTranslator"""

    @pytest.fixture
    def translator(self):
        return GlossTranslator(None)

    @pytest.mark.asyncio
    async def test_translate_to_gloss(self, translator):
        """Test gloss translation."""
        result = await translator.translate_to_gloss("Hello my name is John")

        assert "gloss" in result
        assert result["language"] == "bsl"
        assert "breakdown" in result
