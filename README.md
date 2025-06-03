# 🧑‍⚖️ Private Legal AI Demo (LLaMA 3 70B)

This project is a fully self-hosted Legal AI assistant using **LLaMA 3 70B**, Streamlit UI, ChromaDB vector search, JWT authentication, OCR for scanned PDFs, and async processing for long docs.

---

## 🚀 Features
- 📄 Upload legal documents (PDFs)
- 🔍 Ask questions using natural language
- 🧠 Powered by LLaMA 3 70B using vLLM
- 🔒 JWT-secured access
- 🧾 OCR for scanned documents
- 🔁 Background processing
- 🐳 Dockerized setup for easy deployment

---

## 🛠️ Setup Instructions

### 1. 🧠 Get LLaMA 3 70B Weights
- Apply at [Meta AI](https://ai.meta.com/resources/models-and-libraries/llama-3/)
- Clone from Hugging Face:
  ```bash
  huggingface-cli login
  huggingface-cli repo clone meta-llama/Meta-Llama-3-70B
  ```

### 2. 🧱 Deploy on CoreWeave
- Spin up a VM with **2× A100 80GB GPUs**
- Clone this repo, then run:
  ```bash
  chmod +x start.sh
  ./start.sh
  ```

### 3. 🔑 Login
- Go to [http://<YOUR-IP>:8501](http://<YOUR-IP>:8501)
- Login: `admin` / `demo123`
- Copy the JWT token to access the main app

---

## 🧪 Sample Prompts

**For Contracts:**
- What are the termination clauses?
- Are there any non-compete or liability risks?

**For Case Law:**
- Summarize the legal reasoning
- What precedent does this case set?

**Compliance Checks:**
- Does this meet GDPR retention rules?
- Are there HIPAA red flags?

---

## 📁 Folder Structure

- `frontend/`: Streamlit UI + Login
- `backend/`: LLM API + OCR + async tasks
- `docs/`: Upload folder for PDFs
- `devops/`: Docker + Compose files

---

## 📬 Questions?
Contact: `yourteam@example.com`
