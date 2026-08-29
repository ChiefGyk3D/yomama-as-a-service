#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0
"""
Test the hypeman LLM integration (Ollama/Gemini via LLMManager).
"""

import os
import unittest
from unittest.mock import Mock, patch

from yo_mama.yo_mama_generator import YoMamaGenerator


def _mock_manager(generate_result=None, last_error=None):
    """Build a Mock LLMManager wired the way YoMamaGenerator uses it."""
    manager = Mock()
    manager.authenticate.return_value = True
    manager.generate.return_value = generate_result
    manager.provider = 'mock'
    manager.active = Mock(model='mock-model')
    manager.status.return_value = {
        'primary': {'provider': 'mock', 'last_error': last_error},
        'fallbacks': [],
    }
    return manager


class TestLLMIntegration(unittest.TestCase):
    """Test that the LLMManager layer is used correctly."""

    def test_manager_initialization(self):
        """The generator builds and authenticates an LLMManager."""
        manager = _mock_manager()
        with patch('yo_mama.yo_mama_generator.LLMManager', return_value=manager):
            generator = YoMamaGenerator()

            manager.authenticate.assert_called_once()
            self.assertIs(generator.llm, manager)

    def test_legacy_gemini_kwargs_land_in_env(self):
        """The old api_key/model_name arguments still configure Gemini."""
        manager = _mock_manager()
        env = {k: v for k, v in os.environ.items()
               if k not in ('GEMINI_API_KEY', 'LLM_GEMINI_MODEL')}
        with patch.dict(os.environ, env, clear=True), \
                patch('yo_mama.yo_mama_generator.LLMManager', return_value=manager):
            YoMamaGenerator(api_key='test_key_12345', model_name='gemini-2.5-flash-lite')

            self.assertEqual(os.environ.get('GEMINI_API_KEY'), 'test_key_12345')
            self.assertEqual(os.environ.get('LLM_GEMINI_MODEL'), 'gemini-2.5-flash-lite')

    def test_generate_joke_uses_manager(self):
        """generate_joke sends a prompt through the manager and returns the joke."""
        joke_text = "Yo mama so slow, she's still loading Python 2.7!"
        manager = _mock_manager(generate_result=joke_text)

        with patch('yo_mama.yo_mama_generator.LLMManager', return_value=manager):
            generator = YoMamaGenerator()
            joke = generator.generate_joke(flavor='tech', meanness=5, nerdiness=5)

            manager.generate.assert_called_once()
            prompt = manager.generate.call_args.args[0]
            self.assertIn('tech', prompt)
            self.assertIn('MEANNESS LEVEL: 5', prompt)
            self.assertEqual(joke, joke_text)

    def test_fallback_joke_when_all_providers_fail(self):
        """A None from the manager degrades to a canned joke, not a crash."""
        manager = _mock_manager(generate_result=None, last_error='ConnectionError: refused')

        with patch('yo_mama.yo_mama_generator.LLMManager', return_value=manager):
            generator = YoMamaGenerator()
            joke = generator.generate_joke(flavor='tech', meanness=5, nerdiness=5)

            self.assertEqual(joke, generator._get_fallback_joke('tech'))

    def test_rate_limit_gets_snarky_joke(self):
        """A 429/quota failure returns the rate-limit jokes, not the generic one."""
        manager = _mock_manager(
            generate_result=None,
            last_error='ClientError: 429 Rate limit exceeded',
        )

        with patch('yo_mama.yo_mama_generator.LLMManager', return_value=manager):
            generator = YoMamaGenerator()
            joke = generator.generate_joke(flavor='tech', meanness=5, nerdiness=5)

            self.assertIsNotNone(joke)
            joke_lower = joke.lower()
            self.assertTrue('rate limit' in joke_lower or 'quota' in joke_lower,
                            f"Expected rate limit/quota message, got: {joke}")

    @unittest.skipIf(not os.getenv('GEMINI_API_KEY') and not os.getenv('LLM_OLLAMA_HOST'),
                     "Requires GEMINI_API_KEY or LLM_OLLAMA_HOST")
    def test_real_generation(self):
        """Generate a joke against whichever real provider is configured."""
        generator = YoMamaGenerator()

        joke = generator.generate_joke(flavor='tech', meanness=5, nerdiness=5)

        self.assertIsNotNone(joke)
        self.assertIsInstance(joke, str)
        self.assertGreater(len(joke), 10)
        print(f"\n   🎤 [{generator.llm.provider}] {joke}")


if __name__ == '__main__':
    unittest.main()
