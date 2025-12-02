@echo off
REM AetherSignal Installation Script for Windows

echo 🚀 Installing AetherSignal...
echo.

REM Check Python
python --version
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.11+
    exit /b 1
)

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

REM Create directories
echo 📁 Creating directories...
if not exist logs mkdir logs
if not exist storage mkdir storage
if not exist data\cache mkdir data\cache
if not exist data\processed mkdir data\processed
if not exist config mkdir config
if not exist docs mkdir docs

REM Copy .env template
if not exist .env (
    echo 📋 Creating .env from template...
    if exist .env.example (
        copy .env.example .env
        echo ⚠️  Please edit .env and add your API keys (optional)
    ) else (
        echo STREAMLIT_SERVER_PORT=8501 > .env
        echo LOG_LEVEL=INFO >> .env
        echo DEV_MODE=false >> .env
    )
)

echo.
echo ✨ Installation complete!
echo.
echo To run AetherSignal:
echo   1. Activate virtual environment: venv\Scripts\activate
echo   2. Run: streamlit run app.py
echo.

pause

