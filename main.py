#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0
"""
Yo Mama Bot - Main CLI Interface

Generate hilarious Yo Mama jokes with customizable flavors, meanness, and nerdiness.
Can also run as Discord or Matrix bot.
"""

import sys
import logging
import argparse
from typing import Optional
from yo_mama.config import get_config
from yo_mama.yo_mama_generator import YoMamaGenerator


def setup_logging(level: str = 'INFO'):
    """Configure logging for the application."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def print_joke(joke: str, prefix: str = "🔥"):
    """Print a joke with nice formatting."""
    print(f"\n{prefix} {joke}\n")


def print_batch(jokes: list[str]):
    """Print multiple jokes with formatting."""
    print("\n" + "="*70)
    for i, joke in enumerate(jokes, 1):
        print(f"\n{i}. {joke}")
    print("\n" + "="*70 + "\n")


def interactive_mode(generator: YoMamaGenerator, config):
    """Run the bot in interactive mode."""
    print("\n" + "="*70)
    print("🎤 YO MAMA BOT - Interactive Mode 🎤".center(70))
    print("="*70)
    print("\nCommands:")
    print("  [Enter] - Generate joke with current settings")
    print("  f [flavor] - Change flavor")
    print("  m [1-10] - Change meanness level")
    print("  n [1-10] - Change nerdiness level")
    print("  t [name] - Change target name")
    print("  b [count] - Generate batch of jokes")
    print("  r - Generate random joke")
    print("  flavors - List available flavors")
    print("  settings - Show current settings")
    print("  quit - Exit\n")
    
    # Current settings
    current_flavor = config.default_flavor
    current_meanness = config.default_meanness
    current_nerdiness = config.default_nerdiness
    current_target = None
    
    def show_settings():
        print(f"\n⚙️  Current Settings:")
        print(f"   Flavor: {current_flavor}")
        print(f"   Meanness: {current_meanness}/10")
        print(f"   Nerdiness: {current_nerdiness}/10")
        print(f"   Target: {current_target or 'yo mama'}\n")
    
    show_settings()
    
    while True:
        try:
            user_input = input("yo-mama-bot> ").strip()
            
            if not user_input:
                # Generate joke with current settings
                joke = generator.generate_joke(
                    flavor=current_flavor,
                    meanness=current_meanness,
                    nerdiness=current_nerdiness,
                    target_name=current_target
                )
                print_joke(joke)
            
            elif user_input.lower() == 'quit':
                print("\n👋 Peace out! Keep roasting!\n")
                break
            
            elif user_input.lower() == 'flavors':
                print("\n📋 Available flavors:")
                for flavor in YoMamaGenerator.list_flavors():
                    print(f"   - {flavor}")
                print()
            
            elif user_input.lower() == 'settings':
                show_settings()
            
            elif user_input.lower() == 'r':
                # Random joke
                joke = generator.random_joke()
                print_joke(joke, "🎲")
            
            elif user_input.startswith('f '):
                # Change flavor
                new_flavor = user_input[2:].strip()
                if new_flavor.lower() in YoMamaGenerator.list_flavors():
                    current_flavor = new_flavor.lower()
                    print(f"✓ Flavor set to: {current_flavor}")
                else:
                    print(f"❌ Unknown flavor. Use 'flavors' to see options.")
            
            elif user_input.startswith('m '):
                # Change meanness
                try:
                    new_meanness = int(user_input[2:].strip())
                    if 1 <= new_meanness <= 10:
                        current_meanness = new_meanness
                        print(f"✓ Meanness set to: {current_meanness}/10")
                    else:
                        print("❌ Meanness must be between 1 and 10")
                except ValueError:
                    print("❌ Invalid number")
            
            elif user_input.startswith('n '):
                # Change nerdiness
                try:
                    new_nerdiness = int(user_input[2:].strip())
                    if 1 <= new_nerdiness <= 10:
                        current_nerdiness = new_nerdiness
                        print(f"✓ Nerdiness set to: {current_nerdiness}/10")
                    else:
                        print("❌ Nerdiness must be between 1 and 10")
                except ValueError:
                    print("❌ Invalid number")
            
            elif user_input.startswith('t '):
                # Change target
                new_target = user_input[2:].strip()
                if new_target.lower() == 'none' or new_target.lower() == 'reset':
                    current_target = None
                    print("✓ Target reset to 'yo mama'")
                else:
                    current_target = new_target
                    print(f"✓ Target set to: {current_target}")
            
            elif user_input.startswith('b '):
                # Generate batch
                try:
                    count = int(user_input[2:].strip())
                    if 1 <= count <= 20:
                        print(f"\n⏳ Generating {count} jokes...")
                        jokes = generator.generate_batch(
                            count=count,
                            flavor=current_flavor,
                            meanness=current_meanness,
                            nerdiness=current_nerdiness,
                            target_name=current_target
                        )
                        print_batch(jokes)
                    else:
                        print("❌ Count must be between 1 and 20")
                except ValueError:
                    print("❌ Invalid number")
            
            else:
                print("❌ Unknown command. Type 'quit' to exit or press Enter to generate a joke.")
        
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Peace out!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


def main():
    """Main entry point for the Yo Mama Bot."""
    parser = argparse.ArgumentParser(
        description='Generate Yo Mama jokes with AI or run as Discord/Matrix bot',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Interactive mode
  %(prog)s -f cybersecurity -m 8 -n 9        # Generate harsh, nerdy cybersec joke
  %(prog)s -f linux -m 3 -n 7                # Generate gentle, technical Linux joke
  %(prog)s -b 5 -f gaming                    # Generate 5 gaming jokes
  %(prog)s -r                                # Generate random joke
  %(prog)s --flavors                         # List available flavors
  %(prog)s --discord                         # Run as Discord bot
  %(prog)s --matrix                          # Run as Matrix bot
        """
    )
    
    parser.add_argument(
        '-f', '--flavor',
        help='Joke flavor/theme (cybersecurity, tech, linux, etc.)',
        type=str
    )
    
    parser.add_argument(
        '-m', '--meanness',
        help='Meanness level 1-10 (1=gentle, 10=brutal)',
        type=int,
        choices=range(1, 11),
        metavar='1-10'
    )
    
    parser.add_argument(
        '-n', '--nerdiness',
        help='Nerdiness level 1-10 (1=accessible, 10=very technical)',
        type=int,
        choices=range(1, 11),
        metavar='1-10'
    )
    
    parser.add_argument(
        '-t', '--target',
        help='Custom target name (default: "yo mama")',
        type=str
    )
    
    parser.add_argument(
        '-b', '--batch',
        help='Generate multiple jokes',
        type=int,
        metavar='COUNT'
    )
    
    parser.add_argument(
        '-r', '--random',
        help='Generate completely random joke',
        action='store_true'
    )
    
    parser.add_argument(
        '--flavors',
        help='List available flavors and exit',
        action='store_true'
    )
    
    parser.add_argument(
        '-i', '--interactive',
        help='Run in interactive mode (default if no other args)',
        action='store_true'
    )
    
    parser.add_argument(
        '--log-level',
        help='Set logging level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default=None
    )
    
    parser.add_argument(
        '--discord',
        help='Run as Discord bot',
        action='store_true'
    )
    
    parser.add_argument(
        '--matrix',
        help='Run as Matrix bot',
        action='store_true'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = get_config()
    
    # Setup logging
    log_level = args.log_level or config.log_level
    setup_logging(log_level)
    
    # Handle --flavors flag
    if args.flavors:
        print("\n📋 Available joke flavors:")
        for flavor in YoMamaGenerator.list_flavors():
            print(f"   - {flavor}")
        print()
        return 0
    
    # Run as bot if requested
    if args.discord and args.matrix:
        # Run both bots concurrently
        import threading
        from yo_mama.platforms import run_discord_bot, run_matrix_bot
        
        print("\n🤖 Starting Discord and Matrix bots...\n")
        
        # Start Discord in a thread
        discord_thread = threading.Thread(target=run_discord_bot, daemon=False)
        discord_thread.start()
        
        # Start Matrix in main thread (blocks)
        run_matrix_bot()
        return 0
    
    elif args.discord:
        from yo_mama.platforms import run_discord_bot
        print("\n🤖 Starting Discord bot...\n")
        run_discord_bot()
        return 0
    
    elif args.matrix:
        from yo_mama.platforms import run_matrix_bot
        print("\n🤖 Starting Matrix bot...\n")
        run_matrix_bot()
        return 0
    
    # Validate configuration for CLI mode
    is_valid, missing = config.validate()
    if not is_valid:
        print("\n❌ Error: Missing required configuration:")
        for key in missing:
            print(f"   - {key}")
        print("\nPlease set these in your .env file or Doppler.")
        print("See .env.example for reference.\n")
        return 1
    
    # Initialize generator
    try:
        generator = YoMamaGenerator(
            api_key=config.gemini_api_key,
            model_name=config.gemini_model
        )
    except Exception as e:
        print(f"\n❌ Failed to initialize generator: {e}\n")
        return 1
    
    # Determine mode
    if args.random:
        # Random mode
        joke = generator.random_joke()
        print_joke(joke, "🎲")
    
    elif args.batch:
        # Batch mode
        print(f"\n⏳ Generating {args.batch} jokes...\n")
        jokes = generator.generate_batch(
            count=args.batch,
            flavor=args.flavor or config.default_flavor,
            meanness=args.meanness or config.default_meanness,
            nerdiness=args.nerdiness or config.default_nerdiness,
            target_name=args.target
        )
        print_batch(jokes)
    
    elif args.flavor or args.meanness or args.nerdiness or args.target:
        # Single joke mode with specific parameters
        joke = generator.generate_joke(
            flavor=args.flavor or config.default_flavor,
            meanness=args.meanness or config.default_meanness,
            nerdiness=args.nerdiness or config.default_nerdiness,
            target_name=args.target
        )
        print_joke(joke)
    
    else:
        # Interactive mode (default)
        interactive_mode(generator, config)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
