"""
Configuration loader for the finance tracker application.

Manages loading and accessing application configuration from files and environment.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Load and manage application configuration.

    Supports JSON configuration files and environment variable overrides.
    """

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize config loader.

        Args:
            config_file: Path to JSON config file (optional).
        """
        self.config_file = config_file
        self.config: Dict[str, Any] = {}

        if config_file:
            self.load_config(config_file)

    def load_config(self, config_file: str) -> None:
        """
        Load configuration from a JSON file.

        Args:
            config_file: Path to JSON configuration file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            json.JSONDecodeError: If config file is invalid JSON.
        """
        config_path = Path(config_file)

        if not config_path.exists():
            logger.warning(f"Config file not found: {config_file}")
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
            logger.info(f"Loaded configuration from {config_file}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Supports dot notation for nested values (e.g., 'categorizer.fuzzy_threshold').

        Args:
            key: Configuration key (supports dot notation).
            default: Default value if key not found.

        Returns:
            Configuration value or default.
        """
        if "." in key:
            return self._get_nested(key, default)

        return self.config.get(key, default)

    def _get_nested(self, key: str, default: Any = None) -> Any:
        """
        Get nested configuration value using dot notation.

        Args:
            key: Dot-notation key (e.g., 'db.host').
            default: Default value if key not found.

        Returns:
            Configuration value or default.
        """
        parts = key.split(".")
        value = self.config

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return default

            if value is None:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: Configuration key.
            value: Value to set.
        """
        self.config[key] = value

    def save_config(self, output_file: str) -> None:
        """
        Save current configuration to a JSON file.

        Args:
            output_file: Path for output config file.
        """
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved configuration to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise

    def merge_config(self, other_config: Dict[str, Any]) -> None:
        """
        Merge another configuration dict into current config.

        Args:
            other_config: Configuration dictionary to merge.
        """
        self.config.update(other_config)


def create_default_config() -> Dict[str, Any]:
    """
    Create a default configuration dictionary.

    Returns:
        Default configuration with sensible defaults.
    """
    return {
        "categorizer": {
            "fuzzy_threshold": 80,
            "merchant_memory_file": "data/merchant_memory.json",
        },
        "parser": {
            "bank_format": "rbc",
            "encoding": "utf-8",
        },
        "export": {
            "default_format": "xlsx",
            "output_dir": "output",
        },
    }
