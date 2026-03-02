"""Configuration loader for Lighting, Sound and Music service.

Loads and validates configuration from YAML files with environment
variable overrides.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = "./config.yaml"


class Config:
    """Configuration manager for LSM service."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or os.environ.get(
            "LSM_CONFIG_PATH",
            DEFAULT_CONFIG_PATH
        )
        self._config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from file."""
        if not Path(self.config_path).exists():
            logger.warning(
                f"Config file not found: {self.config_path}, using defaults"
            )
            self._config = self.get_default_config()
            return

        try:
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f) or {}

            # Apply environment variable overrides
            self._apply_env_overrides()

            logger.info(f"Loaded configuration from {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to load config: {e}, using defaults")
            self._config = self.get_default_config()

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides.

        Environment variables should be prefixed with LSM_ and use
        double underscores __ to denote nesting.

        Examples:
            LSM_SERVICE__PORT=8006
            LSM_LOGGING__LEVEL=DEBUG
        """
        for key, value in os.environ.items():
            if key.startswith("LSM_"):
                # Remove LSM_ prefix and split by __
                config_key = key[4:].lower()
                parts = config_key.split("__")

                # Navigate to nested location
                current = self._config
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]

                # Set value (convert to appropriate type)
                current[parts[-1]] = self._convert_value(value)

                logger.debug(f"Applied env override: {config_key}={value}")

    def _convert_value(self, value: str) -> Any:
        """Convert string value to appropriate type.

        Args:
            value: String value from environment

        Returns:
            Converted value (int, float, bool, or str)
        """
        # Try boolean
        if value.lower() in ("true", "yes", "on"):
            return True
        if value.lower() in ("false", "no", "off"):
            return False

        # Try integer
        try:
            return int(value)
        except ValueError:
            pass

        # Try float
        try:
            return float(value)
        except ValueError:
            pass

        # Return as string
        return value

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.

        Supports dot notation for nested keys (e.g., "service.port").

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        parts = key.split(".")
        current = self._config

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default

        return current

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section.

        Args:
            section: Section name

        Returns:
            Configuration section dict
        """
        return self._config.get(section, {})

    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Return default configuration.

        Returns:
            Default configuration dict
        """
        return {
            "service": {
                "name": "lighting-sound-music",
                "version": "0.1.0",
                "port": 8005,
                "host": "0.0.0.0",
                "debug": False
            },
            "lighting": {
                "enabled": True,
                "dmx_universe": 1,
                "sacn_enabled": True,
                "sacn_host": "127.0.0.1",
                "sacn_port": 5568,
                "default_fade_time": 1.0
            },
            "sound": {
                "enabled": True,
                "default_volume": 0.8,
                "max_concurrent_sounds": 8
            },
            "music": {
                "enabled": True,
                "default_model": "turbo",
                "cache_size_mb": 512
            },
            "cues": {
                "enabled": True,
                "max_concurrent_cues": 4,
                "default_fade_time": 1.0
            },
            "logging": {
                "level": "INFO",
                "console": {"enabled": True}
            },
            "cors": {
                "enabled": True,
                "origins": ["*"]
            },
            "health": {
                "liveness_interval": 30,
                "readiness_timeout": 5
            }
        }

    def reload(self) -> None:
        """Reload configuration from file."""
        logger.info("Reloading configuration...")
        self.load()

    @property
    def service_port(self) -> int:
        """Get service port."""
        return self.get("service.port", 8005)

    @property
    def service_host(self) -> str:
        """Get service host."""
        return self.get("service.host", "0.0.0.0")

    @property
    def debug_mode(self) -> bool:
        """Get debug mode."""
        return self.get("service.debug", False)

    @property
    def log_level(self) -> str:
        """Get log level."""
        return self.get("logging.level", "INFO")


# Global configuration instance
_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """Get global configuration instance.

    Args:
        config_path: Optional path to config file

    Returns:
        Configuration instance
    """
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config


def reload_config() -> None:
    """Reload global configuration."""
    global _config
    if _config is not None:
        _config.reload()
