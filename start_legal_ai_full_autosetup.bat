@echo off
echo 🔧 Setting up Legal AI Environment...

REM Change to script directory
cd /d %~dp0

REM Step 1: Activate virtual environment
echo 🔁 Activating virtual environment...
call .venv\Scripts\activate

REM Step 2: Install dependencies
echo 📦 Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM Step 3: Start backend server (FastAPI)
echo 🚀 Starting FastAPI backend on port 8000...
start cmd /k "cd backend && uvicorn llm_server:app --reload --port 8000"

REM Step 4: Start Streamlit frontend
echo 🖼️ Starting Streamlit frontend on port 8501...
streamlit run frontend\app.py
