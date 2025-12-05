"""Configuration management for Lambda Labs CLI."""
import json
from pathlib import Path
from typing import Optional


CONFIG_DIR = Path.home() / ".lambda"
CONFIG_FILE = CONFIG_DIR / "config.json"


class ConfigError(Exception):
    """Exception raised for configuration errors."""
    pass


def ensure_config_dir() -> None:
    """Ensure the config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def save_api_key(api_key: str) -> None:
    """Save the API key to the config file.

    Args:
        api_key: Lambda Labs Cloud API key

    Raises:
        ConfigError: If saving fails
    """
    try:
        ensure_config_dir()
        config = {"api_key": api_key}
        CONFIG_FILE.write_text(json.dumps(config, indent=2))
        CONFIG_FILE.chmod(0o600)  # Restrict permissions to user only
    except Exception as e:
        raise ConfigError(f"Failed to save API key: {str(e)}") from e


def load_api_key() -> Optional[str]:
    """Load the API key from the config file.

    Returns:
        API key if found, None otherwise

    Raises:
        ConfigError: If loading fails
    """
    if not CONFIG_FILE.exists():
        return None

    try:
        config = json.loads(CONFIG_FILE.read_text())
        return config.get("api_key")
    except Exception as e:
        raise ConfigError(f"Failed to load API key: {str(e)}") from e


def get_api_key() -> str:
    """Get the API key from config.

    Returns:
        API key

    Raises:
        ConfigError: If API key is not configured
    """
    api_key = load_api_key()
    if not api_key:
        raise ConfigError(
            "API key not found. Please configure it with: lambda config set-key <api-key>"
        )
    return api_key


def clear_config() -> None:
    """Clear the configuration (delete the config file)."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
