# 🤖 Discord & Matrix Bot Setup Guide

Complete guide for setting up and running **YoMama-as-a-Service** on Discord and Matrix platforms.

---

## 📋 Prerequisites

- Python 3.10+
- Google Gemini API key
- Discord Developer account (for Discord bot)
- Matrix account (for Matrix bot)

---

## 🔷 Discord Bot Setup

### Step 1: Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Give it a name (e.g., "Yo Mama Bot")
4. Go to the "Bot" section in the left sidebar
5. Click "Add Bot" → "Yes, do it!"

### Step 2: Configure Bot

1. **Copy the bot token:**
   - Click "Reset Token" (if needed)
   - Copy the token - you'll need this for `.env`

2. **Enable required intents:**
   - Scroll down to "Privileged Gateway Intents"
   - Enable: `MESSAGE CONTENT INTENT`
   - Enable: `SERVER MEMBERS INTENT` (optional)

3. **Set bot permissions:**
   - Go to "OAuth2" → "URL Generator"
   - Select scopes: `bot` and `applications.commands`
   - Select bot permissions:
     - Read Messages/View Channels
     - Send Messages
     - Send Messages in Threads
     - Embed Links
     - Read Message History
     - Use Slash Commands

### Step 3: Invite Bot to Server

1. Copy the generated OAuth2 URL
2. Open it in your browser
3. Select your server
4. Authorize the bot

### Step 4: Configure Environment

Edit your `.env` file:

```env
# Discord Configuration
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_PREFIX=!
```

### Step 5: Run the Bot

```bash
# Using the dedicated script
./run_discord.sh

# Or directly
python main.py --discord
```

### Discord Commands

**Slash Commands (recommended):**
```
/joke [flavor] [meanness] [nerdiness] [target]
/random
/batch [count] [flavor] [meanness] [nerdiness]
/flavors
/help
```

**Text Commands (legacy):**
```
!joke [flavor] [meanness] [nerdiness]
!random
!flavors
!help
```

**Examples:**
```
/joke classic 8 1         # Traditional Yo Mama joke, savage but accessible
/joke cybersecurity 8 9   # Technical cybersecurity roast
/joke tech 5 5 "your code"
/batch 3 linux 6 8
/random
/help                     # Show all available commands
```

---

## 🔷 Matrix Bot Setup

### Step 1: Create Matrix Account

Option A: Use existing account
- You can use your personal account or create a dedicated bot account

Option B: Create new account
1. Go to https://app.element.io or your homeserver's web client
2. Click "Create Account"
3. Choose your homeserver (matrix.org or your own)
4. Complete registration

### Step 2: Configure Authentication

You have **two options** for authentication:

#### Option A: Use Password (Easier for Testing)

The bot will login with your password and show you the access token.

```env
# Matrix Configuration
MATRIX_HOMESERVER=https://matrix.org
MATRIX_USER_ID=@yourbot:matrix.org
MATRIX_PASSWORD=your_password_here
MATRIX_DEVICE_ID=yo_mama_bot
MATRIX_PREFIX=!
MATRIX_AUTO_JOIN=true
```

When the bot starts, it will display the access token in the logs. You can then save it for future use.

#### Option B: Use Access Token (Recommended for Production)

