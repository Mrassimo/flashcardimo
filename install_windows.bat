@echo off
echo 🔧 Medical Flashcard Generator - Installation Script
echo ==================================================

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo 🐍 Python not found. Downloading Python 3.11...
    curl -o python_installer.exe https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe
    echo 🔄 Installing Python...
    python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python_installer.exe
) else (
    echo ✅ Python already installed
)

:: Get the directory where the script is located
cd /d "%~dp0"

:: Create virtual environment if it doesn't exist
if not exist venv (
    echo 🌟 Creating virtual environment...
    python -m venv venv
) else (
    echo ✅ Virtual environment already exists
)

:: Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

:: Install/upgrade pip
echo 📦 Upgrading pip...
python -m pip install --upgrade pip

:: Install requirements
echo 📚 Installing dependencies...
pip install -r requirements.txt

:: Create .env file if it doesn't exist
if not exist .env (
    echo 🔑 Creating .env file...
    copy .env.example .env
    echo ⚠️ Please edit .env file with your API keys
    notepad .env
)

:: Start the application and close the command prompt when done
echo "🚀 Starting the application..."
python gui.py
exit

echo.
echo ✨ Installation complete! ✨
echo.
echo To start the application:
echo 1. Make sure you've added your API keys to the .env file
echo 2. Double-click 'start_windows.bat' to launch the application
echo.
pause 