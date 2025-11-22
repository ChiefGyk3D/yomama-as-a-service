# 🔒 Secrets Management Guide

Comprehensive guide for managing secrets in **YoMama-as-a-Service** using Doppler, AWS Secrets Manager, HashiCorp Vault, or .env files.

---

## 🎯 Priority System

The bot uses a **priority-based system** for loading secrets:

```
1. Doppler (if DOPPLER_TOKEN is set)           ← HIGHEST PRIORITY
2. AWS Secrets Manager (if SECRETS_MANAGER=aws)
3. HashiCorp Vault (if SECRETS_MANAGER=vault)
4. Environment variables from .env file         ← FALLBACK
5. Default values                               ← LAST RESORT
```

This ensures production secrets override development secrets, and you can mix multiple secret sources.

---

## 📦 Quick Start (Choose One)

### Option 1: Simple .env File (Recommended for Development)

```bash
# Copy the example
cp .env.example .env

# Edit and add your keys
nano .env
```

**Pros:**
- ✅ Simple and fast
- ✅ Works locally without setup
- ✅ Good for development

**Cons:**
- ❌ Keys visible in plain text
- ❌ Easy to accidentally commit
- ❌ Not suitable for production

### Option 2: Doppler (Recommended for Production)

```bash
# Install Doppler CLI
brew install dopplersdk/tap/doppler  # macOS
# or visit: https://docs.doppler.com/docs/install-cli

# Login and setup
doppler login
doppler setup

# Add secrets
doppler secrets set GEMINI_API_KEY="your_key"
doppler secrets set DISCORD_BOT_TOKEN="your_token"

# Run with Doppler
doppler run -- python main.py --discord
```

**Pros:**
- ✅ Secure, encrypted storage
- ✅ Team collaboration
- ✅ Audit logs
- ✅ Easy rotation
- ✅ Works in CI/CD

**Cons:**
- ⚠️ Requires account setup
- ⚠️ Internet connection needed

### Option 3: AWS Secrets Manager

```bash
# Set in .env
SECRETS_MANAGER=aws

# Secrets stored in AWS console or CLI
aws secretsmanager create-secret \
  --name yo-mama-bot/prod \
  --secret-string '{"gemini_api_key":"your_key","discord_bot_token":"your_token"}'
```

**Pros:**
- ✅ AWS native integration
- ✅ IAM-based access control
- ✅ Automatic rotation
- ✅ Audit via CloudTrail

**Cons:**
- ⚠️ AWS account required
- ⚠️ Costs money (small)
- ⚠️ Requires boto3 package

### Option 4: HashiCorp Vault

```bash
# Set in .env
SECRETS_MANAGER=vault
SECRETS_VAULT_URL=https://vault.example.com:8200
SECRETS_VAULT_TOKEN=your_vault_token

# Secrets stored in Vault
vault kv put secret/yo-mama-bot \
  gemini_api_key=your_key \
  discord_bot_token=your_token
```

**Pros:**
- ✅ Self-hosted option
- ✅ Dynamic secrets
- ✅ Fine-grained access control
- ✅ Works on-premise

**Cons:**
- ⚠️ Vault infrastructure needed
- ⚠️ More complex setup
- ⚠️ Requires hvac package

---

## 🔧 Detailed Configuration

### Doppler Setup

**1. Install Doppler CLI:**

```bash
# macOS
brew install dopplersdk/tap/doppler

# Linux
curl -Ls https://cli.doppler.com/install.sh | sh

# Windows
scoop install doppler
```

**2. Login and create project:**

```bash
doppler login
doppler projects create yo-mama-bot
doppler setup --project yo-mama-bot --config dev
```

**3. Add secrets:**

```bash
# Core secrets
doppler secrets set GEMINI_API_KEY="your_gemini_key"

# Discord bot
doppler secrets set DISCORD_BOT_TOKEN="your_discord_token"
doppler secrets set DISCORD_PREFIX="!"

# Matrix bot
doppler secrets set MATRIX_HOMESERVER="https://matrix.org"
doppler secrets set MATRIX_USER_ID="@bot:matrix.org"
doppler secrets set MATRIX_ACCESS_TOKEN="your_matrix_token"

# Bot settings
doppler secrets set DEFAULT_FLAVOR="cybersecurity"
doppler secrets set DEFAULT_MEANNESS="7"
doppler secrets set DEFAULT_NERDINESS="8"
```

**4. Run your bot:**

