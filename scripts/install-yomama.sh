#!/bin/bash
# YoMama-as-a-Service - systemd Installation Script
# Installs YoMama bot as a systemd service

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ACTUAL_USER="$USER"

echo -e "${CYAN}╔═══════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║    🎤 YoMama-as-a-Service Installer 🎤   ║${NC}"
echo -e "${CYAN}║   AI-Powered Roast Bot Installation      ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Project:${NC} $PROJECT_DIR"
echo -e "${BLUE}User:${NC} $ACTUAL_USER"
echo ""

# Check if Python 3.10+ is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: python3 not found${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓${NC} Python version: $PYTHON_VERSION"

# Check if yo_mama directory exists
if [ ! -d "$PROJECT_DIR/yo_mama" ]; then
    echo -e "${RED}ERROR: yo_mama/ directory not found${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${YELLOW}⚠${NC} .env file not found"
    echo ""
    echo "You need to create a .env file with your configuration."
    echo "See .env.example for reference."
    echo ""
    read -p "Would you like to create .env now? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f "$PROJECT_DIR/.env.example" ]; then
            cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
            echo -e "${GREEN}✓${NC} Created .env from .env.example"
            echo ""
            echo -e "${YELLOW}Please edit $PROJECT_DIR/.env with your credentials${NC}"
            echo "Then run this script again."
            exit 0
        else
            echo -e "${RED}ERROR: .env.example not found${NC}"
            exit 1
        fi
    else
        echo "Installation cancelled. Please create .env file first."
        exit 0
    fi
fi

echo -e "${GREEN}✓${NC} Configuration file found"

# Ask which bot to run
echo ""
echo -e "${BLUE}Select bot platform:${NC}"
echo "  1) Discord"
echo "  2) Matrix"
echo "  3) Both (Discord and Matrix)"
echo ""
read -p "Select [1-3] (default: 1): " -n 1 -r BOT_PLATFORM
echo ""
BOT_PLATFORM=${BOT_PLATFORM:-1}

if [[ ! $BOT_PLATFORM =~ ^[1-3]$ ]]; then
    echo -e "${RED}Invalid option${NC}"
    exit 1
fi

case $BOT_PLATFORM in
    1) SERVICE_NAME="yomama-discord"
       EXEC_CMD="--discord"
       ;;
    2) SERVICE_NAME="yomama-matrix"
       EXEC_CMD="--matrix"
       ;;
    3) SERVICE_NAME="yomama-both"
       EXEC_CMD="--discord --matrix"
       ;;
esac

echo -e "${GREEN}✓${NC} Platform selected: $SERVICE_NAME"

# Ask about deployment method
echo ""
echo -e "${BLUE}Choose deployment method:${NC}"
echo "  1) Python Virtual Environment (recommended)"
echo "  2) Docker"
echo ""
read -p "Select [1-2] (default: 1): " -n 1 -r DEPLOY_TYPE
echo ""
DEPLOY_TYPE=${DEPLOY_TYPE:-1}

if [[ ! $DEPLOY_TYPE =~ ^[1-2]$ ]]; then
    echo -e "${RED}Invalid option${NC}"
    exit 1
fi

if [ "$DEPLOY_TYPE" = "1" ]; then
    # Python venv deployment
    echo ""
    echo "Setting up Python virtual environment..."
    
    if [ ! -d "$PROJECT_DIR/venv" ]; then
        python3 -m venv "$PROJECT_DIR/venv"
        echo -e "${GREEN}✓${NC} Virtual environment created"
    else
        echo -e "${YELLOW}Virtual environment already exists${NC}"
    fi
    
    echo "Installing dependencies..."
    "$PROJECT_DIR/venv/bin/pip" install --upgrade pip
    "$PROJECT_DIR/venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
    echo -e "${GREEN}✓${NC} Dependencies installed"
    
    # Create systemd service file
    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
    
    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=YoMama-as-a-Service Bot ($SERVICE_NAME)
After=network.target

[Service]
Type=simple
User=$ACTUAL_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/main.py $EXEC_CMD
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

else
    # Docker deployment
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}ERROR: Docker not installed${NC}"
        echo "Please install Docker first: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    echo ""
    echo "Building Docker image..."
    cd "$PROJECT_DIR"
    docker build -t yomama-bot:latest .
    echo -e "${GREEN}✓${NC} Docker image built"
    
    # Create systemd service file for Docker
    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
    
    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=YoMama-as-a-Service Bot Docker ($SERVICE_NAME)
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=$ACTUAL_USER
WorkingDirectory=$PROJECT_DIR
ExecStartPre=-/usr/bin/docker stop $SERVICE_NAME
ExecStartPre=-/usr/bin/docker rm $SERVICE_NAME
ExecStart=/usr/bin/docker run --name $SERVICE_NAME --env-file $PROJECT_DIR/.env yomama-bot:latest python main.py $EXEC_CMD
ExecStop=/usr/bin/docker stop $SERVICE_NAME
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
fi

echo -e "${GREEN}✓${NC} Service file created: $SERVICE_FILE"

# Reload systemd
sudo systemctl daemon-reload
echo -e "${GREEN}✓${NC} Systemd reloaded"

# Enable and start service
sudo systemctl enable "$SERVICE_NAME"
echo -e "${GREEN}✓${NC} Service enabled"

sudo systemctl start "$SERVICE_NAME"
echo -e "${GREEN}✓${NC} Service started"

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        Installation Complete! 🎉          ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}"
echo ""
echo "Service: $SERVICE_NAME"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status $SERVICE_NAME"
echo "  sudo systemctl stop $SERVICE_NAME"
echo "  sudo systemctl start $SERVICE_NAME"
echo "  sudo systemctl restart $SERVICE_NAME"
echo "  sudo journalctl -u $SERVICE_NAME -f"
echo ""
