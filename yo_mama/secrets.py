# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0
"""
Secrets management for AWS Secrets Manager, HashiCorp Vault, and Doppler.

Priority order for secrets:
1. Doppler (if DOPPLER_TOKEN is set) - HIGHEST PRIORITY
2. AWS Secrets Manager (if SECRETS_MANAGER=aws)
3. HashiCorp Vault (if SECRETS_MANAGER=vault)
4. Environment variables from .env file - FALLBACK
5. Default values - LAST RESORT
"""

import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def load_secrets_from_aws(secret_name: str) -> Dict[str, Any]:
    """
    Load secrets from AWS Secrets Manager.
    
    Args:
        secret_name: Name of the secret in AWS Secrets Manager
        
    Returns:
        Dict of secrets or empty dict on error
    """
    try:
        import boto3
        
        client = boto3.client('secretsmanager')
        response = client.get_secret_value(SecretId=secret_name)
        secrets = json.loads(response['SecretString'])
        logger.debug(f"Successfully loaded AWS secret: {secret_name}")
        return secrets  # lgtm[py/clear-text-logging-sensitive-data]
    except ImportError:
        logger.warning("boto3 not installed. Install with: pip install boto3")
        return {}
    except Exception as e:
        logger.error(f"Failed to load AWS secret '{secret_name}': {type(e).__name__}")
        return {}


def load_secrets_from_vault(secret_path: str) -> Dict[str, Any]:
    """
    Load secrets from HashiCorp Vault.
    
    Args:
        secret_path: Path to the secret in Vault (e.g., 'secret/data/myapp')
        
    Returns:
        Dict of secrets or empty dict on error
    """
    try:
        import hvac
        
        vault_url = os.getenv('SECRETS_VAULT_URL')
        vault_token = os.getenv('SECRETS_VAULT_TOKEN')
        
        if not vault_url or not vault_token:
            logger.error("SECRETS_VAULT_URL or SECRETS_VAULT_TOKEN not configured")
            return {}
        
        client = hvac.Client(url=vault_url, token=vault_token)
        if not client.is_authenticated():
            logger.error("Vault authentication failed")
            return {}
        
        response = client.secrets.kv.v2.read_secret_version(path=secret_path)
        secrets = response['data']['data']
        logger.debug(f"Successfully loaded Vault secret: {secret_path}")
        return secrets  # lgtm[py/clear-text-logging-sensitive-data]
    except ImportError:
        logger.warning("hvac not installed. Install with: pip install hvac")
        return {}
    except Exception as e:
        logger.error(f"Failed to load Vault secret '{secret_path}': {type(e).__name__}")
        return {}


