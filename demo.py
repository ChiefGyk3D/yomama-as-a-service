#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0
"""
Demo script showing various ways to use the Yo Mama Bot.
This demonstrates the API usage for developers.
"""

import sys
from yo_mama.config import get_config
from yo_mama.yo_mama_generator import YoMamaGenerator


def demo_basic():
    """Demo 1: Basic joke generation."""
    print("\n" + "="*70)
    print("DEMO 1: Basic Joke Generation")
    print("="*70)
    
    config = get_config()
    generator = YoMamaGenerator(
        api_key=config.gemini_api_key,
        model_name=config.gemini_model
    )
    
    # Generate a simple joke
    joke = generator.generate_joke(
        flavor='tech',
        meanness=5,
        nerdiness=5
    )
    
    print(f"\n🎤 {joke}\n")


def demo_flavors():
    """Demo 2: Different flavors."""
    print("\n" + "="*70)
    print("DEMO 2: Different Flavors")
    print("="*70)
    
    config = get_config()
    generator = YoMamaGenerator(
        api_key=config.gemini_api_key,
        model_name=config.gemini_model
    )
    
    flavors = ['cybersecurity', 'linux', 'gaming', 'cloud']
    
    for flavor in flavors:
        print(f"\n🎨 {flavor.upper()}:")
        joke = generator.generate_joke(
            flavor=flavor,
            meanness=6,
            nerdiness=7
        )
        print(f"   {joke}")


def demo_intensity_levels():
    """Demo 3: Different intensity levels."""
    print("\n" + "="*70)
    print("DEMO 3: Intensity Levels (Same Flavor, Different Settings)")
    print("="*70)
    
    config = get_config()
    generator = YoMamaGenerator(
        api_key=config.gemini_api_key,
        model_name=config.gemini_model
    )
    
    print("\n🔹 Gentle & Accessible (M:2, N:3)")
    joke1 = generator.generate_joke(flavor='tech', meanness=2, nerdiness=3)
    print(f"   {joke1}")
    
    print("\n🔹 Moderate & Technical (M:5, N:7)")
    joke2 = generator.generate_joke(flavor='tech', meanness=5, nerdiness=7)
    print(f"   {joke2}")
    
    print("\n🔹 Brutal & Expert-Level (M:9, N:10)")
    joke3 = generator.generate_joke(flavor='tech', meanness=9, nerdiness=10)
    print(f"   {joke3}")


def demo_batch():
    """Demo 4: Batch generation."""
    print("\n" + "="*70)
    print("DEMO 4: Batch Generation")
    print("="*70)
    
    config = get_config()
    generator = YoMamaGenerator(
        api_key=config.gemini_api_key,
        model_name=config.gemini_model
    )
    
    print("\n📦 Generating 3 cybersecurity jokes...\n")
    jokes = generator.generate_batch(
        count=3,
        flavor='cybersecurity',
        meanness=7,
        nerdiness=8
    )
    
    for i, joke in enumerate(jokes, 1):
        print(f"{i}. {joke}")


def demo_custom_target():
    """Demo 5: Custom target name."""
    print("\n" + "="*70)
    print("DEMO 5: Custom Target Name")
    print("="*70)
    
    config = get_config()
    generator = YoMamaGenerator(
        api_key=config.gemini_api_key,
        model_name=config.gemini_model
    )
    
    targets = [
        ('your code', 'programming'),
        ('your server', 'devops'),
        ('your database', 'database')
    ]
    
    for target, flavor in targets:
        print(f"\n🎯 Target: {target} ({flavor})")
        joke = generator.generate_joke(
            flavor=flavor,
            meanness=6,
            nerdiness=7,
            target_name=target
        )
        print(f"   {joke}")


def demo_random():
    """Demo 6: Random jokes."""
    print("\n" + "="*70)
    print("DEMO 6: Random Jokes (Random Flavor & Intensity)")
    print("="*70)
    
    config = get_config()
    generator = YoMamaGenerator(
        api_key=config.gemini_api_key,
        model_name=config.gemini_model
    )
    
    print("\n🎲 Generating 3 completely random jokes...\n")
    
    for i in range(3):
        joke = generator.random_joke()
        print(f"{i+1}. {joke}")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("🎤 YO MAMA BOT - API DEMO")
    print("="*70)
    print("\nThis script demonstrates various ways to use the Yo Mama Bot API.")
    print("Each demo will generate jokes using Google Gemini AI.")
    print("\nNote: This will make multiple API calls. Press Ctrl+C to cancel.\n")
    
    try:
        input("Press Enter to start demos (or Ctrl+C to cancel)...")
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled.\n")
        return 0
    
    # Check configuration
    config = get_config()
    is_valid, missing = config.validate()
    
    if not is_valid:
        print("\n❌ Error: Missing configuration:")
        for key in missing:
            print(f"   - {key}")
        print("\nPlease set these in your .env file or Doppler.\n")
        return 1
    
    try:
        # Run demos
        demo_basic()
        input("\nPress Enter for next demo...")
        
        demo_flavors()
        input("\nPress Enter for next demo...")
        
        demo_intensity_levels()
        input("\nPress Enter for next demo...")
        
        demo_batch()
        input("\nPress Enter for next demo...")
        
        demo_custom_target()
        input("\nPress Enter for next demo...")
        
        demo_random()
        
        # Summary
        print("\n" + "="*70)
        print("✅ Demo Complete!")
        print("="*70)
        print("\nFor more usage examples, see:")
        print("  - README.md (full documentation)")
        print("  - QUICKSTART.md (quick reference)")
        print("  - python main.py --help (CLI options)")
        print("\n")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted.\n")
        return 0
    except Exception as e:
        print(f"\n❌ Error during demo: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
