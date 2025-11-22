#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0
"""
Test script to verify Yo Mama Bot configuration and basic functionality.
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")
    
    from google import genai
    print("   ✓ google-genai")
    
    from dopplersdk import DopplerSDK
    print("   ✓ dopplersdk")
    
    from dotenv import load_dotenv
    print("   ✓ python-dotenv")
    
    import discord
    print("   ✓ discord.py")
    
    import nio
    print("   ✓ matrix-nio")
    
    from yo_mama.config import get_config
    print("   ✓ config module")
    
    from yo_mama.yo_mama_generator import YoMamaGenerator
    print("   ✓ yo_mama_generator module")
    
    from yo_mama.platforms import DiscordBot, MatrixBot
    print("   ✓ platform modules")
    
    assert True  # All imports successful


def test_config():
    """Test configuration loading."""
    print("\n🔍 Testing configuration...")
    
    from yo_mama.config import get_config
    config = get_config()
    print("   ✓ Configuration loaded")
    
    # Check for API key (without displaying any part of it)
    if config.gemini_api_key:
        print(f"   ✓ GEMINI_API_KEY found (length: {len(config.gemini_api_key)} chars)")
    else:
        print("   ⚠️  GEMINI_API_KEY not set")
        print("      Edit .env and add your API key")
    
    # Validate config
    is_valid, missing = config.validate()
    if is_valid:
        print("   ✓ All required configuration present")
    else:
        print(f"   ⚠️  Missing configuration: {', '.join(missing)}")
    
    # Show current settings
    print(f"\n   Current settings:")
    print(f"      Model: {config.gemini_model}")
    print(f"      Default Flavor: {config.default_flavor}")
    print(f"      Default Meanness: {config.default_meanness}/10")
    print(f"      Default Nerdiness: {config.default_nerdiness}/10")
    
    # Check Doppler
    if os.getenv('DOPPLER_TOKEN'):
        print("   ✓ Doppler integration enabled")
    else:
        print("   ℹ️  Doppler not configured (using .env only)")
    
    assert config is not None


def test_generator():
    """Test joke generator initialization."""
    print("\n🔍 Testing joke generator...")
    
    from yo_mama.config import get_config
    from yo_mama.yo_mama_generator import YoMamaGenerator
    
    config = get_config()
    
    if not config.gemini_api_key:
        print("   ⚠️  Skipping generator initialization (no API key)")
    else:
        generator = YoMamaGenerator(
            api_key=config.gemini_api_key,
            model_name=config.gemini_model
        )
        print("   ✓ Generator initialized")
        assert generator is not None
    
    # List flavors (doesn't require API key)
    flavors = YoMamaGenerator.list_flavors()
    print(f"   ✓ {len(flavors)} flavors available: {', '.join(flavors[:5])}...")
    assert len(flavors) > 0


def test_joke_generation():
    """Test actual joke generation (optional)."""
    print("\n🔍 Testing joke generation (this may take a moment)...")
    
    from yo_mama.config import get_config
    from yo_mama.yo_mama_generator import YoMamaGenerator
    
    config = get_config()
    
    if not config.gemini_api_key:
        print("   ⚠️  Skipping generation test (no API key)")
        assert True  # Skip test if no API key
        return
    
    generator = YoMamaGenerator(
        api_key=config.gemini_api_key,
        model_name=config.gemini_model
    )
    
    # Generate a test joke
    joke = generator.generate_joke(
        flavor='tech',
        meanness=5,
        nerdiness=5
    )
    
    print("   ✓ Joke generation successful!")
    print(f"\n   🎤 Test joke: {joke}\n")
    
    assert joke is not None
    assert len(joke) > 10
    assert isinstance(joke, str)


def main():
    """Run all tests interactively."""
    print("="*70)
    print("🎤 Yo Mama Bot - Configuration Test")
    print("="*70)
    print()
    
    all_passed = True
    
    # Test imports
    try:
        test_imports()
    except Exception as e:
        print(f"\n❌ Import test failed: {e}")
        print("   Run: pip install -r requirements.txt")
        all_passed = False
    
    # Test config
    try:
        test_config()
    except Exception as e:
        print(f"\n❌ Configuration test failed: {e}")
        print("   Edit .env and add your GEMINI_API_KEY")
        all_passed = False
    
    # Test generator
    try:
        test_generator()
    except Exception as e:
        print(f"\n❌ Generator test failed: {e}")
        all_passed = False
    
    # Test joke generation (optional, requires API key)
    has_api_key = os.getenv('GEMINI_API_KEY')
    if not has_api_key and os.path.isfile('.env'):
        with open('.env', 'r') as f:
            has_api_key = 'GEMINI_API_KEY' in f.read()
    
    if has_api_key:
        response = input("\n🤔 Test joke generation? (y/n, default=n): ").strip().lower()
        if response == 'y':
            try:
                test_joke_generation()
            except Exception as e:
                print(f"\n⚠️  Generation test failed: {e}")
                import traceback
                traceback.print_exc()
    
    # Summary
    print("\n" + "="*70)
    if all_passed:
        print("✅ All tests passed! You're ready to generate jokes!")
        print("\nRun: python main.py")
        print("Or:  ./run.sh")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Copy .env.example to .env: cp .env.example .env")
        print("  3. Edit .env and add your GEMINI_API_KEY")
    print("="*70)
    print()
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
