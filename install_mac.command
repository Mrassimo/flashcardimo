#!/bin/bash

# Make the script exit on error
set -e

echo "🔧 Medical Flashcard Generator - Installation Script"
echo "=================================================="

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "📦 Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # Add Homebrew to PATH
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
else
    echo "✅ Homebrew already installed"
fi

# Install/Update Python with tkinter
echo "🐍 Installing/Updating Python with tkinter..."
brew install python@3.11 || brew upgrade python@3.11
brew install python-tk@3.11 || brew upgrade python-tk@3.11

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🌟 Creating virtual environment..."
    /opt/homebrew/opt/python@3.11/bin/python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
    # Remove it and create new one to ensure clean state
    rm -rf venv
    echo "🌟 Creating fresh virtual environment..."
    /opt/homebrew/opt/python@3.11/bin/python3 -m venv venv
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