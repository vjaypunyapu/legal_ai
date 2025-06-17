# Bash startup script for Linux/Unix
#!/bin/bash

echo "▶️ Setting up Python virtual environment with Python 3.11.6..."

# Step 1: Create venv
python -m venv .venv

# Step 2: Activate venv
source .venv/Scripts/activate  # Use .venv\Scripts\activate.bat on Windows cmd

# Step 3: Upgrade pip and install dependencies
echo "📦 Installing requirements..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# Step 4: Run backend
echo "🚀 Starting FastAPI backend..."
nohup uvicorn backend.llm_server:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &

# Step 5: Run Streamlit frontend
echo "🎬 Starting Streamlit frontend..."
nohup streamlit run app.py > frontend.log 2>&1 &

echo "✅ App is running. Backend: http://localhost:8000 | Frontend: http://localhost:8501"
