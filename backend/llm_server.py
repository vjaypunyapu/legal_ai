from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Query, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext
import uvicorn
import os
import shutil
from typing import Dict

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "secret"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

users_db: Dict[str, Dict] = {
    "admin@example.com": {
        "password": pwd_context.hash("admin123"),
        "role": "admin",
        "activated": True
    },
    "assistant@example.com": {
        "password": pwd_context.hash("assistant123"),
        "role": "assistant",
        "activated": True
    }
}

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str):
    user = users_db.get(username)
    if user and verify_password(password, user["password"]):
        return user
    return None

def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Security(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None or username not in users_db:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return users_db[username]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not user.get("activated"):
        raise HTTPException(status_code=403, detail="User not activated")
    token = create_access_token({"sub": form_data.username, "role": user["role"]})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/ask")
def ask_question(file: UploadFile = File(...), question: str = Form(...), user: dict = Depends(get_current_user)):
    try:
        contents = file.file.read().decode("utf-8")
        answer = f"Answer to '{question}' based on uploaded document."
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        file.file.close()

@app.get("/admin/users")
def get_users():
    return users_db

@app.post("/admin/users")
def add_user(username: str = Query(...), password: str = Query(...), role: str = Query(...)):
    if username in users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    users_db[username] = {
        "password": pwd_context.hash(password),
        "role": role,
        "activated": False
    }
    return {"detail": "User added"}

@app.delete("/admin/users")
def delete_user(username: str = Query(...)):
    if username not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    if username == "admin@example.com":
        raise HTTPException(status_code=403, detail="Cannot delete default admin")
    del users_db[username]
    return {"detail": "User deleted"}

@app.post("/send-activation")
def send_activation(email: str = Query(...), role: str = Query(...)):
    if email not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    activation_link = f"http://localhost:8501/activate?email={email}"
    print(f"Sending activation link to {email}: {activation_link}")
    return {"activation_link": activation_link, "detail": "Email sent"}

@app.post("/activate")
def activate_user(email: str = Query(...)):
    if email in users_db:
        users_db[email]["activated"] = True
        return {"detail": "User activated"}
    else:
        raise HTTPException(status_code=404, detail="User not found")
    

@app.post("/admin/force-activate")
def force_activate_user(username: str = Query(...)):
    if username not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    users_db[username]["activated"] = True
    return {"detail": "User manually activated by admin"}

if __name__ == "__main__":
    uvicorn.run("backend.llm_server:app", host="127.0.0.1", port=8000, reload=True)
