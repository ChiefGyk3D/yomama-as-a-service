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
    try:
        import google.generativeai as genai
        print("   ✓ google-generativeai")
    except ImportError as e:
        print(f"   ❌ google-generativeai: {e}")
        return False
    
    try:
        from dopplersdk import DopplerSDK
        print("   ✓ dopplersdk")
    except ImportError as e:
        print(f"   ❌ dopplersdk: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print("   ✓ python-dotenv")
    except ImportError as e:
        print(f"   ❌ python-dotenv: {e}")
        return False
    
    try:
        import discord
        print("   ✓ discord.py")
    except ImportError as e:
        print(f"   ❌ discord.py: {e}")
        return False
    
    try:
        import nio
        print("   ✓ matrix-nio")
    except ImportError as e:
        print(f"   ❌ matrix-nio: {e}")
        return False
    
    try:
        from yo_mama.config import get_config
        print("   ✓ config module")
    except ImportError as e:
        print(f"   ❌ config module: {e}")
        return False
    
    try:
        from yo_mama.yo_mama_generator import YoMamaGenerator
        print("   ✓ yo_mama_generator module")
    except ImportError as e:
        print(f"   ❌ yo_mama_generator module: {e}")
        return False
    
    try:
        from yo_mama.platforms import DiscordBot, MatrixBot
        print("   ✓ platform modules")
    except ImportError as e:
        print(f"   ❌ platform modules: {e}")
        return False
    
    return True


def test_config():
    """Test configuration loading."""
    print("\n🔍 Testing configuration...")
    
    try:
        from yo_mama.config import get_config
        config = get_config()
        print("   ✓ Configuration loaded")
        
        # Check for API key
        if config.gemini_api_key:
            # Mask the key for security
            masked = config.gemini_api_key[:8] + "..." + config.gemini_api_key[-4:]
            print(f"   ✓ GEMINI_API_KEY found: {masked}")
        else:
            print("   ⚠️  GEMINI_API_KEY not set")
            print("      Edit .env and add your API key")
            return False
        
        # Validate config
        is_valid, missing = config.validate()
        if is_valid:
            print("   ✓ All required configuration present")
        else:
            print(f"   ❌ Missing configuration: {', '.join(missing)}")
            return False
        
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
        
        return True
        
    except Exception as e:
        print(f"   ❌ Configuration error: {e}")
        return False


def test_generator():
    """Test joke generator initialization."""
    print("\n🔍 Testing joke generator...")
    
    try:
        from yo_mama.config import get_config
        from yo_mama.yo_mama_generator import YoMamaGenerator
        
        config = get_config()
        
        if not config.gemini_api_key:
            print("   ⚠️  Skipping generator test (no API key)")
            return True
        
        generator = YoMamaGenerator(
            api_key=config.gemini_api_key,
            model_name=config.gemini_model
        )
        print("   ✓ Generator initialized")
        
        # List flavors
        flavors = YoMamaGenerator.list_flavors()
        print(f"   ✓ {len(flavors)} flavors available: {', '.join(flavors[:5])}...")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Generator error: {e}")
        return False


def test_joke_generation():
    """Test actual joke generation (optional)."""
    print("\n🔍 Testing joke generation (this may take a moment)...")
    
    try:
        from yo_mama.config import get_config
        from yo_mama.yo_mama_generator import YoMamaGenerator
        
        config = get_config()
        
        if not config.gemini_api_key:
            print("   ⚠️  Skipping generation test (no API key)")
            return True
        
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
        
        if joke and len(joke) > 10:
            print("   ✓ Joke generation successful!")
            print(f"\n   🎤 Test joke: {joke}\n")
            return True
        else:
            print("   ❌ Generated joke is invalid or empty")
            return False
        
    except Exception as e:
        print(f"   ❌ Generation error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*70)
    print("🎤 Yo Mama Bot - Configuration Test")
    print("="*70)
    print()
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        print("\n❌ Import test failed")
        print("   Run: pip install -r requirements.txt")
        all_passed = False
    
    # Test config
    if not test_config():
        print("\n❌ Configuration test failed")
        print("   Edit .env and add your GEMINI_API_KEY")
        all_passed = False
    
    # Test generator
    if not test_generator():
        print("\n❌ Generator test failed")
        all_passed = False
    
    # Test joke generation (optional, requires API key)
    if os.getenv('GEMINI_API_KEY') or (os.path.isfile('.env') and 'GEMINI_API_KEY' in open('.env').read()):
        response = input("\n🤔 Test joke generation? (y/n, default=n): ").strip().lower()
        if response == 'y':
            if not test_joke_generation():
                print("\n⚠️  Generation test failed (but other tests may have passed)")
    
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
