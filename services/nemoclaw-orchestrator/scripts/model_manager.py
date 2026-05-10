#!/usr/bin/env python3
"""
NemoClaw Model Manager

Python utility for managing GGUF models in NemoClaw.
Provides programmatic access to model loading, switching, and status checking.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass, asdict
import httpx
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Information about a model"""
    name: str
    description: str
    size_gb: float
    model_type: Literal["ollama", "gguf"]
    gguf_path: Optional[str] = None
    is_loaded: bool = False


class ModelManager:
    """
    Manages GGUF models for NemoClaw

    Handles loading GGUF models into Ollama, checking status,
    and switching between models.
    """

    # Model definitions
    MODELS: Dict[str, ModelInfo] = {
        "llama3:instruct": ModelInfo(
            name="llama3:instruct",
            description="Ollama built-in - 4GB",
            size_gb=4.0,
            model_type="ollama",
        ),
        "llama3:8b": ModelInfo(
            name="llama3:8b",
            description="Ollama built-in - 4.7GB",
            size_gb=4.7,
            model_type="ollama",
        ),
        "llama-3.1-8b-instruct": ModelInfo(
            name="llama-3.1-8b-instruct",
            description="Meta Llama 3.1 8B Instruct - 4.6GB GGUF",
            size_gb=4.6,
            model_type="gguf",
            gguf_path="other/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        ),
        "bsl-phase7": ModelInfo(
            name="bsl-phase7",
            description="BSL Phase 7 model - GGUF",
            size_gb=4.0,
            model_type="gguf",
            gguf_path="bsl-phases/bsl_phase7.Q4_K_M.gguf",
        ),
        "bsl-phase8": ModelInfo(
            name="bsl-phase8",
            description="BSL Phase 8 model - GGUF",
            size_gb=4.0,
            model_type="gguf",
            gguf_path="bsl-phases/bsl_phase8.Q4_K_M.gguf",
        ),
        "bsl-phase9": ModelInfo(
            name="bsl-phase9",
            description="BSL Phase 9 model - GGUF",
            size_gb=4.0,
            model_type="gguf",
            gguf_path="bsl-phases/bsl_phase9.Q4_K_M.gguf",
        ),
        "director-v4": ModelInfo(
            name="director-v4",
            description="Director v4 model - GGUF",
            size_gb=4.0,
            model_type="gguf",
            gguf_path="directors/director_v4.Q4_K_M.gguf",
        ),
        "director-v5": ModelInfo(
            name="director-v5",
            description="Director v5 model - GGUF",
            size_gb=4.0,
            model_type="gguf",
            gguf_path="directors/director_v5.Q4_K_M.gguf",
        ),
        "scenespeak-queryd": ModelInfo(
            name="scenespeak-queryd",
            description="SceneSpeak QueryD model - GGUF",
            size_gb=4.0,
            model_type="gguf",
            gguf_path="scene-speak/scenespeak_queryd.Q4_K_M.gguf",
        ),
    }

    def __init__(
        self,
        gguf_base_path: Optional[str] = None,
        ollama_endpoint: str = "http://localhost:11434",
        env_file: Optional[str] = None
    ):
        """
        Initialize ModelManager

        Args:
            gguf_base_path: Base path to GGUF models directory
            ollama_endpoint: Ollama API endpoint
            env_file: Path to .env file (default: ../.env from script location)
        """
        default_base = Path.home() / "Project_Chimera_Downloads" / "LLM Models" / "gguf"
        self.gguf_base_path = Path(gguf_base_path or os.getenv("CHIMERA_GGUF_BASE", str(default_base)))
        self.ollama_endpoint = ollama_endpoint.rstrip("/")

        # Find .env file
        if env_file is None:
            script_dir = Path(__file__).parent
            env_file = script_dir.parent / ".env"
        self.env_file = Path(env_file)

        # Update loaded status
        self._update_loaded_status()

    def _update_loaded_status(self):
        """Update is_loaded status for all models"""
        try:
            response = httpx.get(f"{self.ollama_endpoint}/api/tags", timeout=5.0)
            if response.status_code == 200:
                loaded_models = response.json().get("models", [])
                loaded_names = {m.get("name") for m in loaded_models}

                for model_info in self.MODELS.values():
                    model_info.is_loaded = model_info.name in loaded_names
        except Exception as e:
            logger.warning(f"Failed to get loaded models: {e}")

    def list_models(self, model_type: Optional[str] = None) -> List[ModelInfo]:
        """
        List available models

        Args:
            model_type: Filter by model type ("ollama" or "gguf")

        Returns:
            List of ModelInfo objects
        """
        models = list(self.MODELS.values())

        if model_type:
            models = [m for m in models if m.model_type == model_type]

        return models

    def get_model(self, model_name: str) -> Optional[ModelInfo]:
        """
        Get model information

        Args:
            model_name: Name of the model

        Returns:
            ModelInfo if found, None otherwise
        """
        return self.MODELS.get(model_name)

    def check_gguf_file(self, model_name: str) -> bool:
        """
        Check if GGUF file exists for a model

        Args:
            model_name: Name of the model

        Returns:
            True if GGUF file exists, False otherwise
        """
        model = self.get_model(model_name)
        if not model or model.model_type != "gguf":
            return False

        gguf_path = self.gguf_base_path / model.gguf_path
        return gguf_path.exists()

    def load_model(self, model_name: str, timeout: int = 300) -> bool:
        """
        Load a GGUF model into Ollama

        Args:
            model_name: Name of the model to load
            timeout: Timeout in seconds for the load operation

        Returns:
            True if successful, False otherwise
        """
        model = self.get_model(model_name)
        if not model:
            logger.error(f"Unknown model: {model_name}")
            return False

        if model.model_type != "gguf":
            logger.warning(f"Model {model_name} is not a GGUF model")
            return False

        if model.is_loaded:
            logger.info(f"Model {model_name} is already loaded")
            return True

        if not self.check_gguf_file(model_name):
            logger.error(f"GGUF file not found for model: {model_name}")
            return False

        gguf_path = self.gguf_base_path / model.gguf_path

        try:
            logger.info(f"Loading model {model_name} from {gguf_path}")
            result = subprocess.run(
                ["ollama", "create", model_name, "--from", str(gguf_path)],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0:
                logger.info(f"Successfully loaded model {model_name}")
                model.is_loaded = True
                return True
            else:
                logger.error(f"Failed to load model: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Model loading timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def unload_model(self, model_name: str) -> bool:
        """
        Unload a model from Ollama

        Args:
            model_name: Name of the model to unload

        Returns:
            True if successful, False otherwise
        """
        try:
            result = subprocess.run(
                ["ollama", "rm", model_name],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                logger.info(f"Successfully unloaded model {model_name}")
                model = self.get_model(model_name)
                if model:
                    model.is_loaded = False
                return True
            else:
                logger.error(f"Failed to unload model: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Failed to unload model: {e}")
            return False

    def switch_model(self, model_name: str, load_if_needed: bool = True) -> bool:
        """
        Switch to a different model (update .env file)

        Args:
            model_name: Name of the model to switch to
            load_if_needed: Load the model if not already loaded

        Returns:
            True if successful, False otherwise
        """
        model = self.get_model(model_name)
        if not model:
            logger.error(f"Unknown model: {model_name}")
            return False

        # Load GGUF models if needed
        if model.model_type == "gguf" and load_if_needed and not model.is_loaded:
            logger.info(f"Model {model_name} not loaded, loading now...")
            if not self.load_model(model_name):
                return False

        # Update .env file
        try:
            env_content = self.env_file.read_text() if self.env_file.exists() else ""

            # Update or add OLLAMA_MODEL line
            lines = env_content.splitlines()
            updated = False

            for i, line in enumerate(lines):
                if line.startswith("OLLAMA_MODEL="):
                    lines[i] = f"OLLAMA_MODEL={model_name}"
                    updated = True
                    break

            if not updated:
                lines.append(f"OLLAMA_MODEL={model_name}")

            self.env_file.write_text("\n".join(lines))
            logger.info(f"Updated .env with OLLAMA_MODEL={model_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update .env file: {e}")
            return False

    def test_model(self, model_name: str, prompt: str = "Say hello in one sentence.") -> bool:
        """
        Test a model with a simple prompt

        Args:
            model_name: Name of the model to test
            prompt: Test prompt

        Returns:
            True if test passed, False otherwise
        """
        try:
            result = subprocess.run(
                ["ollama", "run", model_name, prompt],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0 and result.stdout.strip():
                logger.info(f"Model {model_name} test passed")
                logger.info(f"Response: {result.stdout.strip()}")
                return True
            else:
                logger.error(f"Model {model_name} test failed")
                return False

        except Exception as e:
            logger.error(f"Model test failed: {e}")
            return False

    def get_status(self) -> Dict:
        """
        Get current status of models and configuration

        Returns:
            Dict with status information
        """
        status = {
            "ollama_endpoint": self.ollama_endpoint,
            "ollama_running": False,
            "gguf_base_path": str(self.gguf_base_path),
            "loaded_models": [],
            "current_model": None,
        }

        # Check Ollama
        try:
            response = httpx.get(f"{self.ollama_endpoint}/api/tags", timeout=5.0)
            if response.status_code == 200:
                status["ollama_running"] = True
                loaded_models = response.json().get("models", [])
                status["loaded_models"] = [m.get("name") for m in loaded_models]
        except Exception:
            pass

        # Get current model from .env
        if self.env_file.exists():
            env_content = self.env_file.read_text()
            for line in env_content.splitlines():
                if line.startswith("OLLAMA_MODEL="):
                    status["current_model"] = line.split("=", 1)[1].strip()
                    break

        return status


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="NemoClaw Model Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List command
    subparsers.add_parser("list", help="List all available models")

    # Load command
    load_parser = subparsers.add_parser("load", help="Load a model into Ollama")
    load_parser.add_argument("model", help="Model name to load")

    # Unload command
    unload_parser = subparsers.add_parser("unload", help="Unload a model from Ollama")
    unload_parser.add_argument("model", help="Model name to unload")

    # Switch command
    switch_parser = subparsers.add_parser("switch", help="Switch to a different model")
    switch_parser.add_argument("model", help="Model name to switch to")

    # Test command
    test_parser = subparsers.add_parser("test", help="Test a model")
    test_parser.add_argument("model", help="Model name to test")

    # Status command
    subparsers.add_parser("status", help="Show current status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s"
    )

    manager = ModelManager()

    if args.command == "list":
        print("\n=== Available Models ===\n")
        print("Ollama Built-in Models:")
        for model in manager.list_models("ollama"):
            status = "[LOADED]" if model.is_loaded else "[AVAILABLE]"
            print(f"  {status} {model.name} - {model.description}")

        print("\nGGUF Models:")
        for model in manager.list_models("gguf"):
            status = "[LOADED]" if model.is_loaded else "[NOT LOADED]"
            print(f"  {status} {model.name} - {model.description}")

    elif args.command == "load":
        if manager.load_model(args.model):
            print(f"✓ Successfully loaded model: {args.model}")
            sys.exit(0)
        else:
            print(f"✗ Failed to load model: {args.model}")
            sys.exit(1)

    elif args.command == "unload":
        if manager.unload_model(args.model):
            print(f"✓ Successfully unloaded model: {args.model}")
            sys.exit(0)
        else:
            print(f"✗ Failed to unload model: {args.model}")
            sys.exit(1)

    elif args.command == "switch":
        if manager.switch_model(args.model):
            print(f"✓ Switched to model: {args.model}")
            print("Restart NemoClaw service to apply changes")
            sys.exit(0)
        else:
            print(f"✗ Failed to switch to model: {args.model}")
            sys.exit(1)

    elif args.command == "test":
        if manager.test_model(args.model):
            print(f"✓ Model test passed: {args.model}")
            sys.exit(0)
        else:
            print(f"✗ Model test failed: {args.model}")
            sys.exit(1)

    elif args.command == "status":
        status = manager.get_status()
        print("\n=== NemoClaw Model Status ===\n")
        print(f"Ollama Service: {'Running' if status['ollama_running'] else 'Stopped'}")
        print(f"GGUF Base Path: {status['gguf_base_path']}")
        print(f"\nLoaded Models: {', '.join(status['loaded_models']) or 'None'}")
        print(f"Current Model: {status['current_model'] or 'Not set'}")


if __name__ == "__main__":
    main()
