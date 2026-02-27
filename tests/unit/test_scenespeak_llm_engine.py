"""Unit tests for SceneSpeak LLM Engine."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import sys
from pathlib import Path

# Add services to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services"))

from services.scenespeak_agent.src.models.request import GenerationRequest
from services.scenespeak_agent.src.models.response import GenerationResponse
from services.scenespeak_agent.src.core.llm_engine import LLMEngine


@pytest.mark.unit
class TestLLMEngine:
    """Test cases for LLMEngine."""

    @pytest.fixture
    def engine(self):
        """Create an LLM engine instance."""
        return LLMEngine(
            model_name="mistralai/Mistral-7B-Instruct-v0.2",
            device="cuda",
            quantization=True
        )

    @pytest.fixture
    def sample_request(self):
        """Create a sample generation request."""
        return GenerationRequest(
            context="A tense scene in a dimly lit room.",
            character="PROTAGONIST",
            sentiment=0.3,
            max_tokens=256,
            temperature=0.8,
            top_p=0.9
        )

    def test_initialization(self, engine):
        """Test engine initialization."""
        assert engine.model_name == "mistralai/Mistral-7B-Instruct-v0.2"
        assert engine.device == "cuda"
        assert engine.quantization is True
        assert engine.model is None
        assert engine.tokenizer is None
        assert engine.loaded is False

    @pytest.mark.asyncio
    async def test_load_model(self, engine):
        """Test model loading."""
        with patch('services.scenespeak_agent.src.core.llm_engine.AutoTokenizer') as mock_tokenizer_class, \
             patch('services.scenespeak_agent.src.core.llm_engine.AutoModelForCausalLM') as mock_model_class, \
             patch('services.scenespeak_agent.src.core.llm_engine.BitsAndBytesConfig') as mock_bitsandbytes:

            # Setup mocks
            mock_tokenizer = MagicMock()
            mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer

            mock_model = MagicMock()
            mock_model_class.from_pretrained.return_value = mock_model

            mock_quant_config = MagicMock()
            mock_bitsandbytes.return_value = mock_quant_config

            # Load the model
            await engine.load()

            # Verify tokenizer was loaded
            mock_tokenizer_class.from_pretrained.assert_called_once_with(
                "mistralai/Mistral-7B-Instruct-v0.2",
                cache_dir="/app/models"
            )

            # Verify model was loaded with quantization
            mock_bitsandbytes.assert_called_once()
            mock_model_class.from_pretrained.assert_called_once()
            call_args = mock_model_class.from_pretrained.call_args
            assert call_args[1]['quantization_config'] == mock_quant_config
            assert call_args[1]['cache_dir'] == "/app/models"

            # Verify model was set to eval mode
            mock_model.eval.assert_called_once()

            # Verify loaded flag is set
            assert engine.loaded is True
            assert engine.tokenizer == mock_tokenizer
            assert engine.model == mock_model

    @pytest.mark.asyncio
    async def test_load_idempotent(self, engine):
        """Test that loading twice doesn't reload the model."""
        with patch('services.scenespeak_agent.src.core.llm_engine.AutoTokenizer') as mock_tokenizer_class, \
             patch('services.scenespeak_agent.src.core.llm_engine.AutoModelForCausalLM') as mock_model_class:

            mock_tokenizer = MagicMock()
            mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer

            mock_model = MagicMock()
            mock_model_class.from_pretrained.return_value = mock_model

            # Load twice
            await engine.load()
            await engine.load()

            # Verify only loaded once
            mock_tokenizer_class.from_pretrained.assert_called_once()
            mock_model_class.from_pretrained.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_dialogue(self, engine, sample_request):
        """Test dialogue generation."""
        with patch('services.scenespeak_agent.src.core.llm_engine.AutoTokenizer') as mock_tokenizer_class, \
             patch('services.scenespeak_agent.src.core.llm_engine.AutoModelForCausalLM') as mock_model_class:

            # Setup mocks
            mock_tokenizer = MagicMock()
            # Create a mock tensor-like object with to() method
            mock_input_ids = MagicMock()
            mock_input_ids.shape = (1, 10)  # 10 input tokens

            mock_inputs = {'input_ids': mock_input_ids}
            mock_inputs_obj = MagicMock()
            mock_inputs_obj.__getitem__ = lambda self, key: mock_inputs.get(key)
            mock_inputs_obj.to = MagicMock(return_value=mock_inputs_obj)
            mock_tokenizer.return_value = mock_inputs_obj
            mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer

            mock_model = MagicMock()
            # Mock generate to return output with more tokens than input
            mock_output = MagicMock()
            mock_output.shape = (1, 50)  # 50 total tokens (10 input + 40 new)
            mock_model.generate.return_value = mock_output
            mock_model_class.from_pretrained.return_value = mock_model

            # Mock decode to return dialogue
            mock_tokenizer.decode.return_value = "I can't believe what I'm hearing."

            # Load and generate
            await engine.load()
            response = await engine.generate(sample_request)

            # Verify response structure
            assert isinstance(response, GenerationResponse)
            assert response.dialogue == "I can't believe what I'm hearing."
            assert response.character == "PROTAGONIST"
            assert response.sentiment_used == 0.3
            assert response.tokens == 40  # 50 - 10
            assert response.from_cache is False
            assert response.model_version == "mistralai/Mistral-7B-Instruct-v0.2"
            assert isinstance(response.timestamp, datetime)
            assert response.generation_time_ms > 0

            # Verify tokenizer calls
            mock_tokenizer.assert_called_once()
            mock_tokenizer.decode.assert_called_once()

            # Verify model generate call
            mock_model.generate.assert_called_once()
            call_kwargs = mock_model.generate.call_args[1]
            assert call_kwargs['max_new_tokens'] == 256
            assert call_kwargs['temperature'] == 0.8
            assert call_kwargs['top_p'] == 0.9
            assert call_kwargs['do_sample'] is True

    @pytest.mark.asyncio
    async def test_generate_auto_loads(self, engine, sample_request):
        """Test that generate automatically loads the model if not loaded."""
        with patch('services.scenespeak_agent.src.core.llm_engine.AutoTokenizer') as mock_tokenizer_class, \
             patch('services.scenespeak_agent.src.core.llm_engine.AutoModelForCausalLM') as mock_model_class:

            mock_tokenizer = MagicMock()
            mock_inputs = MagicMock()
            mock_inputs.shape = [1, 10]
            mock_inputs.__getitem__ = lambda self, key: {'input_ids': MagicMock(shape=(1, 10))}.get(key)
            mock_tokenizer.return_value = mock_inputs
            mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer

            mock_model = MagicMock()
            mock_output = MagicMock()
            mock_output.shape = (1, 50)
            mock_output.__getitem__ = lambda self, key: MagicMock(shape=(1, 40)) if key == 0 else MagicMock()
            mock_model.generate.return_value = mock_output
            mock_model_class.from_pretrained.return_value = mock_model

            mock_tokenizer.decode.return_value = "Test dialogue."

            # Generate without explicitly loading
            response = await engine.generate(sample_request)

            # Verify model was loaded
            assert engine.loaded is True
            assert isinstance(response, GenerationResponse)

    @pytest.mark.asyncio
    async def test_sentiment_to_description(self, engine):
        """Test sentiment to description conversion."""
        assert engine._sentiment_to_description(0.8) == "very happy and optimistic"
        assert engine._sentiment_to_description(0.3) == "positive and cheerful"
        assert engine._sentiment_to_description(0.0) == "neutral"
        assert engine._sentiment_to_description(-0.3) == "somewhat negative or sad"
        assert engine._sentiment_to_description(-0.8) == "very negative or angry"

    @pytest.mark.asyncio
    async def test_build_prompt(self, engine, sample_request):
        """Test prompt building."""
        prompt = engine._build_prompt(sample_request)

        assert "PROTAGONIST" in prompt
        assert "A tense scene in a dimly lit room." in prompt
        assert "positive and cheerful" in prompt  # sentiment 0.3
        assert "Generate a response" in prompt

    @pytest.mark.asyncio
    async def test_generate_with_zero_temperature(self, engine):
        """Test generation with zero temperature (no sampling)."""
        request = GenerationRequest(
            context="Test context",
            character="TEST_CHAR",
            sentiment=0.0,
            temperature=0.0
        )

        with patch('services.scenespeak_agent.src.core.llm_engine.AutoTokenizer') as mock_tokenizer_class, \
             patch('services.scenespeak_agent.src.core.llm_engine.AutoModelForCausalLM') as mock_model_class:

            mock_tokenizer = MagicMock()
            mock_inputs = MagicMock()
            mock_inputs.shape = [1, 10]
            mock_inputs.__getitem__ = lambda self, key: {'input_ids': MagicMock(shape=(1, 10))}.get(key)
            mock_tokenizer.return_value = mock_inputs
            mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer

            mock_model = MagicMock()
            mock_output = MagicMock()
            mock_output.shape = (1, 50)
            mock_output.__getitem__ = lambda self, key: MagicMock(shape=(1, 40)) if key == 0 else MagicMock()
            mock_model.generate.return_value = mock_output
            mock_model_class.from_pretrained.return_value = mock_model

            mock_tokenizer.decode.return_value = "Test response."

            await engine.load()
            await engine.generate(request)

            # Verify do_sample is False when temperature is 0
            call_kwargs = mock_model.generate.call_args[1]
            assert call_kwargs['do_sample'] is False

    @pytest.mark.asyncio
    async def test_generate_with_negative_sentiment(self, engine):
        """Test generation with negative sentiment."""
        request = GenerationRequest(
            context="A tragic scene",
            character="HERO",
            sentiment=-0.7
        )

        with patch('services.scenespeak_agent.src.core.llm_engine.AutoTokenizer') as mock_tokenizer_class, \
             patch('services.scenespeak_agent.src.core.llm_engine.AutoModelForCausalLM') as mock_model_class:

            mock_tokenizer = MagicMock()
            mock_inputs = MagicMock()
            mock_inputs.shape = [1, 10]
            mock_inputs.__getitem__ = lambda self, key: {'input_ids': MagicMock(shape=(1, 10))}.get(key)
            mock_tokenizer.return_value = mock_inputs
            mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer

            mock_model = MagicMock()
            mock_output = MagicMock()
            mock_output.shape = (1, 50)
            mock_output.__getitem__ = lambda self, key: MagicMock(shape=(1, 40)) if key == 0 else MagicMock()
            mock_model.generate.return_value = mock_output
            mock_model_class.from_pretrained.return_value = mock_model

            mock_tokenizer.decode.return_value = "I can't go on."

            await engine.load()
            await engine.generate(request)

            # Verify prompt includes negative sentiment
            prompt = engine._build_prompt(request)
            assert "very negative or angry" in prompt

    @pytest.mark.asyncio
    async def test_load_without_quantization(self):
        """Test model loading without quantization."""
        engine = LLMEngine(
            model_name="mistralai/Mistral-7B-Instruct-v0.2",
            device="cpu",
            quantization=False
        )

        with patch('services.scenespeak_agent.src.core.llm_engine.AutoTokenizer') as mock_tokenizer_class, \
             patch('services.scenespeak_agent.src.core.llm_engine.AutoModelForCausalLM') as mock_model_class, \
             patch('services.scenespeak_agent.src.core.llm_engine.BitsAndBytesConfig') as mock_bitsandbytes:

            mock_tokenizer = MagicMock()
            mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer

            mock_model = MagicMock()
            mock_model_class.from_pretrained.return_value = mock_model

            await engine.load()

            # Verify BitsAndBytesConfig was not called
            mock_bitsandbytes.assert_not_called()

            # Verify model was loaded without quantization config
            call_args = mock_model_class.from_pretrained.call_args
            assert call_args[1]['quantization_config'] is None
