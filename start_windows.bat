@echo off

:: Get the directory where the script is located
cd /d "%~dp0"

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Start the application
python gui.py 