# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0
"""
Discord bot platform for Yo Mama Bot.

Supports slash commands, text commands, and webhook posting.
"""

import logging
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from ..config import get_config
from ..yo_mama_generator import YoMamaGenerator

logger = logging.getLogger(__name__)


class DiscordBot:
    """
    Discord bot with slash commands for generating Yo Mama jokes.
    
    Commands:
    - /joke [flavor] [meanness] [nerdiness] [target] - Generate a joke
    - /random - Generate a random joke
    - /batch [count] [flavor] [meanness] [nerdiness] - Generate multiple jokes
    - /flavors - List available flavors
    """
    
    def __init__(self, config=None):
        """Initialize the Discord bot."""
        self.config = config or get_config()
        
        # Bot setup with intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        self.bot = commands.Bot(
            command_prefix=self.config.get_config('DISCORD_PREFIX', '!'),
            intents=intents,
            help_command=None
        )
        
        # Initialize joke generator
        self.generator = YoMamaGenerator(
            api_key=self.config.gemini_api_key,
            model_name=self.config.gemini_model
        )
        
        # Setup event handlers and commands
        self._setup_events()
        self._setup_commands()
        
        logger.info("Discord bot initialized")
    
    def _setup_events(self):
        """Setup Discord event handlers."""
        
        @self.bot.event
        async def on_ready():
            """Called when the bot is ready."""
            logger.info(f'Discord bot logged in as {self.bot.user}')
            logger.info(f'Bot is in {len(self.bot.guilds)} guilds')
            
            # Sync slash commands
            try:
                synced = await self.bot.tree.sync()
                logger.info(f'Synced {len(synced)} slash commands')
            except Exception as e:
                logger.error(f'Failed to sync commands: {e}')
        
        @self.bot.event
        async def on_command_error(ctx, error):
            """Handle command errors."""
            if isinstance(error, commands.CommandNotFound):
                return
            elif isinstance(error, commands.MissingRequiredArgument):
                await ctx.send(f'❌ Missing argument: {error.param.name}')
            else:
                logger.error(f'Command error: {error}')
                await ctx.send(f'❌ An error occurred: {str(error)}')
    
    def _setup_commands(self):
        """Setup bot commands."""
        
        # Slash command: /joke
        @self.bot.tree.command(name="joke", description="Generate a Yo Mama joke")
        @app_commands.describe(
            flavor="Joke flavor",
            meanness="How mean (1-11, default: 5) - These go to eleven! 🎸",
            nerdiness="How nerdy (1-10, default: 5)",
            target="Custom target name (default: yo mama)",
            user="Mention a user to roast (optional)"
        )
        @app_commands.choices(flavor=[
            app_commands.Choice(name="🎭 Classic (Traditional Yo Mama)", value="classic"),
            app_commands.Choice(name="🔒 Cybersecurity", value="cybersecurity"),
            app_commands.Choice(name="💻 Tech (General Technology)", value="tech"),
            app_commands.Choice(name="🐧 Linux", value="linux"),
            app_commands.Choice(name="🌐 General", value="general"),
            app_commands.Choice(name="🎮 Gaming", value="gaming"),
            app_commands.Choice(name="👨‍💻 Programming", value="programming"),
            app_commands.Choice(name="📡 Networking", value="networking"),
            app_commands.Choice(name="☁️ Cloud", value="cloud"),
            app_commands.Choice(name="🚀 DevOps", value="devops"),
            app_commands.Choice(name="🗄️ Database", value="database"),
            app_commands.Choice(name="📻 Amateur Radio (Ham Radio)", value="radio"),
            app_commands.Choice(name="❓ Secret...", value="thegame"),  # Easter egg
        ])
        async def joke_slash(
            interaction: discord.Interaction,
            flavor: Optional[str] = None,
            meanness: Optional[int] = None,
            nerdiness: Optional[int] = None,
            target: Optional[str] = None,
            user: Optional[discord.User] = None
        ):
            await interaction.response.defer(thinking=True)
            
            try:
                # Validate inputs
                if meanness is not None and not (1 <= meanness <= 11):
                    await interaction.followup.send("❌ Meanness must be between 1 and 11 (these go to eleven! 🎸)")
                    return
                
                if nerdiness is not None and not (1 <= nerdiness <= 10):
                    await interaction.followup.send("❌ Nerdiness must be between 1 and 10")
                    return
                
                # Handle user mention (prepend to message)
                mention_text = f"{user.mention} " if user else ""
                
                # Special handling for "thegame" Easter egg
                if flavor == "thegame":
                    joke = self.generator.generate_joke(
                        flavor="thegame",
                        meanness=11,  # THESE GO TO ELEVEN! 🎸
                        nerdiness=meanness or 5,  # Use meanness as nerdiness for thegame
                        target_name=user.display_name if user else (target or "you")
                    )
                    embed = discord.Embed(
                        description=f"{mention_text}🎮💀 {joke}",
                        color=discord.Color.purple()
                    )
                    embed.set_footer(text="You just lost The Game. Sorry! 😈")
                else:
                    # Generate normal joke
                    joke = self.generator.generate_joke(
                        flavor=flavor or self.config.default_flavor,
                        meanness=meanness or self.config.default_meanness,
                        nerdiness=nerdiness or self.config.default_nerdiness,
                        target_name=user.display_name if user else target
                    )
                    
                    # Create embed
                    embed = discord.Embed(
                        description=f"{mention_text}🎤 {joke}",
                        color=discord.Color.red()
                    )
                    
                    # Add footer with settings
                    settings = []
                    if flavor:
                        settings.append(f"Flavor: {flavor}")
                    settings.append(f"Meanness: {meanness or self.config.default_meanness}/10")
                    settings.append(f"Nerdiness: {nerdiness or self.config.default_nerdiness}/10")
                    embed.set_footer(text=" | ".join(settings))
                
                await interaction.followup.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Error generating joke: {e}")
                await interaction.followup.send(f"❌ Failed to generate joke: {str(e)}")
        
        # Slash command: /random
        @self.bot.tree.command(name="random", description="Generate a random Yo Mama joke")
        async def random_slash(interaction: discord.Interaction):
            await interaction.response.defer(thinking=True)
            
            try:
                joke = self.generator.random_joke()
                
                embed = discord.Embed(
                    description=f"🎲 {joke}",
                    color=discord.Color.gold()
                )
                embed.set_footer(text="Random joke with random settings")
                
                await interaction.followup.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Error generating random joke: {e}")
                await interaction.followup.send(f"❌ Failed to generate joke: {str(e)}")
        
        # Slash command: /batch
        @self.bot.tree.command(name="batch", description="Generate multiple Yo Mama jokes")
        @app_commands.describe(
            count="Number of jokes (1-10)",
            flavor="Joke flavor",
            meanness="How mean (1-11) - These go to eleven! 🎸",
            nerdiness="How nerdy (1-10)"
        )
        @app_commands.choices(flavor=[
            app_commands.Choice(name="🎭 Classic (Traditional Yo Mama)", value="classic"),
            app_commands.Choice(name="🔒 Cybersecurity", value="cybersecurity"),
            app_commands.Choice(name="💻 Tech (General Technology)", value="tech"),
            app_commands.Choice(name="🐧 Linux", value="linux"),
            app_commands.Choice(name="🌐 General", value="general"),
            app_commands.Choice(name="🎮 Gaming", value="gaming"),
            app_commands.Choice(name="👨‍💻 Programming", value="programming"),
            app_commands.Choice(name="📡 Networking", value="networking"),
            app_commands.Choice(name="☁️ Cloud", value="cloud"),
            app_commands.Choice(name="🚀 DevOps", value="devops"),
            app_commands.Choice(name="🗄️ Database", value="database"),
            app_commands.Choice(name="📻 Amateur Radio (Ham Radio)", value="radio"),
            app_commands.Choice(name="❓ Secret...", value="thegame"),  # Easter egg
        ])
        async def batch_slash(
            interaction: discord.Interaction,
            count: int = 3,
            flavor: Optional[str] = None,
            meanness: Optional[int] = None,
            nerdiness: Optional[int] = None
        ):
            await interaction.response.defer(thinking=True)
            
            try:
                # Validate count
                if not (1 <= count <= 10):
                    await interaction.followup.send("❌ Count must be between 1 and 10")
                    return
                
                # Generate jokes
                jokes = self.generator.generate_batch(
                    count=count,
                    flavor=flavor or self.config.default_flavor,
                    meanness=meanness or self.config.default_meanness,
                    nerdiness=nerdiness or self.config.default_nerdiness
                )
                
                # Create embed
                embed = discord.Embed(
                    title=f"🔥 {count} Yo Mama Jokes",
                    color=discord.Color.red()
                )
                
                for i, joke in enumerate(jokes, 1):
                    embed.add_field(
                        name=f"#{i}",
                        value=joke,
                        inline=False
                    )
                
                # Add footer
                settings = []
                if flavor:
                    settings.append(f"Flavor: {flavor}")
                settings.append(f"M: {meanness or self.config.default_meanness}")
                settings.append(f"N: {nerdiness or self.config.default_nerdiness}")
                embed.set_footer(text=" | ".join(settings))
                
                await interaction.followup.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Error generating batch: {e}")
                await interaction.followup.send(f"❌ Failed to generate jokes: {str(e)}")
        
        # Slash command: /flavors
        @self.bot.tree.command(name="flavors", description="List available joke flavors")
        async def flavors_slash(interaction: discord.Interaction):
            flavors = YoMamaGenerator.list_flavors()
            
            embed = discord.Embed(
                title="📋 Available Joke Flavors",
                description="\n".join([f"• `{flavor}`" for flavor in flavors]),
                color=discord.Color.blue()
            )
            
            await interaction.response.send_message(embed=embed)
        
        # Slash command: /help
        @self.bot.tree.command(name="help", description="Show help for Yo Mama Bot")
        async def help_slash(interaction: discord.Interaction):
            embed = discord.Embed(
                title="🎤 Yo Mama Bot - Help",
                description="AI-powered Yo Mama joke generator with customizable meanness and nerdiness!",
                color=discord.Color.purple()
            )
            
            # Commands section
            embed.add_field(
                name="📝 Slash Commands",
                value=(
                    "`/joke [flavor] [meanness] [nerdiness] [target]`\n"
                    "Generate a custom Yo Mama joke\n\n"
                    "`/random`\n"
                    "Generate a completely random joke\n\n"
                    "`/batch [count] [flavor] [meanness] [nerdiness]`\n"
                    "Generate multiple jokes (1-10)\n\n"
                    "`/flavors`\n"
                    "List all available joke flavors\n\n"
                    "`/help`\n"
                    "Show this help message"
                ),
                inline=False
            )
            
            # Parameters section
            embed.add_field(
                name="⚙️ Parameters",
                value=(
                    "**Meanness (1-10):**\n"
                    "1 = Gentle and playful\n"
                    "10 = Absolutely savage\n\n"
                    "**Nerdiness (1-10):**\n"
                    "1 = Everyone can understand\n"
                    "10 = Extremely technical"
                ),
                inline=False
            )
            
            # Flavors section
            flavors = YoMamaGenerator.list_flavors()
            flavor_list = [
                "🎭 `classic` - Traditional Yo Mama jokes",
                "🔒 `cybersecurity` - Hacking & security",
                "💻 `tech` - General technology",
                "🐧 `linux` - Linux & Unix",
                "🌐 `general` - Everyday tech",
                "🎮 `gaming` - Video games",
                "👨‍💻 `programming` - Coding",
                "📡 `networking` - Networks",
                "☁️ `cloud` - Cloud computing",
                "🚀 `devops` - DevOps & CI/CD",
                "🗄️ `database` - Databases",
                "📻 `radio` - Amateur radio / Ham radio"
            ]
            embed.add_field(
                name="🎯 Available Flavors",
                value="\n".join(flavor_list),
                inline=False
            )
            
            # Examples section
            embed.add_field(
                name="💡 Examples",
                value=(
                    "`/joke classic 7 1` - Classic fat/ugly jokes, pretty mean, easy to understand\n"
                    "`/joke cybersecurity 8 9` - Savage cybersecurity roast\n"
                    "`/joke linux 6 10` - Technical Linux joke\n"
                    "`/random` - Surprise me!\n"
                    "`/batch 3 tech 5 5` - Generate 3 tech jokes"
                ),
                inline=False
            )
            
            embed.set_footer(text=f"Prefix: {self.bot.command_prefix} | Powered by Google Gemini")
            
            await interaction.response.send_message(embed=embed)
        
        # Text command: !joke (for backwards compatibility)
        @self.bot.command(name='joke')
        async def joke_text(ctx, flavor: Optional[str] = None, meanness: int = 5, nerdiness: int = 5):
            """Generate a Yo Mama joke (text command)"""
            async with ctx.typing():
                try:
                    logger.info(f"Text command received: flavor='{flavor}', type={type(flavor)}")
                    # Special handling for "thegame" Easter egg
                    if flavor and flavor.lower() == "thegame":
                        joke = self.generator.generate_joke(
                            flavor="thegame",
                            meanness=10,  # Always maximum savage
                            nerdiness=5,
                            target_name=None
                        )
                        embed = discord.Embed(
                            description=f"🎮💀 {joke}",
                            color=discord.Color.purple()
                        )
                        embed.set_footer(text="You just lost The Game. Sorry! 😈")
                        await ctx.send(embed=embed)
                    else:
                        joke = self.generator.generate_joke(
                            flavor=flavor,
                            meanness=meanness,
                            nerdiness=nerdiness
                        )
                        await ctx.send(f"🎤 {joke}")
                except Exception as e:
                    await ctx.send(f"❌ Error: {str(e)}")
        
        # Text command: !random
        @self.bot.command(name='random')
        async def random_text(ctx):
            """Generate a random joke (text command)"""
            async with ctx.typing():
                try:
                    joke = self.generator.random_joke()
                    await ctx.send(f"🎲 {joke}")
                except Exception as e:
                    await ctx.send(f"❌ Error: {str(e)}")
        
        # Text command: !thegame (Easter egg)
        @self.bot.command(name='thegame')
        async def thegame_text(ctx):
            """You just lost The Game! (Easter egg)"""
            async with ctx.typing():
                try:
                    joke = self.generator.generate_joke(
                        flavor="thegame",
                        meanness=11,  # THESE GO TO ELEVEN! 🎸
                        nerdiness=5,
                        target_name=None
                    )
                    embed = discord.Embed(
                        description=f"🎮💀 {joke}",
                        color=discord.Color.purple()
                    )
                    embed.set_footer(text="You just lost The Game. Sorry! 😈")
                    await ctx.send(embed=embed)
                except Exception as e:
                    await ctx.send(f"❌ Error: {str(e)}")
        
        # Text command: help
        @self.bot.command(name='help')
        async def help_text(ctx):
            """Show help information (text command)"""
            embed = discord.Embed(
                title="🎤 Yo Mama Bot - Help",
                description="AI-powered Yo Mama joke generator with customizable meanness and nerdiness!",
                color=discord.Color.purple()
            )
            
            prefix = self.bot.command_prefix
            
            # Commands section
            embed.add_field(
                name="📝 Text Commands",
                value=(
                    f"`{prefix}joke [flavor] [meanness] [nerdiness]`\n"
                    "Generate a custom Yo Mama joke\n\n"
                    f"`{prefix}random`\n"
                    "Generate a completely random joke\n\n"
                    f"`{prefix}flavors`\n"
                    "List all available joke flavors\n\n"
                    f"`{prefix}help`\n"
                    "Show this help message"
                ),
                inline=False
            )
            
            # Parameters section
            embed.add_field(
                name="⚙️ Parameters",
                value=(
                    "**Meanness (1-10):**\n"
                    "1 = Gentle and playful\n"
                    "10 = Absolutely savage\n\n"
                    "**Nerdiness (1-10):**\n"
                    "1 = Everyone can understand\n"
                    "10 = Extremely technical"
                ),
                inline=False
            )
            
            # Flavors section
            flavors = YoMamaGenerator.list_flavors()
            embed.add_field(
                name="🎯 Available Flavors",
                value=", ".join([f"`{f}`" for f in flavors[:5]]) + f"\n...and {len(flavors) - 5} more! Use `{prefix}flavors` for full list",
                inline=False
            )
            
            # Examples section
            embed.add_field(
                name="💡 Examples",
                value=(
                    f"`{prefix}joke classic 7 1` - Classic fat/ugly jokes, pretty mean\n"
                    f"`{prefix}joke cybersecurity 8 9` - Savage cybersecurity roast\n"
                    f"`{prefix}joke linux 6 10` - Technical Linux joke\n"
                    f"`{prefix}random` - Surprise me!"
                ),
                inline=False
            )
            
            embed.set_footer(text=f"Powered by Google Gemini | Slash commands also available: /help")
            
            await ctx.send(embed=embed)
        
        # Text command: !flavors
        @self.bot.command(name='flavors')
        async def flavors_text(ctx):
            """List available flavors (text command)"""
            flavors = YoMamaGenerator.list_flavors()
            await ctx.send(f"📋 Available flavors:\n" + ", ".join(flavors))
    
    def run(self):
        """Run the Discord bot."""
        token = self.config.get_secret('DISCORD_BOT_TOKEN')
        
        if not token:
            logger.error("DISCORD_BOT_TOKEN not found in configuration")
            raise ValueError("DISCORD_BOT_TOKEN is required")
        
        logger.info("Starting Discord bot...")
        self.bot.run(token)
    
    async def post_to_webhook(self, webhook_url: str, joke: str, settings: Optional[dict] = None):
        """
        Post a joke to a Discord webhook.
        
        Args:
            webhook_url: Discord webhook URL
            joke: The joke to post
            settings: Optional dict with flavor, meanness, nerdiness
        """
        try:
            webhook = discord.Webhook.from_url(webhook_url, session=None)
            
            embed = discord.Embed(
                description=f"🎤 {joke}",
                color=discord.Color.red()
            )
            
            if settings:
                footer_parts = []
                if 'flavor' in settings:
                    footer_parts.append(f"Flavor: {settings['flavor']}")
                if 'meanness' in settings:
                    footer_parts.append(f"M: {settings['meanness']}/10")
                if 'nerdiness' in settings:
                    footer_parts.append(f"N: {settings['nerdiness']}/10")
                
                if footer_parts:
                    embed.set_footer(text=" | ".join(footer_parts))
            
            await webhook.send(embed=embed, username="Yo Mama Bot")
            logger.info("Posted joke to webhook")
            
        except Exception as e:
            logger.error(f"Failed to post to webhook: {e}")
            raise


# Standalone function to run the bot
def run_discord_bot():
    """Run the Discord bot standalone."""
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        bot = DiscordBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    run_discord_bot()
