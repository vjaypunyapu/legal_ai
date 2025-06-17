# Dockerfile to run full legal_ai app with frontend (Streamlit), backend (FastAPI), and Ollama (Mistral)

# Use base image with Python
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Set up app directories
WORKDIR /app
COPY . /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    OLLAMA_HOST=http://localhost:11434

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Expose ports for FastAPI (8000) and Streamlit (8501)
EXPOSE 8000 8501

# Start both services using a process manager
CMD ["bash", "-c", "ollama serve & sleep 15 && uvicorn backend.llm_server:app --host 0.0.0.0 --port 8000 & streamlit run app.py --server.port 8501 --server.address 0.0.0.0"]