def load_secrets_from_doppler(secret_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Load secrets from Doppler.
    
    Args:
        secret_name: Optional prefix to filter secrets (e.g., 'DISCORD' for DISCORD_*)
        
    Returns:
        Dict of secrets or empty dict on error
    """
    try:
        from dopplersdk import DopplerSDK
        
        doppler_token = os.getenv('DOPPLER_TOKEN')
        if not doppler_token:
            logger.debug("DOPPLER_TOKEN not set")
            return {}
        
        # Get Doppler project and config from environment
        doppler_project = os.getenv('DOPPLER_PROJECT', 'yo-mama-bot')
        doppler_config = os.getenv('DOPPLER_CONFIG', 'dev')
        
        sdk = DopplerSDK()
        sdk.set_access_token(doppler_token)
        
        # Fetch secrets from the specified project and config
        try:
            secrets_response = sdk.secrets.list(
                project=doppler_project,
                config=doppler_config
            )
            
            secrets_dict = {}
            if hasattr(secrets_response, 'secrets'):
                all_keys = list(secrets_response.secrets.keys())
                logger.info(f"Doppler connection successful. Found {len(all_keys)} total secrets")
                
                for secret_key, secret_value in secrets_response.secrets.items():
                    # If secret_name prefix is provided, filter by it
                    if secret_name:
                        if secret_key.upper().startswith(secret_name.upper()):
                            # Extract the actual key name (e.g., CLIENT_ID from DISCORD_CLIENT_ID)
                            key_suffix = secret_key[len(secret_name)+1:].lower()  # +1 for underscore
                            secrets_dict[key_suffix] = secret_value.get('computed', secret_value.get('raw', ''))
                    else:
                        # Return all secrets with their full names
                        secrets_dict[secret_key] = secret_value.get('computed', secret_value.get('raw', ''))
                
                if secret_name and not secrets_dict:
                    logger.debug(f"No secrets found with prefix '{secret_name}'")
                
                return secrets_dict  # lgtm[py/clear-text-logging-sensitive-data]
            else:
                logger.warning("No secrets found in Doppler response")
                return {}
                
        except Exception as e:
            logger.error(f"Failed to fetch Doppler secrets: {type(e).__name__}: {e}")
            return {}
            
    except ImportError:
        logger.warning("dopplersdk not installed. Install with: pip install doppler-sdk")
        return {}
    except Exception as e:
        logger.error(f"Failed to configure Doppler: {type(e).__name__}: {e}")
        return {}


def get_secret(
    key: str,
    platform: Optional[str] = None,
    default: Optional[str] = None,
    aws_secret_name: Optional[str] = None,
    vault_secret_path: Optional[str] = None,
    doppler_prefix: Optional[str] = None
) -> Optional[str]:
    """
    Get a secret value with comprehensive priority system.
    
    Priority order:
    1. Doppler (if DOPPLER_TOKEN exists) - HIGHEST PRIORITY
    2. AWS Secrets Manager (if SECRETS_MANAGER=aws and aws_secret_name provided)
    3. HashiCorp Vault (if SECRETS_MANAGER=vault and vault_secret_path provided)
    4. Environment variable from .env file - FALLBACK
    5. Default value - LAST RESORT
    
    Args:
        key: Secret key to retrieve (e.g., 'api_key', 'bot_token')
        platform: Optional platform name for env var construction (e.g., 'discord')
        default: Default value if not found anywhere
        aws_secret_name: AWS Secrets Manager secret name
        vault_secret_path: HashiCorp Vault secret path
        doppler_prefix: Doppler secret prefix (e.g., 'DISCORD' for DISCORD_BOT_TOKEN)
        
    Returns:
        Secret value or default
        
    Examples:
        # Simple lookup with env var fallback
        api_key = get_secret('GEMINI_API_KEY')
        
        # Platform-specific with all secret managers
        token = get_secret(
            'bot_token',
            platform='discord',
            aws_secret_name='prod/discord',
            vault_secret_path='secret/discord',
            doppler_prefix='DISCORD'
        )
    """
    try:
        # Construct environment variable name
        if platform:
            env_key = f"{platform.upper()}_{key.upper()}"
        else:
            env_key = key.upper()
        
        # Priority 1: Try Doppler first if DOPPLER_TOKEN exists
        if os.getenv('DOPPLER_TOKEN'):
            # Try with doppler_prefix if provided
            if doppler_prefix:
                doppler_secrets = load_secrets_from_doppler(doppler_prefix)
                # Look for the key with or without prefix
                if key.lower() in doppler_secrets:
                    value = doppler_secrets[key.lower()]
                    if value:
                        logger.debug(f"Found {env_key} in Doppler (with prefix)")
                        return value
            
            # Try direct key lookup in all Doppler secrets
            all_doppler_secrets = load_secrets_from_doppler()
            if env_key in all_doppler_secrets:
                value = all_doppler_secrets[env_key]
                if value:
                    logger.debug(f"Found {env_key} in Doppler (direct)")
                    return value
        
        # Check which secrets manager is enabled (AWS/Vault)
        secret_manager = os.getenv('SECRETS_MANAGER', 'none').lower()
        
        # Priority 2: Try AWS Secrets Manager
        if secret_manager == 'aws' and aws_secret_name:
            aws_secrets = load_secrets_from_aws(aws_secret_name)
            if key.lower() in aws_secrets:
                value = aws_secrets[key.lower()]
                if value:
                    logger.debug(f"Found {env_key} in AWS Secrets Manager")
                    return value
            # Also try with the full env key
            if env_key.lower() in aws_secrets:
                value = aws_secrets[env_key.lower()]
                if value:
                    logger.debug(f"Found {env_key} in AWS Secrets Manager")
                    return value
        
        # Priority 3: Try HashiCorp Vault
        if secret_manager == 'vault' and vault_secret_path:
            vault_secrets = load_secrets_from_vault(vault_secret_path)
            if key.lower() in vault_secrets:
                value = vault_secrets[key.lower()]
                if value:
                    logger.debug(f"Found {env_key} in Vault")
                    return value
            # Also try with the full env key
            if env_key.lower() in vault_secrets:
                value = vault_secrets[env_key.lower()]
                if value:
                    logger.debug(f"Found {env_key} in Vault")
                    return value
        
        # Priority 4: Fallback to environment variable (.env file)
        env_value = os.getenv(env_key)
        if env_value:
            logger.debug(f"Found {env_key} in environment")
            return env_value
        
        # Priority 5: Return default
        if default:
            logger.debug(f"Using default value for {env_key}")
        else:
            logger.debug(f"Secret {env_key} not found anywhere")
        
        return default
        
    except Exception as e:
        logger.error(f"Error getting secret '{key}': {type(e).__name__}: {e}")
        return default


def get_secrets_for_platform(
    platform: str,
    keys: list[str],
    aws_secret_name: Optional[str] = None,
    vault_secret_path: Optional[str] = None
) -> Dict[str, Optional[str]]:
    """
    Get multiple secrets for a platform at once.
    
    Args:
        platform: Platform name (e.g., 'discord', 'matrix')
        keys: List of secret keys to retrieve
        aws_secret_name: Optional AWS secret name
        vault_secret_path: Optional Vault secret path
        
    Returns:
        Dictionary of key -> value mappings
        
    Example:
        secrets = get_secrets_for_platform(
            'discord',
            ['bot_token', 'client_id', 'client_secret'],
            aws_secret_name='prod/discord'
        )
    """
    result = {}
    for key in keys:
        result[key] = get_secret(
            key,
            platform=platform,
            aws_secret_name=aws_secret_name,
            vault_secret_path=vault_secret_path,
            doppler_prefix=platform.upper()
        )
    return result


# Convenience functions for common use cases

def get_doppler_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a secret from Doppler only."""
    secrets = load_secrets_from_doppler()
    return secrets.get(key.upper(), default)


def get_aws_secret(secret_name: str, key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a specific key from an AWS secret."""
    secrets = load_secrets_from_aws(secret_name)
    return secrets.get(key.lower(), default)


def get_vault_secret(secret_path: str, key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a specific key from a Vault secret."""
    secrets = load_secrets_from_vault(secret_path)
    return secrets.get(key.lower(), default)
