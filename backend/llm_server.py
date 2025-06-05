
from fastapi import FastAPI, UploadFile, Form, File, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import EmailStr
from jose import jwt, JWTError
from passlib.context import CryptContext
import requests
import pdfplumber
import json
import os
import smtplib
from email.message import EmailMessage

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

SECRET_KEY = "secret"
ACTIVATION_SECRET_KEY = "activation_secret"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
USER_DB_PATH = "users.json"

SMTP_EMAIL = "vjaypunyapu26@gmail.com"
SMTP_PASSWORD = "tajm czva ktnn uein"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def load_users():
    if not os.path.exists(USER_DB_PATH):
        return {}
    with open(USER_DB_PATH, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_DB_PATH, "w") as f:
        json.dump(users, f)

def fake_decode_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"username": payload.get("sub"), "role": payload.get("role")}
    except Exception:
        return None

def send_activation_email(email: str, token: str):
    link = f"http://localhost:8000/activate?token={token}"
    message = EmailMessage()
    message["Subject"] = "Activate your Legal AI account"
    message["From"] = SMTP_EMAIL
    message["To"] = email
    message.set_content(f"Welcome to Legal AI!\nPlease activate your account by visiting:\n{link}")

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(message)

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    users = load_users()
    print("Loaded users:", users)
    print("Form username:", form_data.username)
    print("Form password:", form_data.password)
    user = users.get(form_data.username)
    if user and verify_password(form_data.password, user["password"]):
        token = jwt.encode({"sub": form_data.username, "role": user["role"]}, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/ask")
async def ask_question(token: str = Depends(oauth2_scheme), file: UploadFile = File(...), question: str = Form(...)):
    user = fake_decode_token(token)
    if not user or user["role"] != "assistant":
        raise HTTPException(status_code=403, detail="Unauthorized")

    with open("assistant_queries.log", "a") as log_file:
        log_file.write(f"{user['username']}: {question} on {file.filename}\n")

    pdf_text = ""
    try:
        with pdfplumber.open(file.file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pdf_text += text + "\n"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read PDF: {e}")

    prompt = f"""Use the following document to answer this legal question:\n\n{pdf_text}\n\nQuestion: {question}"""
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "mistral", "prompt": prompt, "stream": False
    })

    if response.ok:
        return {"answer": response.json().get("response", "").strip()}
    else:
        raise HTTPException(status_code=500, detail="LLM error")

@app.get("/admin/users")
def list_users(token: str = Depends(oauth2_scheme)):
    admin = fake_decode_token(token)
    if not admin or admin["role"] != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")
    return load_users()

@app.post("/admin/users")
def add_user(request: Request, token: str = Depends(oauth2_scheme)):
    admin = fake_decode_token(token)
    if not admin or admin["role"] != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")
    new_user = request.query_params
    username = new_user.get("username")
    password = new_user.get("password")
    role = new_user.get("role")
    if not username or not password or not role:
        raise HTTPException(status_code=400, detail="Missing parameters")
    users = load_users()
    if username in users:
        raise HTTPException(status_code=400, detail="User already exists")
    users[username] = {"password": get_password_hash(password), "role": role}
    save_users(users)
    return {"status": "user added"}

@app.delete("/admin/users")
def delete_user(request: Request, token: str = Depends(oauth2_scheme)):
    admin = fake_decode_token(token)
    if not admin or admin["role"] != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")
    username = request.query_params.get("username")
    users = load_users()
    if username not in users:
        raise HTTPException(status_code=404, detail="User not found")
    if username == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete admin")
    users.pop(username)
    save_users(users)
    return {"status": "user deleted"}

@app.post("/send-activation")
def send_activation(email: EmailStr, role: str):
    token = jwt.encode({"email": email, "role": role}, ACTIVATION_SECRET_KEY, algorithm=ALGORITHM)
    try:
        send_activation_email(email, token)
        return {"status": "Activation email sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email send error: {e}")

@app.get("/activate", response_class=HTMLResponse)
def activate_form(token: str):
    return f"""
    <html>
    <body>
        <h2>Set Your Password</h2>
        <form action="/activate" method="post">
            <input type="hidden" name="token" value="{token}">
            <input type="password" name="password" placeholder="New password" required>
            <button type="submit">Activate Account</button>
        </form>
    </body>
    </html>
    """

@app.post("/activate", response_class=HTMLResponse)
async def activate_user(request: Request):
    form = await request.form()
    token = form["token"]
    password = form["password"]
    try:
        payload = jwt.decode(token, ACTIVATION_SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("email")
        role = payload.get("role")
        if not email or not role:
            raise HTTPException(status_code=400, detail="Invalid token")

        users = load_users()
        users[email] = {"password": get_password_hash(password), "role": role}
        save_users(users)
        return "<h3>✅ Account activated. You may now log in.</h3>"
    except JWTError:
        raise HTTPException(status_code=400, detail="Token invalid or expired")