```bash
# Option A: Use Doppler to inject secrets
doppler run -- python main.py --discord

# Option B: Set DOPPLER_TOKEN in .env
doppler configure get token --plain > /tmp/token
# Add to .env: DOPPLER_TOKEN=<token>
python main.py --discord
```

**5. Multiple environments:**

```bash
# Create environments
doppler configs create stg
doppler configs create prd

# Switch between them
doppler setup --config stg
doppler setup --config prd

# Or specify in .env
DOPPLER_CONFIG=prd
```

### AWS Secrets Manager Setup

**1. Install boto3:**

```bash
pip install boto3
```

**2. Configure AWS credentials:**

```bash
aws configure
# Or set: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
```

**3. Create secret:**

```bash
aws secretsmanager create-secret \
  --name yo-mama-bot/prod \
  --description "Yo Mama Bot production secrets" \
  --secret-string '{
    "gemini_api_key": "your_key",
    "discord_bot_token": "your_token",
    "matrix_homeserver": "https://matrix.org",
    "matrix_user_id": "@bot:matrix.org",
    "matrix_access_token": "your_token"
  }'
```

**4. Enable in .env:**

```env
SECRETS_MANAGER=aws
```

**5. Use in code:**

```python
from yo_mama.secrets import get_secret

# Automatically checks AWS Secrets Manager first
api_key = get_secret('gemini_api_key', default='fallback_key')
```

### HashiCorp Vault Setup

**1. Install hvac:**

```bash
pip install hvac
```

**2. Configure Vault access:**

```env
SECRETS_MANAGER=vault
SECRETS_VAULT_URL=https://vault.example.com:8200
SECRETS_VAULT_TOKEN=your_vault_token
```

**3. Store secrets in Vault:**

```bash
vault kv put secret/yo-mama-bot \
  gemini_api_key=your_key \
  discord_bot_token=your_token \
  matrix_homeserver=https://matrix.org \
  matrix_user_id=@bot:matrix.org \
  matrix_access_token=your_token
```

**4. Use in code:**

```python
from yo_mama.secrets import get_secret

# Automatically checks Vault first
api_key = get_secret('gemini_api_key')
```

---

## 💻 Using in Code

### Simple Secret Retrieval

```python
from yo_mama import get_secret, get_config

# Get any secret (checks all sources in priority order)
api_key = get_secret('GEMINI_API_KEY')

# With default fallback
token = get_secret('DISCORD_BOT_TOKEN', default='test_token')

# Using config object
config = get_config()
api_key = config.get_secret('GEMINI_API_KEY')
```

### Platform-Specific Secrets

```python
from yo_mama.secrets import get_secret

# Platform-prefixed secrets
token = get_secret(
    'bot_token',
    platform='discord',
    doppler_prefix='DISCORD'
)
# Looks for: DISCORD_BOT_TOKEN in all sources

# Matrix example
homeserver = get_secret(
    'homeserver',
    platform='matrix',
    doppler_prefix='MATRIX'
)
# Looks for: MATRIX_HOMESERVER
```

### Multiple Secrets at Once

```python
from yo_mama.secrets import get_secrets_for_platform

# Get all Discord secrets
discord_secrets = get_secrets_for_platform(
    'discord',
    ['bot_token', 'client_id', 'client_secret']
)

print(discord_secrets['bot_token'])
print(discord_secrets['client_id'])
```

### Direct Secret Manager Access

```python
from yo_mama.secrets import (
    load_secrets_from_doppler,
    load_secrets_from_aws,
    load_secrets_from_vault
)

# Load all secrets from Doppler
doppler_secrets = load_secrets_from_doppler()
print(doppler_secrets)

# Load from AWS with specific secret name
aws_secrets = load_secrets_from_aws('yo-mama-bot/prod')
print(aws_secrets)

# Load from Vault with specific path
vault_secrets = load_secrets_from_vault('secret/yo-mama-bot')
print(vault_secrets)
```

---

## 🔄 Migration Scenarios

### From .env to Doppler

```bash
# 1. Install Doppler
brew install dopplersdk/tap/doppler

# 2. Login and setup
doppler login
doppler setup

# 3. Import secrets from .env
doppler secrets upload .env

# 4. Verify
doppler secrets

# 5. Update .env to use Doppler
echo "DOPPLER_TOKEN=$(doppler configure get token --plain)" >> .env

# 6. Run
python main.py --discord
```

### From AWS to Doppler

