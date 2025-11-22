#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0
"""
Test Google Genai SDK integration to prevent crashes.
"""

import unittest
import os
from unittest.mock import Mock, patch, MagicMock
from yo_mama.yo_mama_generator import YoMamaGenerator


class TestGenaiIntegration(unittest.TestCase):
    """Test that google-genai SDK is used correctly."""
    
    def test_client_initialization(self):
        """Test that Client object is created correctly."""
        with patch('yo_mama.yo_mama_generator.genai.Client') as mock_client:
            generator = YoMamaGenerator(
                api_key="test_key_12345",
                model_name="gemini-2.5-flash-lite"
            )
            
            # Verify Client was called with api_key
            mock_client.assert_called_once_with(api_key="test_key_12345")
            
            # Verify generator has client attribute
            self.assertTrue(hasattr(generator, 'client'))
    
    def test_generate_content_call_structure(self):
        """Test that generate_content is called with correct parameters."""
        # Create mock client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "Yo mama so slow, she's still loading Python 2.7!"
        mock_client.models.generate_content.return_value = mock_response
        
        with patch('yo_mama.yo_mama_generator.genai.Client', return_value=mock_client):
            generator = YoMamaGenerator(
                api_key="test_key_12345",
                model_name="gemini-2.5-flash-lite"
            )
            
            # Generate a joke
            joke = generator.generate_joke(flavor='tech', meanness=5, nerdiness=5)
            
            # Verify generate_content was called
            mock_client.models.generate_content.assert_called_once()
            
            # Verify it was called with model and contents parameters
            call_kwargs = mock_client.models.generate_content.call_args.kwargs
            self.assertIn('model', call_kwargs)
            self.assertIn('contents', call_kwargs)
            self.assertEqual(call_kwargs['model'], 'gemini-2.5-flash-lite')
            
            # Verify joke was returned
            self.assertEqual(joke, "Yo mama so slow, she's still loading Python 2.7!")
    
    def test_no_configure_method_used(self):
        """Test that deprecated configure() method is NOT used."""
        with patch('yo_mama.yo_mama_generator.genai') as mock_genai:
            mock_client = Mock()
            mock_genai.Client.return_value = mock_client
            
            generator = YoMamaGenerator(
                api_key="test_key_12345",
                model_name="gemini-2.5-flash-lite"
            )
            
            # Verify configure was NOT called
            self.assertFalse(mock_genai.configure.called if hasattr(mock_genai, 'configure') else True)
    
    def test_api_error_handling(self):
        """Test that API errors are handled gracefully."""
        mock_client = Mock()
        mock_client.models.generate_content.side_effect = Exception("API Error: Rate limit exceeded (429)")
        
        with patch('yo_mama.yo_mama_generator.genai.Client', return_value=mock_client):
            generator = YoMamaGenerator(
                api_key="test_key_12345",
                model_name="gemini-2.5-flash-lite"
            )
            
            # Should return rate limit joke instead of crashing
            joke = generator.generate_joke(flavor='tech', meanness=5, nerdiness=5)
            
            # Should get a rate-limit/quota fallback joke
            self.assertIsNotNone(joke)
            self.assertGreater(len(joke), 0)
            # Check for rate limit OR quota keywords
            joke_lower = joke.lower()
            self.assertTrue("rate limit" in joke_lower or "quota" in joke_lower,
                          f"Expected rate limit/quota message, got: {joke}")
    
    @unittest.skipIf(not os.getenv('GEMINI_API_KEY'), "Requires GEMINI_API_KEY")
    def test_real_api_call(self):
        """Test actual API call with real credentials (integration test)."""
        from yo_mama.config import get_config
        
        config = get_config()
        if not config.gemini_api_key:
            self.skipTest("No API key available")
        
        generator = YoMamaGenerator(
            api_key=config.gemini_api_key,
            model_name=config.gemini_model
        )
        
        # Generate actual joke
        joke = generator.generate_joke(flavor='tech', meanness=5, nerdiness=5)
        
        # Verify joke was generated
        self.assertIsNotNone(joke)
        self.assertIsInstance(joke, str)
        self.assertGreater(len(joke), 10)
        print(f"\n   🎤 Generated joke: {joke}")


if __name__ == '__main__':
    unittest.main()
