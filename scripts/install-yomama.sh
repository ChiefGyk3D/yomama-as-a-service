#!/bin/bash
# SolarStorm Scout - systemd Installation Script
# Installs SolarStorm Scout as a systemd service with timer

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
ACTUAL_USER_UID=$(id -u)
ACTUAL_USER_GID=$(id -g)

echo -e "${CYAN}╔════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     🌞 SolarStorm Scout Installer 🌞      ║${NC}"
echo -e "${CYAN}║   Space Weather Social Media Bot          ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Project:${NC} $PROJECT_DIR"
echo -e "${BLUE}User:${NC} $ACTUAL_USER"
echo ""

# Check if Python 3.8+ is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: python3 not found${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓${NC} Python version: $PYTHON_VERSION"

# Check if solarstorm_scout directory exists
if [ ! -d "$PROJECT_DIR/solarstorm_scout" ]; then
    echo -e "${RED}ERROR: solarstorm_scout/ directory not found${NC}"
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

# Ask about posting interval
echo ""
echo -e "${BLUE}Posting Interval Configuration:${NC}"
echo "How often should SolarStorm Scout post updates?"
echo ""
read -p "Enter interval in hours (default: 1.5): " INTERVAL_HOURS
INTERVAL_HOURS=${INTERVAL_HOURS:-1.5}

# Validate interval
if ! [[ "$INTERVAL_HOURS" =~ ^[0-9]+\.?[0-9]*$ ]]; then
    echo -e "${RED}ERROR: Invalid interval. Must be a number.${NC}"
    exit 1
fi

# Calculate interval in seconds for systemd
INTERVAL_SECONDS=$(python3 -c "print(int($INTERVAL_HOURS * 3600))")

# Ask about timer type
echo ""
echo -e "${BLUE}Timer Type:${NC}"
echo "  1) Relative timing (runs X hours after previous completion)"
echo "     Example: If 1.5h and bot takes 2min, posts at 00:02, 01:32, 03:02..."
echo ""
echo "  2) Fixed schedule (runs at exact times)"
echo "     Example: If 1.5h, posts at 00:00, 01:30, 03:00, 04:30..."
echo ""
read -p "Select [1-2] (default: 2): " -n 1 -r TIMER_TYPE
echo ""
TIMER_TYPE=${TIMER_TYPE:-2}

if [[ ! $TIMER_TYPE =~ ^[1-2]$ ]]; then
    echo -e "${RED}Invalid option${NC}"
    exit 1
fi

if [ "$TIMER_TYPE" = "2" ]; then
    echo -e "${GREEN}✓${NC} Fixed schedule: Posts every ${INTERVAL_HOURS} hours at exact intervals"
else
    echo -e "${GREEN}✓${NC} Relative timing: Posts ${INTERVAL_HOURS} hours after previous run"
fi

# Check if service already exists
if sudo systemctl list-units --full --all | grep -q "solarstorm-scout.service"; then
    echo ""
    echo -e "${YELLOW}Service already exists${NC}"
    
    if sudo systemctl is-active --quiet solarstorm-scout.timer; then
        echo -e "${YELLOW}Timer is currently running${NC}"
        read -p "Stop timer before reinstalling? (Y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            echo "Stopping solarstorm-scout timer..."
            sudo systemctl stop solarstorm-scout.timer
            sudo systemctl disable solarstorm-scout.timer
            echo -e "${GREEN}✓${NC} Timer stopped"
        fi
    fi
    
    # Check for .last_run file (anti-spam tracking)
    if [ -f "$PROJECT_DIR/logs/.last_run" ]; then
        echo ""
        read -p "Reset rate limit timer (.last_run file)? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm "$PROJECT_DIR/logs/.last_run"
            echo -e "${GREEN}✓${NC} Rate limit timer reset"
        fi
    fi
fi

# Ask about deployment method
echo ""
echo -e "${BLUE}Choose deployment method:${NC}"
echo "  1) Python"
echo "  2) Docker"
echo ""
read -p "Select [1-2] (default: 1): " -n 1 -r DEPLOY_TYPE
echo ""
DEPLOY_TYPE=${DEPLOY_TYPE:-1}

if [[ ! $DEPLOY_TYPE =~ ^[1-2]$ ]]; then
    echo -e "${RED}Invalid option${NC}"
    exit 1
fi

# Sub-menu based on deployment type
if [ "$DEPLOY_TYPE" = "1" ]; then
    echo ""
    echo -e "${BLUE}Python deployment method:${NC}"
    echo "  1) Virtual Environment (recommended)"
    echo "  2) System Python"
    echo ""
    read -p "Select [1-2] (default: 1): " -n 1 -r PYTHON_MODE
    echo ""
    PYTHON_MODE=${PYTHON_MODE:-1}
    
    if [[ ! $PYTHON_MODE =~ ^[1-2]$ ]]; then
        echo -e "${RED}Invalid option${NC}"
        exit 1
    fi
    
    DEPLOYMENT_MODE=$PYTHON_MODE
