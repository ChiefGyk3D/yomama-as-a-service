#!/bin/bash
# SPDX-License-Identifier: MPL-2.0
# This file is part of YoMama-as-a-Service. See LICENSE for details.

# Run Matrix bot

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

echo "🤖 Starting Matrix bot..."
echo "Press Ctrl+C to stop"
echo ""

python main.py --matrix#!/bin/bash
# Run Matrix bot

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

echo "🤖 Starting Matrix bot..."
echo "Press Ctrl+C to stop"
echo ""

python main.py --matrix
