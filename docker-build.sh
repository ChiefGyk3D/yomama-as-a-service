#!/bin/bash
# SPDX-License-Identifier: MPL-2.0
# This file is part of YoMama-as-a-Service. See LICENSE for details.

set -e

echo "🐳 YoMama-as-a-Service - Docker Build Script"
echo "=============================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "   ✓ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your configuration"
    echo ""
    read -p "Do you want to edit .env now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} .env
    fi
fi

echo ""
echo "🔨 Building Docker image..."
echo "This will update all OS packages during build..."
echo ""

# Build the Docker image with no cache to ensure fresh updates
docker build --no-cache --pull -t yomama-as-a-service:latest .

echo ""
echo "✅ Docker image built successfully!"
echo ""
echo "Next steps:"
echo "1. Make sure your .env file is configured"
echo "2. Run Discord bot: docker-compose up -d yomama-discord"
echo "3. Run Matrix bot: docker-compose up -d yomama-matrix"
echo "4. Run both bots: docker-compose up -d"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f yomama-discord"
echo "  docker-compose logs -f yomama-matrix"
echo ""
echo "To stop:"
echo "  docker-compose down"
echo ""
