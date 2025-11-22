#!/bin/bash
# YoMama-as-a-Service - systemd Uninstallation Script

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔═══════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   🎤 YoMama-as-a-Service Uninstaller 🎤  ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════╝${NC}"
echo ""

# Find all YoMama service files in /etc/systemd/system/
SERVICES=$(sudo find /etc/systemd/system/ -name "yomama-*.service" -type f 2>/dev/null | xargs -n1 basename 2>/dev/null || true)

# Check for Docker containers
DOCKER_CONTAINERS=$(docker ps -a --filter "name=yomama" --format "{{.Names}}" 2>/dev/null || true)

# Check if anything is installed
if [ -z "$SERVICES" ] && [ -z "$DOCKER_CONTAINERS" ]; then
    echo -e "${YELLOW}No YoMama services or Docker containers found${NC}"
    echo "Nothing to uninstall."
    exit 0
fi

# Show what was found
if [ -n "$SERVICES" ]; then
    echo "Found the following YoMama systemd services:"
    echo "$SERVICES"
    echo ""
fi

if [ -n "$DOCKER_CONTAINERS" ]; then
    echo "Found the following YoMama Docker containers:"
    echo "$DOCKER_CONTAINERS"
    echo ""
fi

echo -e "${YELLOW}Configuration files (.env) will be preserved.${NC}"
echo ""
read -p "Continue with uninstall? (y/N) " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

# Stop and disable systemd services
if [ -n "$SERVICES" ]; then
    echo ""
    echo "Removing systemd services..."
    
    for SERVICE in $SERVICES; do
        echo ""
        echo "Processing $SERVICE..."
        
        if sudo systemctl is-active --quiet "$SERVICE"; then
            echo "Stopping $SERVICE..."
            sudo systemctl stop "$SERVICE"
            echo -e "${GREEN}✓${NC} Stopped"
        fi
        
        if sudo systemctl is-enabled --quiet "$SERVICE" 2>/dev/null; then
            echo "Disabling $SERVICE..."
            sudo systemctl disable "$SERVICE"
            echo -e "${GREEN}✓${NC} Disabled"
        fi
        
        # Remove service file
        SERVICE_FILE="/etc/systemd/system/$SERVICE"
        if [ -f "$SERVICE_FILE" ]; then
            sudo rm "$SERVICE_FILE"
            echo -e "${GREEN}✓${NC} Service file removed"
        fi
    done

    # Reload systemd
    sudo systemctl daemon-reload
    echo -e "${GREEN}✓${NC} Systemd reloaded"
    echo ""
    echo -e "${GREEN}Systemd services uninstalled!${NC}"
fi

# Docker cleanup
if command -v docker &> /dev/null; then
    echo ""
    echo -e "${BLUE}Docker Cleanup:${NC}"
    
    # Check for Docker images
    YOMAMA_IMAGE=$(docker images -q yomama-bot:latest 2>/dev/null)
    GHCR_IMAGE=$(docker images -q ghcr.io/chiefgyk3d/yomama-as-a-service 2>/dev/null)
    
    # Check for ALL containers with "yomama" in the name (not just "yomama-")
    RUNNING_CONTAINERS=$(docker ps -a --filter "name=yomama" --format "{{.Names}}" 2>/dev/null || true)
    
    if [ -n "$RUNNING_CONTAINERS" ]; then
        echo "Found YoMama containers:"
        echo "$RUNNING_CONTAINERS"
        echo ""
        read -p "Remove YoMama Docker containers? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            for CONTAINER in $RUNNING_CONTAINERS; do
                docker stop "$CONTAINER" 2>/dev/null || true
                docker rm "$CONTAINER" 2>/dev/null || true
                echo -e "${GREEN}✓${NC} Removed container: $CONTAINER"
            done
        fi
    fi
    
    if [ -n "$YOMAMA_IMAGE" ] || [ -n "$GHCR_IMAGE" ]; then
        echo ""
        read -p "Remove YoMama Docker images? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if [ -n "$YOMAMA_IMAGE" ]; then
                docker rmi yomama-bot:latest 2>/dev/null || true
                echo -e "${GREEN}✓${NC} Local image removed"
            fi
            if [ -n "$GHCR_IMAGE" ]; then
                docker rmi ghcr.io/chiefgyk3d/yomama-as-a-service:latest 2>/dev/null || true
                echo -e "${GREEN}✓${NC} GHCR image removed"
            fi
        else
            echo "Docker images preserved"
        fi
    fi
fi

# Ask about venv cleanup
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [ -d "$PROJECT_DIR/venv" ]; then
    echo ""
    read -p "Remove Python virtual environment? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$PROJECT_DIR/venv"
        echo -e "${GREEN}✓${NC} Virtual environment removed"
    else
        echo "Virtual environment preserved"
    fi
fi

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        Uninstall Complete! 👋             ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}"
echo ""
echo "Your .env file and project files have been preserved."
echo ""
