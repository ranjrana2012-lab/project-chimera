"""Unit tests for BSL Text2Gloss handler and translator."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from services.bsl_text2gloss_agent.src.core.gloss_translator import GlossTranslator
from services.bsl_text2gloss_agent.src.core.handler import BSLHandler
from services.bsl_text2gloss_agent.src.core.translator import BSLTranslator
from services.bsl_text2gloss_agent.src.core.gloss_formatter import GlossFormatter, GlossFormat


@pytest.mark.unit
class TestGlossTranslator:
    """Test cases for GlossTranslator."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = Mock()
        settings.model_name = "Helsinki-NLP/opus-mt-en-ROMANCE"
        settings.device = "cpu"
        settings.gloss_format = "hamnosys"
        return settings

    @pytest.fixture
    def translator(self, mock_settings):
        """Create GlossTranslator instance."""
        return GlossTranslator(mock_settings)

    def test_translator_initialization(self, translator, mock_settings):
        """Test translator initialization."""
        assert translator.model_name == mock_settings.model_name
        assert translator.device == mock_settings.device
        assert isinstance(translator.formatter, GlossFormatter)

    @pytest.mark.asyncio
    async def test_translate_to_gloss(self, translator):
        """Test gloss translation."""
        # Mock the underlying translator
        translator.translator = Mock()
        translator.translator.translate = AsyncMock(return_value={
            "gloss": "HELLO HOW YOU",
            "confidence": 0.85,
            "model_used": "test-model"
        })

        result = await translator.translate_to_gloss("Hello, how are you?")

        assert "gloss" in result
        # The formatter adds a ^ prefix for hamnosys format
        assert "HELLO HOW YOU" in result["gloss"]
        assert "breakdown" in result
        assert result["confidence"] == 0.85
        assert result["format"] == "hamnosys"

    @pytest.mark.asyncio
    async def test_translate_with_custom_format(self, translator):
        """Test translation with custom gloss format."""
        translator.translator = Mock()
        translator.translator.translate = AsyncMock(return_value={
            "gloss": "HELLO HOW YOU",
            "confidence": 0.85,
            "model_used": "test-model"
        })

        result = await translator.translate_to_gloss(
            "Hello",
            gloss_format="simplified"
        )

        assert result["format"] == "simplified"

    @pytest.mark.asyncio
    async def test_close(self, translator):
        """Test resource cleanup."""
        translator.translator = Mock()
        translator.translator.close = AsyncMock()

        await translator.close()

        translator.translator.close.assert_called_once()


@pytest.mark.unit
class TestBSLHandler:
    """Test cases for BSLHandler."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = Mock()
        settings.model_name = "Helsinki-NLP/opus-mt-en-ROMANCE"
        settings.device = "cpu"
        settings.gloss_format = "hamnosys"
        return settings

    @pytest.fixture
    def handler(self, mock_settings):
        """Create BSLHandler instance."""
        return BSLHandler(mock_settings)

    def test_handler_initialization(self, handler, mock_settings):
        """Test handler initialization."""
        assert handler.settings == mock_settings
        assert handler.translator is not None

    @pytest.mark.asyncio
    async def test_initialize(self, handler):
        """Test handler initialization."""
        handler.translator.load_model = AsyncMock()

        await handler.initialize()

        handler.translator.load_model.assert_called_once()

    @pytest.mark.asyncio
    async def test_translate(self, handler):
        """Test translation through handler."""
        handler.translator.translate_to_gloss = AsyncMock(return_value={
            "gloss": "HELLO HOW YOU",
            "breakdown": [],
            "confidence": 0.85,
            "model_used": "test-model",
            "format": "hamnosys"
        })

        result = await handler.translate("Hello, how are you?")

        assert "gloss" in result
        assert result["language"] == "bsl"
        assert "latency_ms" in result
        assert result["confidence"] == 0.85

    @pytest.mark.asyncio
    async def test_translate_batch(self, handler):
        """Test batch translation."""
        handler.translator.translate_batch = AsyncMock(return_value=[
            {
                "gloss": "HELLO",
                "breakdown": [],
                "confidence": 0.85,
                "model_used": "test-model",
                "format": "hamnosys"
            },
            {
                "gloss": "GOODBYE",
                "breakdown": [],
                "confidence": 0.88,
                "model_used": "test-model",
                "format": "hamnosys"
            }
        ])

        results = await handler.translate_batch(["Hello", "Goodbye"])

        assert len(results) == 2
        assert results[0]["gloss"] == "HELLO"
        assert results[1]["gloss"] == "GOODBYE"

    @pytest.mark.asyncio
    async def test_close(self, handler):
        """Test handler cleanup."""
        handler.translator.close = AsyncMock()

        await handler.close()

        handler.translator.close.assert_called_once()


@pytest.mark.unit
class TestGlossFormatter:
    """Test cases for GlossFormatter."""

    @pytest.fixture
    def formatter(self):
        """Create GlossFormatter instance."""
        return GlossFormatter(default_format=GlossFormat.SIMPLIFIED)

    def test_format_simplified(self, formatter):
        """Test simplified format."""
        result = formatter.format_gloss("hello how are you", GlossFormat.SIMPLIFIED)
        assert result == "HELLO HOW ARE YOU"

    def test_create_breakdown(self, formatter):
        """Test breakdown creation."""
        breakdown = formatter.create_breakdown(
            "HELLO HOW YOU",
            "hello how you",
            confidence=0.90
        )

        assert len(breakdown) == 3
        assert breakdown[0]["gloss"] == "HELLO"
        assert breakdown[0]["english_source"] == "hello"
        assert breakdown[0]["confidence"] == 0.90

    def test_normalize_text(self, formatter):
        """Test text normalization."""
        result = formatter.normalize_text("Hello,  how  are  you?")
        assert result == "hello, how are you?"

    def test_normalize_contractions(self, formatter):
        """Test contraction expansion."""
        result = formatter.normalize_text("don't won't can't")
        assert "do not" in result
        assert "will not" in result
        assert "cannot" in result

    def test_add_non_manual_markers(self, formatter):
        """Test adding non-manual markers."""
        result = formatter.add_non_manual_markers("HELLO", ["question"])
        assert "?" in result or "brows" in result


@pytest.mark.unit
class TestBSLTranslator:
    """Test cases for BSLTranslator (translation engine)."""

    @pytest.fixture
    def translator(self):
        """Create BSLTranslator instance."""
        return BSLTranslator(model_name="test-model", device="cpu")

    def test_translator_initialization(self, translator):
        """Test translator initialization."""
        assert translator.model_name == "test-model"
        assert translator.device == "cpu"
        assert translator._loaded is False

    @pytest.mark.asyncio
    async def test_load_model(self, translator):
        """Test model loading with mocked transformers."""
        with patch('services.bsl_text2gloss_agent.src.core.translator.AutoTokenizer') as mock_tokenizer, \
             patch('services.bsl_text2gloss_agent.src.core.translator.AutoModelForSeq2SeqLM') as mock_model:

            mock_tokenizer.from_pretrained = Mock(return_value=Mock())
            mock_model.from_pretrained = Mock(return_value=Mock())

            await translator.load_model()

            assert translator._loaded is True

