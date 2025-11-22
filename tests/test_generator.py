#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0
"""
Test joke generator functionality.
"""

import unittest
from yo_mama.yo_mama_generator import YoMamaGenerator


class TestGenerator(unittest.TestCase):
    """Test YoMamaGenerator functionality."""
    
    def test_list_flavors(self):
        """Test that flavors can be listed."""
        flavors = YoMamaGenerator.list_flavors()
        self.assertIsInstance(flavors, list)
        self.assertGreater(len(flavors), 0)
        self.assertIn('classic', flavors)
        self.assertIn('cybersecurity', flavors)
        self.assertIn('tech', flavors)
    
    def test_flavor_count(self):
        """Test that we have the expected number of flavors."""
        flavors = YoMamaGenerator.list_flavors()
        # We should have at least 10 flavors
        self.assertGreaterEqual(len(flavors), 10)


if __name__ == '__main__':
    unittest.main()
