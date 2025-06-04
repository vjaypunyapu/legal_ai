# 🧠 Legal AI Assistant

A private legal document Q&A assistant built with **Streamlit**, **FastAPI**, and **Ollama** using open-source LLMs like Mistral 7B.

---

## 🚀 Features

- 🔐 Login-protected UI
- 📄 Upload legal PDF documents
- ❓ Ask questions about the content
- 🤖 Powered by local LLM (via Ollama)
- 🧠 Uses PDF context for accurate answers

---

## 🛠️ Local Installation Guide

### 1. Clone the Repository

```bash
git clone https://github.com/vjaypunyapu/legal_ai.git
cd legal_ai
```

### 2. Set Up Python Virtual Environment

```bash
python -m venv .venv
# On Windows
.\.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

If you don't have a `requirements.txt`, install manually:

```bash
pip install fastapi uvicorn streamlit python-jose pdfplumber requests
```

---

### 4. Install and Run Ollama (for LLM)

- Download from: https://ollama.com/download
- Then in terminal:

```bash
ollama pull mistral
ollama run mistral
```

---

## 🧪 Running the App

### Backend (FastAPI)

```bash
uvicorn backend.llm_server:app --reload
```

### Frontend (Streamlit)

```bash
streamlit run frontend/app.py
```

Then visit: [http://localhost:8501](http://localhost:8501)

---

## 👤 Login Credentials

- **Username:** `test`
- **Password:** `test123`

---

## 📝 Example PDF to Test

You can upload a legal PDF like an NDA, lease, or contract and ask:

- "What is the duration of the agreement?"
- "Is third-party disclosure allowed?"
- "What happens in case of breach?"

---

## 💬 Contact

Built by [TechJ]. Questions? Reach out to [vjaypunyapu@yahoo.com]
