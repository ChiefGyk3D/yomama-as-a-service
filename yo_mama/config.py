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

import os
import logging
from typing import Optional
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
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
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
    
    def get_config(self, key: str, default: Optional[str] = None) -> Optional[str]:
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
            logger.warning(f"Invalid integer value for {key}: {value}")
            return default
    
    # Specific configuration getters
    
    @property
    def gemini_api_key(self) -> Optional[str]:
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
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate that all required configuration is present.
        
        Returns:
            Tuple of (is_valid, list of missing keys)
        """
        required_keys = ['GEMINI_API_KEY']
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
