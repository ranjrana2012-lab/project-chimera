"""LLM engine for dialogue generation."""

import asyncio
import hashlib
import time
from pathlib import Path
from typing import Optional

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from datetime import datetime, timezone

from ..models.request import GenerationRequest
from ..models.response import GenerationResponse


class LLMEngine:
    """Manages LLM model loading and inference."""

    def __init__(
        self,
        model_name: str = "mistralai/Mistral-7B-Instruct-v0.2",
        device: str = "cuda",
        quantization: bool = True
    ):
        self.model_name = model_name
        self.device = device
        self.quantization = quantization
        self.model = None
        self.tokenizer = None
        self.loaded = False

    async def load(self) -> None:
        """Load the model."""
        if self.loaded:
            return

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            cache_dir="/app/models"
        )

        # Configure quantization
        if self.quantization:
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True
            )
        else:
            quantization_config = None

        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            quantization_config=quantization_config,
            device_map="auto",
            cache_dir="/app/models",
            torch_dtype=torch.float16
        )

        self.model.eval()
        self.loaded = True

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate dialogue."""
        if not self.loaded:
            await self.load()

        start_time = time.time()
        request_id = hashlib.md5(
            f"{request.context}:{request.character}:{request.sentiment}".encode()
        ).hexdigest()

        # Build prompt
        prompt = self._build_prompt(request)

        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        # Generate
        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                do_sample=request.temperature > 0,
                pad_token_id=self.tokenizer.eos_token_id
            )

        # Decode
        dialogue = self.tokenizer.decode(
            output_ids[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )

        generation_time = (time.time() - start_time) * 1000

        return GenerationResponse(
            request_id=request_id,
            dialogue=dialogue.strip(),
            character=request.character,
            sentiment_used=request.sentiment,
            tokens=output_ids.shape[1] - inputs['input_ids'].shape[1],
            confidence=0.8,  # Placeholder
            from_cache=False,
            generation_time_ms=generation_time,
            model_version=self.model_name,
            timestamp=datetime.now(timezone.utc)
        )

    def _build_prompt(self, request: GenerationRequest) -> str:
        """Build prompt from request."""
        sentiment_desc = self._sentiment_to_description(request.sentiment)

        prompt = f"""You are {request.character}, a character in a live theatre performance.

Context: {request.context}
Current mood: {sentiment_desc}

Generate a response that fits this scene and mood:"""

        return prompt

    def _sentiment_to_description(self, sentiment: float) -> str:
        """Convert sentiment value to description."""
        if sentiment > 0.5:
            return "very happy and optimistic"
        elif sentiment > 0:
            return "positive and cheerful"
        elif sentiment == 0:
            return "neutral"
        elif sentiment > -0.5:
            return "somewhat negative or sad"
        else:
            return "very negative or angry"
