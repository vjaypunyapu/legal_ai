@echo off
echo 🚀 Starting Legal AI App (Windows Setup)...

REM Change directory to the project folder
cd /d %~dp0

REM Check if Python is installed
python --version
IF %ERRORLEVEL% NEQ 0 (
    echo ❌ Python is not installed. Please install Python 3.10+ and re-run this script.
    pause
    exit /b
)

REM Create virtual environment
python -m venv .venv
call .venv\Scripts\activate

REM Install requirements
echo 📦 Installing Python packages...
pip install --upgrade pip
pip install -r requirements.txt

REM Start Ollama model
echo 🧠 Starting Mistral model with Ollama...
start cmd /k "ollama run mistral"

REM Launch Streamlit UI
echo 🚀 Launching Streamlit app...
streamlit run frontend\app.py
