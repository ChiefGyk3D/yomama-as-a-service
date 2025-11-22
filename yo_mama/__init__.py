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

from .yo_mama_generator import YoMamaGenerator
from .config import get_config, Config
from .secrets import (
    get_secret,
    load_secrets_from_doppler,
    load_secrets_from_aws,
    load_secrets_from_vault,
    get_secrets_for_platform
)

__all__ = [
    'YoMamaGenerator',
    'get_config',
    'Config',
    'get_secret',
    'load_secrets_from_doppler',
    'load_secrets_from_aws',
    'load_secrets_from_vault',
    'get_secrets_for_platform'
]
