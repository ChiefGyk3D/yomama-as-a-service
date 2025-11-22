#!/bin/bash
# SPDX-License-Identifier: MPL-2.0
# This file is part of YoMama-as-a-Service. See LICENSE for details.

# Quick run script for Yo Mama Bot

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ No .env file found. Run ./setup.sh first."
    exit 1
fi

# Run the bot with any provided arguments
python main.py "$@"
#!/bin/bash
# Quick run script for Yo Mama Bot

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ No .env file found. Run ./setup.sh first."
    exit 1
fi

# Run the bot with any provided arguments
python main.py "$@"
