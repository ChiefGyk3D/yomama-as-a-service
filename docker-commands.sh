#!/bin/bash
# SPDX-License-Identifier: MPL-2.0
# This file is part of YoMama-as-a-Service. See LICENSE for details.

# Quick Docker commands reference
# Run this script with: source docker-commands.sh (to enable aliases)

# Aliases for common Docker operations
alias yomama-build='./docker-build.sh'
alias yomama-up='docker-compose up -d'
alias yomama-down='docker-compose down'
alias yomama-logs='docker-compose logs -f'
alias yomama-restart='docker-compose restart'
alias yomama-ps='docker-compose ps'
alias yomama-stats='docker stats'

# Discord-specific
alias yomama-discord-up='docker-compose up -d yomama-discord'
alias yomama-discord-logs='docker-compose logs -f yomama-discord'
alias yomama-discord-restart='docker-compose restart yomama-discord'

# Matrix-specific
alias yomama-matrix-up='docker-compose up -d yomama-matrix'
alias yomama-matrix-logs='docker-compose logs -f yomama-matrix'
alias yomama-matrix-restart='docker-compose restart yomama-matrix'

echo "🎤 YoMama Docker Commands Loaded!"
echo ""
echo "Available commands:"
echo "  yomama-build          - Build Docker image"
echo "  yomama-up             - Start all bots"
echo "  yomama-down           - Stop all bots"
echo "  yomama-logs           - View logs (all)"
echo "  yomama-restart        - Restart all bots"
echo "  yomama-ps             - Show container status"
echo "  yomama-stats          - Show resource usage"
echo ""
echo "Discord bot:"
echo "  yomama-discord-up     - Start Discord bot"
echo "  yomama-discord-logs   - View Discord logs"
echo "  yomama-discord-restart - Restart Discord bot"
echo ""
echo "Matrix bot:"
echo "  yomama-matrix-up      - Start Matrix bot"
echo "  yomama-matrix-logs    - View Matrix logs"
echo "  yomama-matrix-restart - Restart Matrix bot"
echo ""
