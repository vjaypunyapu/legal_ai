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

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    python -m venv .venv
)

REM Activate the virtual environment
call .venv\Scripts\activate

REM Install required packages
echo 📦 Installing Python packages...
pip install --upgrade pip
pip install -r requirements.txt

REM Start Ollama model in a new terminal
echo 🧠 Starting Mistral model with Ollama...
start cmd /k "ollama run mistral"

REM Start FastAPI backend in a new terminal with log file
echo ⚙️ Starting FastAPI backend...
start cmd /k "cd backend && uvicorn llm_server:app --host 0.0.0.0 --port 8000 > ../backend_log.txt 2>&1"

REM Launch Streamlit frontend
echo 🖼️ Launching Streamlit frontend...
streamlit run frontend\app.py

echo ✅ All systems started. Check http://localhost:8501
