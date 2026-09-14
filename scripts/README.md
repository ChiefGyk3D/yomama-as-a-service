# YoMama-as-a-Service Scripts

This directory contains utility scripts for YoMama bot setup, configuration, and management.

## 🔧 Available Scripts

### create-secrets.sh
**Interactive secrets setup wizard**

Helps you configure API keys and bot credentials across multiple secrets management platforms.

**Usage:**
```bash
./scripts/create-secrets.sh
```

**Features:**
- ✅ Supports Doppler, AWS Secrets Manager, HashiCorp Vault, and .env files
- ✅ Interactive prompts for Discord and Matrix credentials
- ✅ Gemini API key configuration
- ✅ Loads existing .env values as defaults
- ✅ Environment-aware (dev/staging/production)

> After running it, check the generated `.env` against
> [`.env.example`](../.env.example) — the wizard is shared with sibling projects
> and may not prompt for every key this bot reads (for example the `LLM_*`
> Ollama settings).

---

### install-yomama.sh
**systemd service installation script**

Installs YoMama-as-a-Service as a Linux systemd service with automatic startup.

**Usage:**
```bash
sudo ./scripts/install-yomama.sh
```

**Features:**
- ✅ Supports both Python and Docker deployments
- ✅ Creates Python virtual environment (Python mode)
- ✅ Pulls `ghcr.io/chiefgyk3d/yomama-as-a-service:latest`, or builds locally (Docker mode)
- ✅ Configures automatic restart on failure
- ✅ Sets up proper permissions and security
- ✅ Loads configuration from .env file

**Service name:** you choose the platform during installation, and the unit is
named after it — `yomama-discord`, `yomama-matrix`, or `yomama-both`.

---

### uninstall-yomama.sh
**systemd service removal script**

Removes the YoMama systemd service and optionally cleans up Docker resources.

**Usage:**
```bash
sudo ./scripts/uninstall-yomama.sh
```

**Features:**
- ✅ Stops and disables service
- ✅ Removes systemd service file
- ✅ Cleans up Docker containers (Docker mode)
- ✅ Optionally removes Docker images
- ✅ Preserves .env and project files by default

---

### setup_matrix_bot.sh
**Matrix bot configuration helper**

Helps set up Matrix bot credentials and room configuration.

**Usage:**
```bash
./scripts/setup_matrix_bot.sh
```

---

## 📋 Prerequisites

**All scripts require:**
- Linux operating system
- Bash shell

**create-secrets.sh requires:**
- Python 3.10+ installed
- Platform-specific tools (optional):
  - Doppler CLI for Doppler integration
  - AWS CLI for AWS Secrets Manager
  - Vault CLI for HashiCorp Vault

**install-yomama.sh requires:**
- Root/sudo access
- systemd (Linux)
- For Python mode: Python 3.10+, pip
- For Docker mode: Docker, Docker Compose

---

## 🚀 Quick Start

**First-time setup:**

1. **Configure secrets:**
   ```bash
   ./scripts/create-secrets.sh
   ```

2. **Install as service:**
   ```bash
   sudo ./scripts/install-yomama.sh
   ```

3. **Manage service** (substitute the service you installed — `yomama-discord`,
   `yomama-matrix`, or `yomama-both`):
   ```bash
   sudo systemctl status yomama-discord
   sudo systemctl stop yomama-discord
   sudo systemctl start yomama-discord
   sudo journalctl -u yomama-discord -f
   ```

**To uninstall:**
```bash
sudo ./scripts/uninstall-yomama.sh
```

---

## 📚 See Also

- [Main README](../README.md)
- [Quick Start Guide](../QUICKSTART.md)
- [Bot Setup Guide](../BOT_SETUP.md)
- [Secrets Management](../SECRETS_MANAGEMENT.md)
- [Docker Guide](../DOCKER.md)

---

**Happy roasting! 🎤🔥**
