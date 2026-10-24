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
from .secrets import (
    MissingSecretError,
    get_secret,
    is_placeholder,
    load_secrets_from_doppler,
)

# Load .env file
load_dotenv()

logger = logging.getLogger(__name__)


def _id_list(raw: str | None) -> list[str]:
    """Split a comma separated setting into trimmed, non-empty items."""
    return [item.strip() for item in (raw or '').split(',') if item.strip()]


class Config:
    """
    Configuration manager with comprehensive secrets manager support.
    
    Supports Doppler, AWS Secrets Manager, HashiCorp Vault, and .env fallback.
    """
    
    def __init__(self):
        # Check which secrets managers are available
        self._has_doppler = not is_placeholder(os.getenv('DOPPLER_TOKEN'))
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
        """Google Gemini API key, or None when unset, empty or a placeholder."""
        value = self.get_secret('GEMINI_API_KEY')
        if value and is_placeholder(value):
            logger.warning("GEMINI_API_KEY is a placeholder; treating it as unset")
            return None
        return value or None
    
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
    
    # Abuse controls (threat model t4 and t6). Conservative defaults.

    @property
    def rate_limit_cooldown(self) -> int:
        """Seconds a user must wait between generations; 0 disables."""
        return max(0, self.get_int('RATE_LIMIT_COOLDOWN_SECONDS', 10))

    @property
    def max_concurrent_generations(self) -> int:
        """Generations allowed to run at once across all users (minimum 1)."""
        return max(1, self.get_int('MAX_CONCURRENT_GENERATIONS', 2))

    @property
    def batch_max_count(self) -> int:
        """Largest /batch size. Defaults to 5; never above the hard ceiling of 10."""
        return min(10, max(1, self.get_int('BATCH_MAX_COUNT', 5)))

    @property
    def discord_guild_only(self) -> bool:
        """Refuse Discord commands outside a server (no DMs)."""
        return self.get_bool('DISCORD_GUILD_ONLY', True)

    @property
    def discord_allowed_guilds(self) -> list[str]:
        """Guild ids allowed to use the bot; empty means any guild."""
        return _id_list(self.get_secret('DISCORD_ALLOWED_GUILDS', ''))

    @property
    def discord_allowed_channels(self) -> list[str]:
        """Channel ids allowed to use the bot; empty means any channel."""
        return _id_list(self.get_secret('DISCORD_ALLOWED_CHANNELS', ''))

    @property
    def discord_optout_file(self) -> str | None:
        """JSON file for the opt-out list; unset keeps it in memory only."""
        return self.get_secret('DISCORD_OPTOUT_FILE', '') or None

    @property
    def matrix_auto_join(self) -> bool:
        """Join rooms the bot is invited to (subject to the allowlist)."""
        return self.get_bool('MATRIX_AUTO_JOIN', True)

    @property
    def matrix_auto_join_allowlist(self) -> list[str]:
        """Matrix user ids (@u:server) or server names whose invites are accepted."""
        return [item.lower() for item in _id_list(self.get_secret('MATRIX_AUTO_JOIN_ALLOWLIST', ''))]

    @property
    def matrix_auto_join_allow_all(self) -> bool:
        """Accept every invite (the old behavior). Off unless set explicitly."""
        return self.get_bool('MATRIX_AUTO_JOIN_ALLOW_ALL', False)

    @property
    def matrix_ignore_senders(self) -> list[str]:
        """Matrix user ids whose messages are ignored (other bots)."""
        return [item.lower() for item in _id_list(self.get_secret('MATRIX_IGNORE_SENDERS', ''))]

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
            if is_placeholder(self.get_secret(key)):
                missing.append(key)
        
        is_valid = len(missing) == 0
        return is_valid, missing

    def require_valid(self) -> None:
        """Raise MissingSecretError naming each missing required key (never a value)."""
        is_valid, missing = self.validate()
        if not is_valid:
            raise MissingSecretError(
                f"Required secret(s) empty, unset or still a placeholder: {', '.join(missing)}")


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
