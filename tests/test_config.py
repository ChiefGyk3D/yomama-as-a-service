# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0
"""
Test configuration loading and validation.
"""

import os
import unittest
from unittest.mock import patch

from yo_mama.config import Config, get_config


class TestConfig(unittest.TestCase):
    """Test configuration functionality."""
    
    def test_config_loads(self):
        """Test that configuration can be loaded."""
        config = get_config()
        self.assertIsNotNone(config)
    
    def test_config_has_model(self):
        """Test that configuration has a model set."""
        config = get_config()
        self.assertIsNotNone(config.gemini_model)
        self.assertIsInstance(config.gemini_model, str)
        self.assertTrue(len(config.gemini_model) > 0)
    
    def test_config_has_defaults(self):
        """Test that configuration has default values."""
        config = get_config()
        self.assertIsNotNone(config.default_flavor)
        self.assertIsNotNone(config.default_meanness)
        self.assertIsNotNone(config.default_nerdiness)
        
        # Check ranges
        self.assertGreaterEqual(config.default_meanness, 1)
        self.assertLessEqual(config.default_meanness, 10)
        self.assertGreaterEqual(config.default_nerdiness, 1)
        self.assertLessEqual(config.default_nerdiness, 10)

    def test_random_reply_defaults(self):
        """Drive-by jokes default to a low chance with a per-channel cooldown."""
        env = {k: v for k, v in os.environ.items() if not k.startswith('DISCORD_RANDOM_REPLY')}
        with patch.dict(os.environ, env, clear=True):
            config = Config()
            self.assertAlmostEqual(config.discord_random_reply_chance, 0.02)
            self.assertEqual(config.discord_random_reply_cooldown, 600)
            self.assertEqual(config.discord_random_reply_channels, [])

    def test_random_reply_from_env(self):
        with patch.dict(os.environ, {
            'DISCORD_RANDOM_REPLY_CHANCE': '0.1',
            'DISCORD_RANDOM_REPLY_COOLDOWN': '30',
            'DISCORD_RANDOM_REPLY_CHANNELS': '123, 456,,abc',
        }):
            config = Config()
            self.assertAlmostEqual(config.discord_random_reply_chance, 0.1)
            self.assertEqual(config.discord_random_reply_cooldown, 30)
            self.assertEqual(config.discord_random_reply_channels, [123, 456])

    def test_get_float_rejects_garbage(self):
        with patch.dict(os.environ, {'DISCORD_RANDOM_REPLY_CHANCE': 'lots'}):
            config = Config()
            self.assertAlmostEqual(config.discord_random_reply_chance, 0.02)


if __name__ == '__main__':
    unittest.main()
