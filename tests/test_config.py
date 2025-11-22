#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0
"""
Test configuration loading and validation.
"""

import unittest
import os
from yo_mama.config import get_config


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


if __name__ == '__main__':
    unittest.main()
