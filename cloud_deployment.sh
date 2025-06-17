#!/bin/bash

# Update & install dependencies
sudo apt update && sudo apt install -y docker.io git

# Clone your repo
git clone https://github.com/vjaypunyapu/legal_ai.git
cd legal_ai

# Start Ollama and pull Mistral model
docker run -d --name ollama -p 11434:11434 -v ollama:/root/.ollama ollama/ollama
sleep 15
docker exec ollama ollama run mistral

# Start your app Docker container (assuming Dockerfile is ready)
docker build -t legal-ai .
docker run -d -p 8000:8000 --name legalai legal-ai
