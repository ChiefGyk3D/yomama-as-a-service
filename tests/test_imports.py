# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0
"""
Test that all required modules can be imported.
"""

import unittest


class TestImports(unittest.TestCase):
    """Test that all dependencies are installed and importable."""
    
    def test_google_genai(self):
        """Test google-genai import."""
        try:
            from google import genai  # noqa: F401  # the import is the test
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import google.genai: {e}")
    
    def test_dopplersdk(self):
        """Test dopplersdk import."""
        try:
            from dopplersdk import DopplerSDK  # noqa: F401  # the import is the test
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import dopplersdk: {e}")
    
    def test_dotenv(self):
        """Test python-dotenv import."""
        try:
            from dotenv import load_dotenv  # noqa: F401  # the import is the test
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import dotenv: {e}")
    
    def test_discord(self):
        """Test discord.py import."""
        try:
            import discord  # noqa: F401  # the import is the test
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import discord: {e}")
    
    def test_matrix_nio(self):
        """Test matrix-nio import."""
        try:
            import nio  # noqa: F401  # the import is the test
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import nio: {e}")
    
    def test_yo_mama_config(self):
        """Test yo_mama.config import."""
        try:
            from yo_mama.config import (
                get_config,  # noqa: F401  # the import is the test
            )
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import yo_mama.config: {e}")
    
    def test_yo_mama_generator(self):
        """Test yo_mama.yo_mama_generator import."""
        try:
            from yo_mama.yo_mama_generator import (
                YoMamaGenerator,  # noqa: F401  # the import is the test
            )
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import yo_mama.yo_mama_generator: {e}")
    
    def test_yo_mama_platforms(self):
        """Test yo_mama.platforms import."""
        try:
            from yo_mama.platforms import (  # noqa: F401  # the import is the test
                DiscordBot,
                MatrixBot,
            )
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import yo_mama.platforms: {e}")


if __name__ == '__main__':
    unittest.main()
