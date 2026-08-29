#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0
"""
LLM integration tests for the joke generator.

The provider plumbing (Gemini client construction, retries, rate limiting,
reconnection, Ollama support) lives in hypeman-social and is covered by that
library's own test suite. These tests cover the bot's layer: prompt flow
through the engine, rate-limit meta-jokes, and fallback jokes.
"""

import os
import unittest
from unittest.mock import Mock

from yo_mama.yo_mama_generator import YoMamaGenerator


def _make_generator(response="Yo mama so slow, she's still loading Python 2.7!"):
    """Generator with a mocked hypeman engine (no network, no API key)."""
    generator = YoMamaGenerator.__new__(YoMamaGenerator)
    generator.api_key = 'test_key_12345'
    generator.model_name = 'gemini-2.5-flash-lite'
    generator.engine = Mock()
    generator.engine.generate.return_value = response
    generator.engine.status.return_value = {'primary': {'last_error': None}, 'fallbacks': []}
    return generator


class TestLLMIntegration(unittest.TestCase):
    """The bot's use of the shared hypeman-social LLM engine."""

    def test_joke_flows_through_engine(self):
        generator = _make_generator()
        joke = generator.generate_joke(flavor='tech', meanness=5, nerdiness=5)

        generator.engine.generate.assert_called_once()
        prompt = generator.engine.generate.call_args[0][0]
        self.assertIn('tech', prompt)
        self.assertEqual(joke, "Yo mama so slow, she's still loading Python 2.7!")

    def test_meanness_eleven_goes_to_eleven(self):
        generator = _make_generator()
        generator.generate_joke(flavor='tech', meanness=11, nerdiness=5)
        prompt = generator.engine.generate.call_args[0][0]
        self.assertIn('ELEVEN', prompt)

    def test_custom_target_name_in_prompt(self):
        generator = _make_generator()
        generator.generate_joke(flavor='tech', target_name='yo router')
        prompt = generator.engine.generate.call_args[0][0]
        self.assertIn('yo router', prompt)

    def test_rate_limit_returns_meta_joke(self):
        generator = _make_generator(response=None)
        generator.engine.status.return_value = {
            'primary': {'last_error': 'ClientError: 429 RESOURCE_EXHAUSTED'},
            'fallbacks': [],
        }

        joke = generator.generate_joke(flavor='tech', meanness=5, nerdiness=5)

        self.assertIsNotNone(joke)
        joke_lower = joke.lower()
        self.assertTrue('rate limit' in joke_lower or 'quota' in joke_lower,
                        f"Expected rate limit/quota message, got: {joke}")

    def test_engine_failure_returns_fallback_joke(self):
        generator = _make_generator(response=None)
        joke = generator.generate_joke(flavor='tech', meanness=5, nerdiness=5)
        self.assertIsNotNone(joke)
        self.assertGreater(len(joke), 0)
        self.assertIn('mama', joke.lower())

    def test_unknown_flavor_falls_back_to_random(self):
        generator = _make_generator()
        joke = generator.generate_joke(flavor='nonexistent-flavor')
        self.assertIsNotNone(joke)
        generator.engine.generate.assert_called_once()

    @unittest.skipIf(not os.getenv('GEMINI_API_KEY'), "Requires GEMINI_API_KEY")
    def test_real_api_call(self):
        """Actual API call with real credentials (integration test)."""
        from yo_mama.config import get_config

        config = get_config()
        if not config.gemini_api_key:
            self.skipTest("No API key available")

        generator = YoMamaGenerator(
            api_key=config.gemini_api_key,
            model_name=config.gemini_model
        )
        joke = generator.generate_joke(flavor='tech', meanness=5, nerdiness=5)
        self.assertIsNotNone(joke)
        self.assertGreater(len(joke), 10)


if __name__ == '__main__':
    unittest.main()
