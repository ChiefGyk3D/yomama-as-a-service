# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0
"""
Matrix bot platform for Yo Mama Bot.

Supports Matrix rooms and commands.
"""

import logging
import asyncio
from typing import Optional
from nio import AsyncClient, MatrixRoom, RoomMessageText, InviteEvent
from ..config import get_config
from ..yo_mama_generator import YoMamaGenerator

logger = logging.getLogger(__name__)


class MatrixBot:
    """
    Matrix bot for generating Yo Mama jokes in Matrix rooms.
    
    Commands:
    - !joke [flavor] [meanness] [nerdiness] - Generate a joke
    - !random - Generate a random joke
    - !batch [count] [flavor] - Generate multiple jokes
    - !flavors - List available flavors
    - !help - Show help message
    """
    
    def __init__(self, config=None):
        """Initialize the Matrix bot."""
        self.config = config or get_config()
        
        # Get Matrix configuration
        self.homeserver = self.config.get_secret('MATRIX_HOMESERVER', 'https://matrix.org')
        # Ensure homeserver URL has a protocol
        if not self.homeserver.startswith(('http://', 'https://')):
            self.homeserver = f'https://{self.homeserver}'
        
        self.user_id = self.config.get_secret('MATRIX_USER_ID')
        self.access_token = self.config.get_secret('MATRIX_ACCESS_TOKEN')
        self.password = self.config.get_secret('MATRIX_PASSWORD')
        self.device_id = self.config.get_secret('MATRIX_DEVICE_ID', 'yo_mama_bot')
        
        # Require either access token OR username+password
        if not self.user_id:
            raise ValueError("MATRIX_USER_ID is required")
        
        if not self.access_token and not self.password:
            raise ValueError("Either MATRIX_ACCESS_TOKEN or MATRIX_PASSWORD is required")
        
        # Initialize Matrix client
        self.client = AsyncClient(
            homeserver=self.homeserver,
            user=self.user_id,
            device_id=self.device_id
        )
        
        # Set access token if provided, otherwise we'll login with password
        if self.access_token:
            self.client.access_token = self.access_token
            self.use_password_login = False
        else:
            self.use_password_login = True
        
        # Initialize joke generator
        self.generator = YoMamaGenerator(
            api_key=self.config.gemini_api_key,
            model_name=self.config.gemini_model
        )
        self.prefix = self.config.get_config('MATRIX_PREFIX', '!')
        
        # Auto-join rooms
        self.auto_join = self.config.get_bool('MATRIX_AUTO_JOIN', True)
        
        # Setup callbacks
        self._setup_callbacks()
        
        logger.info(f"Matrix bot initialized for {self.user_id}")
    
    def _setup_callbacks(self):
        """Setup Matrix event callbacks."""
        
        # Handle room messages
        self.client.add_event_callback(self._handle_message, RoomMessageText)
        
        # Handle room invites
        if self.auto_join:
            self.client.add_event_callback(self._handle_invite, InviteEvent)
    
    async def _handle_invite(self, room: MatrixRoom, event: InviteEvent):
        """Auto-join rooms when invited."""
        logger.info(f"Invited to room {room.room_id}")
        try:
            await self.client.join(room.room_id)
            logger.info(f"Joined room {room.room_id}")
        except Exception as e:
            logger.error(f"Failed to join room: {e}")
    
    async def _handle_message(self, room: MatrixRoom, event: RoomMessageText):
        """Handle incoming messages."""
        # Ignore our own messages
        if event.sender == self.user_id:
            return
        
        message = event.body.strip()
        
        # Check if message starts with prefix
        if not message.startswith(self.prefix):
            return
        
        # Parse command
        parts = message[len(self.prefix):].split()
        if not parts:
            return
        
        command = parts[0].lower()
        args = parts[1:]
        
        logger.info(f"Command '{command}' from {event.sender} in {room.room_id}")
        
        # Route commands
        try:
            if command == 'joke':
                await self._cmd_joke(room, args)
            elif command == 'random':
                await self._cmd_random(room)
            elif command == 'batch':
                await self._cmd_batch(room, args)
            elif command == 'flavors':
                await self._cmd_flavors(room)
            elif command == 'help':
                await self._cmd_help(room)
            else:
                await self._send_message(room, f"Unknown command: {command}. Try !help")
        except Exception as e:
            logger.error(f"Error handling command: {e}")
            await self._send_message(room, f"❌ Error: {str(e)}")
    
    async def _cmd_joke(self, room: MatrixRoom, args: list):
        """Handle !joke command."""
        # Parse arguments: [flavor] [meanness] [nerdiness]
        flavor = args[0] if len(args) > 0 else None
        meanness = int(args[1]) if len(args) > 1 else self.config.default_meanness
        nerdiness = int(args[2]) if len(args) > 2 else self.config.default_nerdiness
        
        # Validate
        if meanness < 1 or meanness > 11:
            await self._send_message(room, "❌ Meanness must be between 1 and 11 (these go to eleven! 🎸)")
            return
        
        if nerdiness < 1 or nerdiness > 10:
            await self._send_message(room, "❌ Nerdiness must be between 1 and 10")
            return
        
        # Generate joke
        await self._send_message(room, "🎤 Generating joke...")
        
        joke = self.generator.generate_joke(
            flavor=flavor,
            meanness=meanness,
            nerdiness=nerdiness
        )
        
        # Format message
        settings = f"[Flavor: {flavor or 'random'}, M: {meanness}/10, N: {nerdiness}/10]"
        message = f"🎤 {joke}\n\n<i>{settings}</i>"
        
        await self._send_message(room, message, html=True)
    
    async def _cmd_random(self, room: MatrixRoom):
        """Handle !random command."""
        await self._send_message(room, "🎲 Generating random joke...")
        
        joke = self.generator.random_joke()
        await self._send_message(room, f"🎲 {joke}")
    
    async def _cmd_batch(self, room: MatrixRoom, args: list):
        """Handle !batch command."""
        # Parse arguments: [count] [flavor]
        try:
            count = int(args[0]) if len(args) > 0 else 3
        except ValueError:
            await self._send_message(room, "❌ Count must be a number")
            return
        
        if count < 1 or count > 10:
            await self._send_message(room, "❌ Count must be between 1 and 10")
            return
        
        flavor = args[1] if len(args) > 1 else None
        
        await self._send_message(room, f"🔥 Generating {count} jokes...")
        
        jokes = self.generator.generate_batch(
            count=count,
            flavor=flavor,
            meanness=self.config.default_meanness,
            nerdiness=self.config.default_nerdiness
        )
        
        # Format message
        message_parts = [f"🔥 <b>{count} Yo Mama Jokes</b>"]
        for i, joke in enumerate(jokes, 1):
            message_parts.append(f"\n{i}. {joke}")
        
        message = "\n".join(message_parts)
        await self._send_message(room, message, html=True)
    
    async def _cmd_flavors(self, room: MatrixRoom):
        """Handle !flavors command."""
        flavors = YoMamaGenerator.list_flavors()
        message = "📋 <b>Available Flavors:</b>\n" + "\n".join([f"• {flavor}" for flavor in flavors])
        await self._send_message(room, message, html=True)
    
    async def _cmd_help(self, room: MatrixRoom):
        """Handle !help command."""
        help_text = """
🎤 <b>Yo Mama Bot - Help</b>

<b>Commands:</b>
• <code>!joke [flavor] [meanness] [nerdiness]</code> - Generate a joke
  Example: <code>!joke cybersecurity 8 9</code>

• <code>!random</code> - Generate a random joke

• <code>!batch [count] [flavor]</code> - Generate multiple jokes
  Example: <code>!batch 5 tech</code>

• <code>!flavors</code> - List available flavors

• <code>!help</code> - Show this help message

<b>Parameters:</b>
• Meanness: 1-10 (1=gentle, 10=brutal)
• Nerdiness: 1-10 (1=accessible, 10=very technical)

<b>Flavors:</b> cybersecurity, tech, linux, gaming, programming, networking, cloud, devops, database, general
        """
        await self._send_message(room, help_text.strip(), html=True)
    
    async def _send_message(self, room: MatrixRoom, message: str, html: bool = False):
        """Send a message to a room."""
        try:
            if html:
                # Convert markdown-style formatting to HTML
                html_message = message.replace('\n', '<br/>')
                content = {
                    "msgtype": "m.text",
                    "body": message,
                    "format": "org.matrix.custom.html",
                    "formatted_body": html_message
                }
            else:
                content = {
                    "msgtype": "m.text",
                    "body": message
                }
            
            await self.client.room_send(
                room_id=room.room_id,
                message_type="m.room.message",
                content=content
            )
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    async def send_joke_to_room(self, room_id: str, joke: str, settings: Optional[dict] = None):
        """
        Send a joke to a specific room.
        
        Args:
            room_id: Matrix room ID
            joke: The joke to send
            settings: Optional dict with flavor, meanness, nerdiness
        """
        try:
            message = f"🎤 {joke}"
            
            if settings:
                parts = []
                if 'flavor' in settings:
                    parts.append(f"Flavor: {settings['flavor']}")
                if 'meanness' in settings:
                    parts.append(f"M: {settings['meanness']}/10")
                if 'nerdiness' in settings:
                    parts.append(f"N: {settings['nerdiness']}/10")
                
                if parts:
                    message += f"\n\n<i>[{' | '.join(parts)}]</i>"
            
            content = {
                "msgtype": "m.text",
                "body": joke,
                "format": "org.matrix.custom.html",
                "formatted_body": message.replace('\n', '<br/>')
            }
            
            await self.client.room_send(
                room_id=room_id,
                message_type="m.room.message",
                content=content
            )
            
            logger.info(f"Sent joke to room {room_id}")
            
        except Exception as e:
            logger.error(f"Failed to send joke to room: {e}")
            raise
    
    async def start(self):
        """Start the Matrix bot."""
        logger.info("Starting Matrix bot...")
        
        try:
            # Login with password if needed
            if self.use_password_login:
                logger.info(f"Logging in as {self.user_id} with password...")
                response = await self.client.login(self.password)
                
                if hasattr(response, 'access_token'):
                    logger.info("Login successful!")
                    logger.info(f"Access token: {response.access_token[:20]}... (save this to MATRIX_ACCESS_TOKEN)")
                else:
                    raise Exception(f"Login failed: {response}")
            else:
                logger.info(f"Using existing access token for {self.user_id}")
            
            # Sync and run forever
            await self.client.sync_forever(timeout=30000, full_state=True)
        except Exception as e:
            logger.error(f"Bot error: {e}")
            raise
        finally:
            await self.client.close()
    
    def run(self):
        """Run the Matrix bot (blocking)."""
        asyncio.run(self.start())


# Standalone function to run the bot
def run_matrix_bot():
    """Run the Matrix bot standalone."""
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        bot = MatrixBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    run_matrix_bot()