else
    echo ""
    echo -e "${BLUE}Docker deployment method:${NC}"
    echo "  1) Pull from GHCR (recommended)"
    echo "  2) Build locally"
    echo ""
    read -p "Select [1-2] (default: 1): " -n 1 -r DOCKER_MODE
    echo ""
    DOCKER_MODE=${DOCKER_MODE:-1}
    
    if [[ ! $DOCKER_MODE =~ ^[1-2]$ ]]; then
        echo -e "${RED}Invalid option${NC}"
        exit 1
    fi
    
    # Map to original numbering: 3=GHCR, 4=local build
    DEPLOYMENT_MODE=$((DOCKER_MODE + 2))
fi

# Setup environment based on deployment mode
if [ "$DEPLOYMENT_MODE" = "3" ] || [ "$DEPLOYMENT_MODE" = "4" ]; then
    # Docker deployment
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}ERROR: Docker not installed${NC}"
        echo "Please install Docker first: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    echo -e "${GREEN}✓${NC} Docker found"
    
    if [ "$DEPLOYMENT_MODE" = "3" ]; then
        # Pull from GHCR
        echo ""
        echo "Pulling Docker image from GHCR..."
        DOCKER_IMAGE="ghcr.io/chiefgyk3d/solarstorm_scout:latest"
        
        if docker pull "$DOCKER_IMAGE"; then
            echo -e "${GREEN}✓${NC} Image pulled successfully"
        else
            echo -e "${RED}✗${NC} Failed to pull image from GHCR"
            echo ""
            read -p "Would you like to build locally instead? (Y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                DEPLOYMENT_MODE="4"
            else
                exit 1
            fi
        fi
    fi
    
    if [ "$DEPLOYMENT_MODE" = "4" ]; then
        # Build Docker image locally
        echo ""
        echo "Building Docker image locally..."
        
        if ! docker build -t solarstorm-scout:local "$PROJECT_DIR"; then
            echo -e "${RED}✗${NC} Docker build failed"
            exit 1
        fi
        
        DOCKER_IMAGE="solarstorm-scout:local"
        echo -e "${GREEN}✓${NC} Image built successfully"
    fi
    
    # Docker-specific service configuration
    # --rm flag automatically removes container when it exits
    EXEC_START="/usr/bin/docker run --rm --name solarstorm-scout --env-file=$PROJECT_DIR/.env -v $PROJECT_DIR/logs:/app/logs $DOCKER_IMAGE"
    
elif [ "$DEPLOYMENT_MODE" = "1" ]; then
    echo ""
    echo "Setting up Python virtual environment..."
    
    VENV_DIR="$PROJECT_DIR/venv"
    
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
        echo -e "${GREEN}✓${NC} Virtual environment created"
    else
        echo -e "${GREEN}✓${NC} Virtual environment exists"
    fi
    
    # Activate and install dependencies
    source "$VENV_DIR/bin/activate"
    
    echo "Installing dependencies..."
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r "$PROJECT_DIR/requirements.txt"
    echo -e "${GREEN}✓${NC} Dependencies installed"
    
    PYTHON_BIN="$VENV_DIR/bin/python3"
    PYTHON_PATH="$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"
else
    echo ""
    echo "Installing dependencies to system Python..."
    pip3 install --user -r "$PROJECT_DIR/requirements.txt"
    echo -e "${GREEN}✓${NC} Dependencies installed"
    
    PYTHON_BIN="python3"
    PYTHON_PATH="/usr/local/bin:/usr/bin:/bin"
    EXEC_START="$PYTHON_BIN -m solarstorm_scout.main"
fi

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"
echo -e "${GREEN}✓${NC} Logs directory created"

# Generate service file
echo ""
echo "Generating systemd service files..."

SERVICE_FILE="/etc/systemd/system/solarstorm-scout.service"
TIMER_FILE="/etc/systemd/system/solarstorm-scout.timer"

# Remove old service files to ensure clean installation
if [ -f "$SERVICE_FILE" ]; then
    sudo rm "$SERVICE_FILE"
    echo -e "${GREEN}✓${NC} Removed old service file"
fi

if [ -f "$TIMER_FILE" ]; then
    sudo rm "$TIMER_FILE"
    echo -e "${GREEN}✓${NC} Removed old timer file"
fi

# Create service file based on deployment mode
if [ "$DEPLOYMENT_MODE" = "3" ] || [ "$DEPLOYMENT_MODE" = "4" ]; then
    # Docker service file
    cat << EOF | sudo tee "$SERVICE_FILE" > /dev/null
[Unit]
Description=SolarStorm Scout - Space Weather Bot (Docker)
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
User=$ACTUAL_USER
WorkingDirectory=$PROJECT_DIR
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$EXEC_START
# No ExecStop needed - --rm flag auto-removes container when it exits
StandardOutput=append:$PROJECT_DIR/logs/solarstorm.log
StandardError=append:$PROJECT_DIR/logs/solarstorm.error.log

