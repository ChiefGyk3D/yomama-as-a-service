# 🚀 YoMama-as-a-Service - Quick Start Guide

## Installation (3 steps)

```bash
# 1. Run setup script
./setup.sh

# 2. Edit .env and add your API key
nano .env  # or use your preferred editor
# Add: GEMINI_API_KEY=your_actual_api_key_here

# 3. Run the bot (choose mode)
./run.sh              # CLI interactive mode
./run.sh --discord    # Discord bot
./run.sh --matrix     # Matrix bot
```

## Common Usage

### Running as Discord Bot

```bash
# Make sure DISCORD_BOT_TOKEN is set in .env
./run.sh --discord

# Or directly
python main.py --discord
```

**Discord Commands:**
- `/joke classic 8 1` - Traditional Yo Mama joke (savage, accessible)
- `/joke cybersecurity 8 9` - Harsh, nerdy cybersecurity roast
- `/random` - Random joke with random settings
- `/batch 5 tech` - Generate 5 tech jokes
- `/flavors` - List all available flavors
- `/help` - Show complete help

### Running as Matrix Bot

```bash
# Make sure MATRIX_* credentials are set in .env
./run.sh --matrix

# Or directly
python main.py --matrix
```

**Matrix Commands:**
- `!joke classic 8 1` - Traditional Yo Mama joke
- `!joke cybersecurity 8 9` - Technical cybersecurity roast
- `!random` - Random joke with random settings
- `!batch 5 tech` - Generate 5 jokes
- `!flavors` - List all available flavors
- `!help` - Show complete help

### CLI Mode

```bash
# Interactive mode (recommended for first-time users)
./run.sh

# Quick single joke
./run.sh -f cybersecurity -m 7 -n 8

# Generate 5 jokes
./run.sh -b 5 -f tech

# Random joke
./run.sh -r

# See all options
./run.sh --help

# List available flavors
./run.sh --flavors
```

## Interactive Mode Commands

Once in interactive mode, you can use:

```
[Enter]         Generate joke with current settings
f tech          Change flavor to tech
m 8             Set meanness to 8
n 9             Set nerdiness to 9
b 5             Generate 5 jokes
r               Random joke
settings        Show current settings
flavors         List all flavors
quit            Exit
```

## Doppler Setup (Optional)

If you want to use Doppler for secrets management:

```bash
# Install Doppler CLI
brew install dopplersdk/tap/doppler  # macOS
# or visit: https://docs.doppler.com/docs/install-cli

# Login and setup
doppler login
doppler setup

# Add secrets
doppler secrets set GEMINI_API_KEY="your_key"
doppler secrets set DEFAULT_FLAVOR="cybersecurity"
doppler secrets set DEFAULT_MEANNESS="7"
doppler secrets set DEFAULT_NERDINESS="8"

# Run with Doppler
doppler run -- python main.py
```

## Examples

### Cybersecurity Jokes
```bash
# Brutal, highly technical
./run.sh -f cybersecurity -m 9 -n 10

# Moderate roasting
./run.sh -f cybersecurity -m 5 -n 7
```

### Linux Jokes
```bash
# Command-line humor
./run.sh -f linux -m 6 -n 8

# Generate batch
./run.sh -b 3 -f linux -m 7 -n 9
```

### Custom Target
```bash
# Roast something other than "yo mama"
./run.sh -f programming -t "your code" -m 8
./run.sh -f devops -t "your CI/CD pipeline" -m 7
```

## Troubleshooting

### No API key error
```bash
# Make sure you've edited .env
cat .env | grep GEMINI_API_KEY
# Should show: GEMINI_API_KEY=your_actual_key
```

### Module not found
```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt
```

### Permission denied
```bash
# Make scripts executable
chmod +x setup.sh run.sh main.py
```

## Tips

- Start with **meanness 5** and **nerdiness 5** to get a feel
- Use **interactive mode** to experiment with settings quickly
- Try **batch mode** (`-b 5`) to compare multiple jokes at once
- Use **random mode** (`-r`) for variety
- Cybersecurity jokes work best with high nerdiness (8-10)
- General jokes should use lower nerdiness (3-5) for wider appeal

---

For full documentation, see [README.md](README.md)

---

*This project is licensed under the Mozilla Public License 2.0 (MPL-2.0). See the `LICENSE` file for details.*
