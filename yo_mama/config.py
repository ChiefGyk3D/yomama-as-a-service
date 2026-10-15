# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0
"""
Configuration management with comprehensive secrets manager support.

Priority order:
1. Doppler Secrets Manager (if DOPPLER_TOKEN is set) - HIGHEST PRIORITY
2. AWS Secrets Manager (if SECRETS_MANAGER=aws)
3. HashiCorp Vault (if SECRETS_MANAGER=vault)
4. Environment variables from .env file - FALLBACK
5. Default values - LAST RESORT
"""

import logging
import os

from dotenv import load_dotenv

# Import our comprehensive secrets manager
from .secrets import get_secret, load_secrets_from_doppler

# Load .env file
load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """
    Configuration manager with comprehensive secrets manager support.
    
    Supports Doppler, AWS Secrets Manager, HashiCorp Vault, and .env fallback.
    """
    
    def __init__(self):
        # Check which secrets managers are available
        self._has_doppler = bool(os.getenv('DOPPLER_TOKEN'))
        self._secrets_manager = os.getenv('SECRETS_MANAGER', 'none').lower()
        
        if self._has_doppler:
            doppler_secrets = load_secrets_from_doppler()
            logger.info(f"Doppler enabled with {len(doppler_secrets)} secrets")
        
        if self._secrets_manager == 'aws':
            logger.info("AWS Secrets Manager enabled")
        elif self._secrets_manager == 'vault':
            logger.info("HashiCorp Vault enabled")
    
    def get_secret(self, key: str, default: str | None = None) -> str | None:
        """
        Get a secret value with comprehensive priority system.
        
        Priority:
        1. Doppler (if DOPPLER_TOKEN is set)
        2. AWS Secrets Manager (if SECRETS_MANAGER=aws)
        3. HashiCorp Vault (if SECRETS_MANAGER=vault)
        4. Environment variable from .env
        5. Default value
        
        Args:
            key: Secret key name
            default: Default value if not found
            
        Returns:
            Secret value or default
        """
        return get_secret(key, default=default)
    
    def get_config(self, key: str, default: str | None = None) -> str | None:
        """
        Alias for get_secret for configuration values.
        
        Args:
            key: Config key name
            default: Default value if not found
            
        Returns:
            Config value or default
        """
        return self.get_secret(key, default)
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        Get a boolean configuration value.
        
        Args:
            key: Config key name
            default: Default value if not found
            
        Returns:
            Boolean value
        """
        value = self.get_secret(key)
        if value is None:
            return default
        
        return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
    
    def get_int(self, key: str, default: int = 0) -> int:
        """
        Get an integer configuration value.
        
        Args:
            key: Config key name
            default: Default value if not found
            
        Returns:
            Integer value
        """
        value = self.get_secret(key)
        if value is None:
            return default
        
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Invalid integer value for {key}")
            return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """
        Get a floating-point configuration value.
        
        Args:
            key: Config key name
            default: Default value if not found
            
        Returns:
            Float value
        """
        value = self.get_secret(key)
        if value is None:
            return default
        
        try:
            return float(value)
        except ValueError:
            logger.warning(f"Invalid float value for {key}")
            return default
    
    # Specific configuration getters

    @property
    def llm_provider(self) -> str:
        """Primary LLM provider: 'ollama' or 'gemini'."""
        return (self.get_secret('LLM_PROVIDER', 'gemini') or 'gemini').lower()

    @property
    def llm_fallback_providers(self) -> list[str]:
        """Opt-in fallback provider chain, e.g. 'gemini' or 'gemini,ollama'."""
        raw = self.get_secret('LLM_FALLBACK_PROVIDER', '') or ''
        return [name.strip().lower() for name in raw.split(',') if name.strip()]

    @property
    def gemini_api_key(self) -> str | None:
        """Get Google Gemini API key."""
        return self.get_secret('GEMINI_API_KEY')
    
    @property
    def gemini_model(self) -> str:
        """Get Gemini model name."""
        return self.get_secret('GEMINI_MODEL', 'gemini-2.5-flash-lite')
    
    @property
    def default_flavor(self) -> str:
        """Get default joke flavor."""
        return self.get_secret('DEFAULT_FLAVOR', 'tech')
    
    @property
    def default_meanness(self) -> int:
        """Get default meanness level."""
        return self.get_int('DEFAULT_MEANNESS', 5)
    
    @property
    def default_nerdiness(self) -> int:
        """Get default nerdiness level."""
        return self.get_int('DEFAULT_NERDINESS', 5)
    
    @property
    def log_level(self) -> str:
        """Get logging level."""
        return self.get_secret('LOG_LEVEL', 'INFO')
    
    # Discord drive-by replies: every so often the bot turns a random human
    # message into a Yo Mama joke. See yo_mama/random_riff.py.

    @property
    def discord_random_reply_chance(self) -> float:
        """Probability (0-1) that a human message gets a Yo Mama riff. 0 disables."""
        return self.get_float('DISCORD_RANDOM_REPLY_CHANCE', 0.02)

    @property
    def discord_random_reply_cooldown(self) -> int:
        """Seconds a channel stays quiet after the bot riffs there."""
        return self.get_int('DISCORD_RANDOM_REPLY_COOLDOWN', 600)

    @property
    def discord_random_reply_channels(self) -> list[int]:
        """Channel IDs the bot may riff in (comma-separated). Empty means all."""
        raw = self.get_secret('DISCORD_RANDOM_REPLY_CHANNELS', '') or ''
        channels = []
        for part in raw.split(','):
            part = part.strip()
            if not part:
                continue
            try:
                channels.append(int(part))
            except ValueError:
                logger.warning(f"Ignoring non-numeric channel ID in DISCORD_RANDOM_REPLY_CHANNELS: {part!r}")
        return channels

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate that all required configuration is present.
        
        Returns:
            Tuple of (is_valid, list of missing keys)
        """
        # A Gemini API key is only required if Gemini is actually in the
        # provider chain. An Ollama-only setup needs no cloud credentials.
        required_keys = []
        if 'gemini' in [self.llm_provider] + self.llm_fallback_providers:
            required_keys.append('GEMINI_API_KEY')

        missing = []

        for key in required_keys:
            if not self.get_secret(key):
                missing.append(key)
        
        is_valid = len(missing) == 0
        return is_valid, missing


# Global config instance
_config_instance = None


def get_config() -> Config:
    """Get the global config instance (singleton pattern)."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def reset_config():
    """Reset the global config instance (useful for testing)."""
    global _config_instance
    _config_instance = None
