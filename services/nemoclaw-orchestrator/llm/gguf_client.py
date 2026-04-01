# services/nemoclaw-orchestrator/llm/gguf_client.py
"""GGUF client for local quantized model support via Ollama"""
import httpx
import logging
import subprocess
import os
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class GGUFClient:
    """Client for GGUF (quantized) models loaded via Ollama"""

    def __init__(
        self,
        endpoint: str = "http://localhost:11434",
        gguf_base_path: str = "/home/ranj/Project_Chimera_Downloads/LLM Models/gguf",
        model_name: str = "llama-3.1-8b-instruct",
        gguf_relative_path: str = "other/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
    ):
        """
        Initialize GGUF client

        Args:
            endpoint: Ollama endpoint URL
            gguf_base_path: Base path to GGUF models directory
            model_name: Name to register the model under in Ollama
            gguf_relative_path: Relative path from gguf_base_path to the GGUF file
        """
        self.endpoint = endpoint.rstrip("/")
        self.gguf_base_path = Path(gguf_base_path)
        self.model_name = model_name
        self.gguf_path = self.gguf_base_path / gguf_relative_path
        self._client: Optional[httpx.Client] = None

        # Validate GGUF file exists
        if not self.gguf_path.exists():
            logger.warning(f"GGUF file not found: {self.gguf_path}")

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.Client(
                timeout=120.0,  # GGUF models can be slower
                limits=httpx.Limits(max_keepalive_connections=2, max_connections=5)
            )
        return self._client

    def is_model_loaded(self) -> bool:
        """Check if the GGUF model is loaded in Ollama"""
        try:
            client = self._get_client()
            response = client.get(f"{self.endpoint}/api/tags", timeout=5.0)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(m.get("name") == self.model_name for m in models)
            return False
        except Exception as e:
            logger.debug(f"Failed to check loaded models: {e}")
            return False

    def load_model(self) -> bool:
        """
        Load GGUF model into Ollama using ollama create

        Returns:
            True if model is available, False otherwise
        """
        if self.is_model_loaded():
            logger.debug(f"Model {self.model_name} already loaded in Ollama")
            return True

        if not self.gguf_path.exists():
            logger.error(f"Cannot load model - GGUF file not found: {self.gguf_path}")
            return False

        try:
            logger.info(f"Loading GGUF model from {self.gguf_path} as {self.model_name}")
            result = subprocess.run(
                ["ollama", "create", self.model_name, "--from", str(self.gguf_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout for large models
            )

            if result.returncode == 0:
                logger.info(f"Successfully loaded model {self.model_name}")
                return True
            else:
                logger.error(f"Failed to load model: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Model loading timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to load GGUF model: {e}")
            return False

    def is_available(self) -> bool:
        """Check if GGUF model service is available"""
        if not self.is_model_loaded():
            return self.load_model()
        return True

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using GGUF model via Ollama

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            Dict with generated text and metadata
        """
        if not self.is_available():
            raise RuntimeError(f"GGUF model {self.model_name} is not available")

        try:
            client = self._get_client()

            # Ollama API format
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                }
            }

            response = client.post(
                f"{self.endpoint}/api/generate",
                json=payload
            )
            response.raise_for_status()

            data = response.json()

            return {
                "text": data.get("response", ""),
                "model_used": self.model_name,
                "backend": "gguf",
                "gguf_path": str(self.gguf_path),
                "usage": {
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0)
                }
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"GGUF request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"GGUF generation error: {e}")
            raise

    def unload_model(self) -> bool:
        """
        Unload the GGUF model from Ollama

        Returns:
            True if successful, False otherwise
        """
        try:
            result = subprocess.run(
                ["ollama", "rm", self.model_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to unload model: {e}")
            return False

    def close(self):
        """Close HTTP client"""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
