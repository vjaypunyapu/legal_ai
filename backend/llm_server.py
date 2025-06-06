from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Query, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import Column, String, Boolean, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import uvicorn
import os
import shutil
from datetime import datetime

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

from fastapi import UploadFile, File, Form, HTTPException
import fitz  # PyMuPDF

@app.post("/ask")
async def ask_question(file: UploadFile = File(...), question: str = Form(...)):
    filename = file.filename
    contents = await file.read()

    # Process PDF
    if filename.endswith(".pdf"):
        try:
            with open("temp.pdf", "wb") as f:
                f.write(contents)

            doc = fitz.open("temp.pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()

            # Simulated response (replace with actual LLM call)
            answer = f"📄 PDF parsed. Question: '{question}'\n\nExtract:\n{text[:500]}..."
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading PDF: {e}")

    # Process plain text
    elif filename.endswith(".txt"):
        try:
            text = contents.decode("utf-8")
            answer = f"📝 Text file parsed. Question: '{question}'\n\nExtract:\n{text[:500]}..."
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid UTF-8 text file.")
    else:
        raise HTTPException(status_code=400, detail="Only .pdf and .txt files are supported.")

    return {"answer": answer}

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

if __name__ == "__main__":
    uvicorn.run("backend.llm_server:app", host="127.0.0.1", port=8000, reload=True)