**Getting your access token from Element:**
1. Log in to Element Web (https://app.element.io)
2. Click your avatar → "All Settings"
3. Go to "Help & About"
4. Scroll down and click "Access Token"
5. Click the eye icon to reveal and copy the token

**Or use curl:**
```bash
curl -X POST \
  'https://matrix.org/_matrix/client/r0/login' \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "m.login.password",
    "user": "your_username",
    "password": "your_password"
  }'
```

```env
# Matrix Configuration
MATRIX_HOMESERVER=https://matrix.org
MATRIX_USER_ID=@yourbot:matrix.org
MATRIX_ACCESS_TOKEN=your_access_token_here
MATRIX_DEVICE_ID=yo_mama_bot
MATRIX_PREFIX=!
MATRIX_AUTO_JOIN=true
```

### Step 3: Start the Bot

**Important:**
- `MATRIX_USER_ID` must be your full Matrix ID including the homeserver (e.g., `@bot:matrix.org`)
- `MATRIX_HOMESERVER` should match your homeserver URL
- `MATRIX_AUTO_JOIN=true` makes the bot automatically join rooms when invited

### Step 4: Run the Bot

```bash
# Using the dedicated script
./run_matrix.sh

# Or directly
python main.py --matrix
```

### Step 5: Invite Bot to Room

1. Create or open a room in Element/Matrix client
2. Click the room info → "Invite"
3. Enter your bot's user ID (e.g., `@yourbot:matrix.org`)
4. The bot will automatically join (if `MATRIX_AUTO_JOIN=true`)

### Matrix Commands

All commands use the prefix `!` (configurable):

```
!joke [flavor] [meanness] [nerdiness]
!random
!batch [count] [flavor]
!flavors
!help
```

**Examples:**
```
!joke classic 8 1         # Traditional Yo Mama joke
!joke cybersecurity 8 9   # Technical cybersecurity roast
!joke tech 5 5
!batch 3 linux
!random
!help                     # Show all commands and parameters
```

---

## 🔧 Troubleshooting

### Discord Bot Issues

**Bot is offline:**
- Check that `DISCORD_BOT_TOKEN` is correct in `.env`
- Verify the bot has been invited to your server
- Check console for error messages

**Slash commands not appearing:**
- Wait a few minutes for Discord to sync commands
- Try kicking and re-inviting the bot
- Check bot has `applications.commands` scope

**Bot can't send messages:**
- Verify bot has "Send Messages" permission
- Check channel permissions allow the bot to post

### Matrix Bot Issues

**Bot won't start:**
- Verify `MATRIX_ACCESS_TOKEN` is correct
- Check `MATRIX_USER_ID` format (must include homeserver)
- Ensure `MATRIX_HOMESERVER` URL is correct

**Bot doesn't join rooms:**
- Set `MATRIX_AUTO_JOIN=true` in `.env`
- Check console logs for invite events
- Manually accept invite through Element if needed

**Commands not working:**
- Verify commands start with `!` (or your configured prefix)
- Check bot has permission to read messages in the room
- Look for error messages in console

### General Issues

**Missing dependencies:**
```bash
pip install -r requirements.txt
```

**Import errors:**
```bash
# Make sure you're in the project root
cd /path/to/Yo_Mama
python main.py --discord
```

**Configuration errors:**
```bash
# Run the test script
python test_setup.py
```

---

## 🎯 Best Practices

### Security

1. **Never commit tokens:**
   - Keep `.env` in `.gitignore`
   - Use Doppler for production secrets

2. **Use separate bot accounts:**
   - Don't use your personal accounts for bots
   - Create dedicated bot accounts for each platform

3. **Rotate tokens regularly:**
   - Regenerate bot tokens periodically
   - Update tokens in both `.env` and Doppler

### Performance

1. **Rate limiting:**
   - Discord: ~50 commands per second per server
   - Matrix: Depends on homeserver (usually ~10/sec)

2. **Response times:**
   - Gemini API calls take 2-5 seconds
   - Bot sends "thinking" indicator while generating

3. **Resource usage:**
   - Minimal CPU when idle
   - ~100-200MB RAM per bot instance
   - Network: depends on usage

### Deployment

**Running on a server:**

```bash
# Using screen
screen -S yo_mama_discord
./run_discord.sh
# Press Ctrl+A, then D to detach

# Using tmux
tmux new -s yo_mama_discord
./run_discord.sh
# Press Ctrl+B, then D to detach

# Using systemd (see deployment guide below)
```

**Systemd service (Linux):**

Create `/etc/systemd/system/yo-mama-discord.service`:

```ini
[Unit]
Description=Yo Mama Discord Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/Yo_Mama
Environment="PATH=/path/to/Yo_Mama/venv/bin"
ExecStart=/path/to/Yo_Mama/venv/bin/python main.py --discord
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable yo-mama-discord
sudo systemctl start yo-mama-discord
sudo systemctl status yo-mama-discord
```

---

## 📊 Monitoring

**View logs:**
```bash
# If using systemd
sudo journalctl -u yo-mama-discord -f

# If using screen
screen -r yo_mama_discord

# If using tmux
tmux attach -t yo_mama_discord
```

**Check bot status:**
- Discord: Check online status in server
- Matrix: Send `!help` command in a room

---

## 🎨 Customization

**Change command prefix:**
```env
DISCORD_PREFIX=yo!
MATRIX_PREFIX=mama!
```

**Adjust default settings:**
```env
DEFAULT_FLAVOR=cybersecurity
DEFAULT_MEANNESS=7
DEFAULT_NERDINESS=8
```

**Change AI model:**
```env
GEMINI_MODEL=gemini-1.5-pro
```

---

## 📞 Support

If you encounter issues:

1. Run the test script: `python test_setup.py`
2. Check the logs for error messages
3. Verify all configuration in `.env`
4. Ensure all dependencies are installed
5. Check the main README.md for more details

---

**Happy roasting! 🔥**

---

*This project is licensed under the Mozilla Public License 2.0 (MPL-2.0). See the `LICENSE` file for details.*