[Install]
WantedBy=multi-user.target
EOF
else
    # Python service file from template
    sed -e "s|%USER%|$ACTUAL_USER|g" \
        -e "s|%GROUP%|$ACTUAL_USER|g" \
        -e "s|%PROJECT_DIR%|$PROJECT_DIR|g" \
        -e "s|%PYTHON_BIN%|$PYTHON_BIN|g" \
        -e "s|%PYTHON_PATH%|$PYTHON_PATH|g" \
        -e "s|%ENV_FILE%|$PROJECT_DIR/.env|g" \
        "$PROJECT_DIR/systemd/solarstorm-scout.service.template" | sudo tee "$SERVICE_FILE" > /dev/null
fi

echo -e "${GREEN}✓${NC} Service file created"

# Create timer file based on timer type
if [ "$TIMER_TYPE" = "2" ]; then
    # Fixed schedule with OnCalendar
    # Generate calendar entries for the interval
    CALENDAR_ENTRIES=$(python3 -c "
interval = $INTERVAL_HOURS
hours_per_day = 24
slots = int(hours_per_day / interval)
times = []
for i in range(slots):
    hour = int(i * interval)
    minute = int((i * interval - hour) * 60)
    times.append(f'{hour:02d}:{minute:02d}:00')
print('\n'.join([f'OnCalendar=*-*-* {time}' for time in times]))
")
    
    cat << EOF | sudo tee "$TIMER_FILE" > /dev/null
[Unit]
Description=SolarStorm Scout Timer - Posts space weather updates every $INTERVAL_HOURS hours
Documentation=https://github.com/chiefgyk3d/solarstorm-scout
Requires=solarstorm-scout.service

[Timer]
# Fixed schedule - runs at exact times
# Note: Will NOT run on boot - only at scheduled times or manual trigger
$CALENDAR_ENTRIES

# Allow some timing jitter to reduce load spikes
AccuracySec=1min

[Install]
WantedBy=timers.target
EOF
else
    # Relative timing with OnUnitActiveSec (original behavior)
    sed -e "s|%INTERVAL_HOURS%|$INTERVAL_HOURS|g" \
        -e "s|%INTERVAL_SECONDS%|$INTERVAL_SECONDS|g" \
        "$PROJECT_DIR/systemd/solarstorm-scout.timer.template" | sudo tee "$TIMER_FILE" > /dev/null
fi

echo -e "${GREEN}✓${NC} Timer file created"

# Reload systemd
sudo systemctl daemon-reload
echo -e "${GREEN}✓${NC} Systemd reloaded"

# Enable and start timer
echo ""
echo "Enabling and starting timer..."
sudo systemctl enable solarstorm-scout.timer
sudo systemctl start solarstorm-scout.timer

if sudo systemctl is-active --quiet solarstorm-scout.timer; then
    echo -e "${GREEN}✓${NC} Timer started successfully"
else
    echo -e "${RED}✗${NC} Timer failed to start"
    exit 1
fi

# Test run (optional)
echo ""
read -p "Would you like to run a test post now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Check if rate limiter exists
    if [ -f "$PROJECT_DIR/logs/.last_run" ]; then
        echo ""
        echo -e "${YELLOW}Note: Rate limiter active (30-minute minimum between posts)${NC}"
        read -p "Remove rate limit to allow test? (Y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            rm "$PROJECT_DIR/logs/.last_run"
            echo -e "${GREEN}✓${NC} Rate limiter removed"
        fi
    fi
    
    echo ""
    echo "Running test post..."
    sudo systemctl start solarstorm-scout.service
    
    echo ""
    echo "Waiting for service to complete..."
    sleep 3
    
    # Optionally show status
    read -p "Show service status? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo systemctl status solarstorm-scout.service --no-pager -l
    fi
fi

# Show information
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║         Installation Complete! ✓           ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Posting Interval:${NC} Every $INTERVAL_HOURS hours"
echo -e "${BLUE}Next Post:${NC} $(systemctl status solarstorm-scout.timer | grep Trigger | awk '{print $3, $4, $5}')"
echo ""
echo -e "${GREEN}Useful Commands:${NC}"
echo "  View timer status:    sudo systemctl status solarstorm-scout.timer"
echo "  View service logs:    sudo journalctl -u solarstorm-scout.service -f"
echo "  Run manual post:      sudo systemctl start solarstorm-scout.service"
echo "  Stop timer:           sudo systemctl stop solarstorm-scout.timer"
echo "  Restart timer:        sudo systemctl restart solarstorm-scout.timer"
echo "  Disable timer:        sudo systemctl disable solarstorm-scout.timer"
echo ""
echo -e "${BLUE}Configuration:${NC} $PROJECT_DIR/.env"
echo -e "${BLUE}Logs:${NC} $PROJECT_DIR/logs/"
echo ""
echo -e "${YELLOW}Note:${NC} Edit .env to change credentials or settings"
echo "      Then restart timer: sudo systemctl restart solarstorm-scout.timer"
echo ""
