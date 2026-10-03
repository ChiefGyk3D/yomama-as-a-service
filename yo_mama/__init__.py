# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0
"""
Yo Mama Bot - AI-powered joke generator with customizable flavors and intensity.

Generate hilarious Yo Mama jokes with adjustable meanness and nerdiness levels
across multiple themes: cybersecurity, tech, Linux, gaming, and more.
"""

__version__ = "1.0.0"
__author__ = "chiefgyk3d"
__description__ = "AI-powered Yo Mama joke generator using Google Gemini"

from .config import Config, get_config
from .secrets import (
    get_secret,
    get_secrets_for_platform,
    load_secrets_from_aws,
    load_secrets_from_doppler,
    load_secrets_from_vault,
)
from .yo_mama_generator import YoMamaGenerator

__all__ = [
    'Config',
    'YoMamaGenerator',
    'get_config',
    'get_secret',
    'get_secrets_for_platform',
    'load_secrets_from_aws',
    'load_secrets_from_doppler',
    'load_secrets_from_vault'
]
