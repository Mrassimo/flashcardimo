#!/bin/bash

# Make the script exit on error
set -e

echo "🔧 Medical Flashcard Generator - Installation Script"
echo "=================================================="

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "📦 Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "✅ Homebrew already installed"
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "🐍 Installing Python..."
    brew install python@3.11
else
    echo "✅ Python already installed"
fi

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🌟 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade pip
echo "📦 Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "🔑 Creating .env file..."
    cp .env.example .env
    echo "⚠️ Please edit .env file with your API keys"
    open -a TextEdit .env
fi

echo ""
echo "✨ Installation complete! ✨"
echo ""
echo "To start the application:"
echo "1. Make sure you've added your API keys to the .env file"
echo "2. Double-click 'start_mac.command' to launch the application"
echo ""
echo "Press any key to exit..."
read -n 1 -s 