```bash
# 1. Export from AWS
aws secretsmanager get-secret-value \
  --secret-id yo-mama-bot/prod \
  --query SecretString \
  --output text > secrets.json

# 2. Convert to env format
jq -r 'to_entries | .[] | "\(.key | ascii_upcase)=\(.value)"' secrets.json > secrets.env

# 3. Upload to Doppler
doppler secrets upload secrets.env

# 4. Clean up
rm secrets.json secrets.env

# 5. Update .env
SECRETS_MANAGER=none  # or remove line
DOPPLER_TOKEN=your_doppler_token
```

### Mixing Multiple Sources

```env
# Use Doppler for most secrets
DOPPLER_TOKEN=your_token
DOPPLER_PROJECT=yo-mama-bot
DOPPLER_CONFIG=prd

# But keep some local overrides in .env
GEMINI_MODEL=gemini-1.5-pro
LOG_LEVEL=DEBUG

# The bot will use Doppler for GEMINI_API_KEY, DISCORD_BOT_TOKEN, etc.
# But use .env for GEMINI_MODEL and LOG_LEVEL
```

---

## 🔐 Security Best Practices

### 1. Never Commit Secrets

```bash
# Ensure .env is in .gitignore
echo ".env" >> .gitignore
echo ".env.*" >> .gitignore
echo "!.env.example" >> .gitignore
```

### 2. Rotate Secrets Regularly

```bash
# Doppler makes this easy
doppler secrets set DISCORD_BOT_TOKEN="new_token"

# AWS Secrets Manager
aws secretsmanager update-secret \
  --secret-id yo-mama-bot/prod \
  --secret-string '{"discord_bot_token":"new_token"}'
```

### 3. Use Different Secrets Per Environment

```bash
# Development
DOPPLER_CONFIG=dev

# Staging
DOPPLER_CONFIG=stg

# Production
DOPPLER_CONFIG=prd
```

### 4. Limit Access

- Use IAM roles for AWS
- Use Doppler service tokens (not personal tokens) in production
- Use Vault policies for fine-grained access

### 5. Audit Access

- Enable CloudTrail for AWS Secrets Manager
- Review Doppler audit logs
- Monitor Vault access logs

---

## 🧪 Testing Secrets Configuration

Run the test script to verify your secrets setup:

```bash
python test_setup.py
```

This will check:
- ✅ All imports working
- ✅ Secrets manager connectivity
- ✅ Required secrets present
- ✅ Configuration valid

---

## 🆘 Troubleshooting

### "DOPPLER_TOKEN not found"

```bash
# Check token is set
echo $DOPPLER_TOKEN

# Get token
doppler configure get token --plain

# Set in .env
echo "DOPPLER_TOKEN=your_token" >> .env
```

### "AWS credentials not found"

```bash
# Configure AWS CLI
aws configure

# Or set in .env
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
```

### "Vault authentication failed"

```bash
# Check Vault token
vault token lookup

# Renew if needed
vault token renew

# Update .env
SECRETS_VAULT_TOKEN=new_token
```

### "Secret not found"

```python
# Check all sources
from yo_mama.secrets import (
    load_secrets_from_doppler,
    load_secrets_from_aws,
    load_secrets_from_vault
)

# Debug Doppler
doppler_secrets = load_secrets_from_doppler()
print("Doppler keys:", list(doppler_secrets.keys()))

# Debug AWS
aws_secrets = load_secrets_from_aws('yo-mama-bot/prod')
print("AWS keys:", list(aws_secrets.keys()))

# Check environment
import os
print("Env keys:", [k for k in os.environ.keys() if 'GEMINI' in k or 'DISCORD' in k])
```

---

## 📊 Comparison Table

| Feature | .env | Doppler | AWS SM | Vault |
|---------|------|---------|--------|-------|
| Setup Time | 1 min | 5 min | 10 min | 30 min |
| Cost | Free | Free tier | ~$0.40/mo | Self-hosted |
| Security | Low | High | High | High |
| Team Sharing | Hard | Easy | Easy | Easy |
| Audit Logs | No | Yes | Yes | Yes |
| Rotation | Manual | Easy | Auto | Dynamic |
| Local Dev | ✅ Perfect | ✅ Great | ⚠️ OK | ⚠️ OK |
| Production | ❌ No | ✅ Perfect | ✅ Perfect | ✅ Perfect |

---

## 🎯 Recommendations

- **Local Development**: Use `.env` file
- **Small Team**: Use Doppler
- **AWS Infrastructure**: Use AWS Secrets Manager
- **Enterprise/On-Prem**: Use HashiCorp Vault
- **CI/CD**: Use Doppler or AWS Secrets Manager

---

**Your secrets are safe! 🔒**

---

*This project is licensed under the Mozilla Public License 2.0 (MPL-2.0). See the `LICENSE` file for details.*
