from datetime import datetime
import os
import shutil
import traceback

import fitz  # PyMuPDF
import uvicorn
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Query, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import Column, String, Boolean, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from llama_index.core import VectorStoreIndex, Settings, SimpleDirectoryReader, load_index_from_storage, StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.response_synthesizers import CompactAndRefine

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======= DATABASE SETUP =======
DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    email = Column(String, primary_key=True, index=True)
    password = Column(String)
    role = Column(String)
    activated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

Base.metadata.create_all(bind=engine)

# ======= AUTH SETUP =======
SECRET_KEY = "secret"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# ======= UTIL FUNCTIONS =======
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.email == username).first()
    if user and verify_password(password, user.password):
        return user
    return None

def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Security(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        user = db.query(User).filter(User.email == username).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

# ======= ROUTES =======
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not user.activated:
        raise HTTPException(status_code=403, detail="User not activated")
    user.last_login = datetime.utcnow()
    db.commit()
    token = create_access_token({"sub": user.email, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/ask")
def ask_question(file: UploadFile = File(...), question: str = Form(...), user: User = Depends(get_current_user)):
    try:
        temp_file_path = "temp.pdf"
        with open(temp_file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        doc = fitz.open(temp_file_path)
        with open("temp.txt", "w", encoding="utf-8") as f:
            for page in doc:
                f.write(page.get_text())
        doc.close()

        documents = SimpleDirectoryReader(input_files=["temp.txt"]).load_data()
        parser = SentenceSplitter(chunk_size=1024, chunk_overlap=100)
        nodes = parser.get_nodes_from_documents(documents)

        Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2", cache_folder=".cache")
        Settings.llm = Ollama(model="mistral", request_timeout=120.0)

        index = VectorStoreIndex(nodes)
        query_engine = index.as_query_engine(
            response_mode="compact_and_refine",
            response_synthesizer=CompactAndRefine()
        )
        response = query_engine.query(question)

        return {"answer": response.response}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF/Q&A error: {str(e)}")
    finally:
        file.file.close()

@app.get("/admin/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@app.post("/admin/users")
def add_user(username: str = Query(...), password: str = Query(...), role: str = Query(...), db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    user = User(email=username, password=get_password_hash(password), role=role, activated=False)
    db.add(user)
    db.commit()
    return {"detail": "User added"}

@app.delete("/admin/users")
def delete_user(username: str = Query(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.email == "admin@example.com":
        raise HTTPException(status_code=403, detail="Cannot delete default admin")
    db.delete(user)
    db.commit()
    return {"detail": "User deleted"}

@app.post("/send-activation")
def send_activation(email: str = Query(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    activation_link = f"http://localhost:8501/activate?email={email}"
    print(f"Sending activation link to {email}: {activation_link}")
    return {"activation_link": activation_link, "detail": "Email sent"}

@app.post("/activate")
def activate_user(email: str = Query(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.activated = True
        db.commit()
        return {"detail": "User activated"}
    else:
        raise HTTPException(status_code=404, detail="User not found")

@app.post("/admin/force-activate")
def force_activate_user(username: str = Query(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.activated = True
    db.commit()
    return {"detail": "User manually activated by admin"}
