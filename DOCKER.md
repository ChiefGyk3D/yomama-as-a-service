# 🐳 Docker Deployment Guide

This guide explains how to build and deploy **YoMama-as-a-Service** using Docker and Docker Compose.

---

## 🎯 Prerequisites

- Docker 20.10+ installed
- Docker Compose 2.0+ installed
- Your API keys and bot tokens ready (or an Ollama server, if you'd rather not
  use a cloud API — see [Environment Variables](#-environment-variables))
- A `.env` file configured (see below)

---

## 🚀 Quick Start

### 1. Get the Docker Image

**Option A: Pull the published image (fastest)**

Multi-arch images (linux/amd64 and linux/arm64, so Raspberry Pi works) are
published to the GitHub Container Registry on every push to `main` (tagged
`latest`) or `develop`, and for every `v*.*.*` release tag:

```bash
docker pull ghcr.io/chiefgyk3d/yomama-as-a-service:latest

# Or pin a release
docker pull ghcr.io/chiefgyk3d/yomama-as-a-service:v1.0.0
```

**Option B: Build it yourself**

The build process will automatically update all OS packages:

```bash
./docker-build.sh
```

Or manually:

```bash
docker build --no-cache --pull -t yomama-as-a-service:latest .
```

`docker-compose.yml` builds from source by default. To run the published image
instead, replace the `build:` block of each service with
`image: ghcr.io/chiefgyk3d/yomama-as-a-service:latest`.

### 2. Configure Environment

Copy and edit the `.env` file:

```bash
cp .env.example .env
nano .env  # or your preferred editor
```

Add your API keys and configuration.

### 3. Run with Docker Compose

**Run both bots:**
```bash
docker-compose up -d
```

**Run only Discord bot:**
```bash
docker-compose up -d yomama-discord
```

**Run only Matrix bot:**
```bash
docker-compose up -d yomama-matrix
```

---

## 📋 Docker Architecture

### Multi-Stage Build

The Dockerfile uses a multi-stage build process:

1. **Builder Stage**: 
   - Updates OS packages (`apt-get upgrade`)
   - Installs build dependencies
   - Compiles Python packages

2. **Final Stage**:
   - Updates OS packages again
   - Copies compiled packages from builder
   - Minimal runtime dependencies
   - Runs as non-root user (`yomama`)

### Security Features

- ✅ Runs as non-root user (UID 1000)
- ✅ Multi-stage build (smaller attack surface)
- ✅ No cache for pip installs
- ✅ Health checks enabled
- ✅ Updated OS packages
- ✅ Minimal base image (python:3.14-slim)

---

## 🔧 Docker Commands

### View Logs

```bash
# Follow all logs
docker-compose logs -f

# Follow specific bot
docker-compose logs -f yomama-discord
docker-compose logs -f yomama-matrix

# View last 100 lines
docker-compose logs --tail=100
```

### Manage Containers

```bash
# Stop all bots
docker-compose down

# Stop specific bot
docker-compose stop yomama-discord

# Restart bots
docker-compose restart

# View status
docker-compose ps

# View resource usage
docker stats
```

### Update and Rebuild

```bash
# Pull latest changes
git pull

# Rebuild with updated packages
./docker-build.sh

# Or manually with no cache
docker build --no-cache --pull -t yomama-as-a-service:latest .

# Restart services
docker-compose down
docker-compose up -d
```

---

## 🌐 Environment Variables

All environment variables from `.env` are passed to containers. Key variables:

### Required
- `GEMINI_API_KEY` - Google Gemini API key (not needed for an Ollama-only setup)
- `DISCORD_BOT_TOKEN` - Discord bot token (for Discord bot)
- `MATRIX_HOMESERVER` - Matrix homeserver URL (for Matrix bot)
- `MATRIX_USER_ID` - Matrix user ID (for Matrix bot)
- `MATRIX_ACCESS_TOKEN` or `MATRIX_PASSWORD` - Matrix auth

### LLM Backend (Optional)
Both services pass these through to the hypeman-social LLM layer:
- `LLM_PROVIDER` - `gemini` (default) or `ollama`
- `LLM_FALLBACK_PROVIDER` - failover backend, e.g. `gemini` behind an Ollama primary
- `LLM_OLLAMA_HOST` - Ollama server host (default: `http://localhost`)
- `LLM_OLLAMA_PORT` - Ollama server port (default: `11434`)
- `LLM_OLLAMA_MODEL` - Ollama model (default: `gemma3:4b`)
- `GEMINI_MODEL` - Gemini model (default: gemini-2.5-flash-lite)

> **Containers and `localhost`:** inside a container, `http://localhost` is the
> container itself. Point `LLM_OLLAMA_HOST` at your host's LAN address, or at
> `http://host.docker.internal` (add
> `extra_hosts: ["host.docker.internal:host-gateway"]` on Linux).

### Bot Defaults (Optional)
- `DEFAULT_FLAVOR` - Default joke flavor (default: tech)
- `DEFAULT_MEANNESS` - Meanness level 1-11 (default: 5)
- `DEFAULT_NERDINESS` - Nerdiness level 1-10 (default: 5)
- `LOG_LEVEL` - Logging level (default: INFO)
- `DISCORD_PREFIX` - Text-command prefix (default in `.env.example`: `$`)
- `MATRIX_PREFIX` / `MATRIX_AUTO_JOIN` / `MATRIX_DEVICE_ID` - Matrix behavior

### Secrets Management (Optional)
- `DOPPLER_TOKEN` - Doppler service token
- `DOPPLER_PROJECT` - Doppler project name
- `DOPPLER_CONFIG` - Doppler config/environment

---

## 📊 Health Checks

Both containers have health checks enabled:

- **Interval**: Every 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3 attempts before marking unhealthy
- **Start Period**: 10 seconds grace period on startup

Check health status:
```bash
docker-compose ps
```

---

## 🔒 Production Deployment

### Using Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml yomama

# View services
docker stack services yomama

# Remove stack
docker stack rm yomama
```

### Using Kubernetes

Generate Kubernetes manifests:
```bash
# Install kompose
curl -L https://github.com/kubernetes/kompose/releases/download/v1.31.2/kompose-linux-amd64 -o kompose
chmod +x kompose
sudo mv kompose /usr/local/bin/

# Convert docker-compose to k8s
kompose convert -f docker-compose.yml

# Apply to cluster
kubectl apply -f .
```

### Secrets in Production

**Option 1: Docker Secrets (Swarm)**
```bash
# Create secrets
echo "your-api-key" | docker secret create gemini_api_key -
echo "your-bot-token" | docker secret create discord_token -

# Update compose file to use secrets
# See Docker Swarm secrets documentation
```

**Option 2: Doppler**
```yaml
# In docker-compose.yml, set:
environment:
  - DOPPLER_TOKEN=your_token_here
  # Other secrets will be loaded from Doppler
```

**Option 3: Kubernetes Secrets**
```bash
# Create k8s secret
kubectl create secret generic yomama-secrets \
  --from-literal=GEMINI_API_KEY=your-key \
  --from-literal=DISCORD_BOT_TOKEN=your-token
```

---

## 🐛 Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs yomama-discord

# Check if image built correctly
docker images | grep yomama

# Rebuild without cache
docker-compose build --no-cache
```

### Permission errors

```bash
# Ensure files are readable
chmod 644 .env
chmod -R 755 yo_mama/

# Check container user
docker-compose exec yomama-discord whoami
# Should output: yomama
```

### Network issues

```bash
# Check network
docker network ls
docker network inspect yomama-as-a-service_yomama-network
# (Compose prefixes the network with the project name — usually the directory name;
#  run `docker network ls` if yours differs)

# Restart network
docker-compose down
docker network prune -f
docker-compose up -d
```

### Bot not responding

```bash
# Check if bot is running
docker-compose ps

# Check health
docker inspect yomama-discord | grep Health

# Restart bot
docker-compose restart yomama-discord
```

---

## 📈 Monitoring

### Basic Monitoring

```bash
# Resource usage
docker stats

# Logs with timestamps
docker-compose logs -f --timestamps

# Export logs
docker-compose logs > logs/docker-$(date +%Y%m%d).log
```

### Advanced Monitoring

Consider integrating:
- **Prometheus** - Metrics collection
- **Grafana** - Metrics visualization
- **Loki** - Log aggregation
- **cAdvisor** - Container metrics

Example Prometheus configuration:
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'docker'
    static_configs:
      - targets: ['cadvisor:8080']
```

---

## 🔄 Updates and Maintenance

### Regular Updates

```bash
# Weekly update cycle
./docker-build.sh
docker-compose down
docker-compose up -d

# Verify bots are working
docker-compose logs --tail=50
```

### Automated Updates

Add to crontab:
```bash
# Edit crontab
crontab -e

# Add weekly rebuild (Sunday 2 AM)
0 2 * * 0 cd /path/to/yomama-as-a-service && ./docker-build.sh && docker-compose down && docker-compose up -d
```

### Backup Strategy

```bash
# Backup script
#!/bin/bash
BACKUP_DIR="/backup/yomama"
DATE=$(date +%Y%m%d)

# Backup .env
cp .env "$BACKUP_DIR/env-$DATE.backup"

# Export container configs
docker inspect yomama-discord > "$BACKUP_DIR/discord-config-$DATE.json"
docker inspect yomama-matrix > "$BACKUP_DIR/matrix-config-$DATE.json"
```

---

## 🎯 Performance Tuning

### Resource Limits

Add to `docker-compose.yml`:

```yaml
services:
  yomama-discord:
    # ... existing config ...
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

### Logging Configuration

```yaml
services:
  yomama-discord:
    # ... existing config ...
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

*This project is licensed under the Mozilla Public License 2.0 (MPL-2.0). See the `LICENSE` file for details.*
