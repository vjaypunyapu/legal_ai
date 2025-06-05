
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import EmailStr
from jose import jwt, JWTError
from passlib.context import CryptContext
import smtplib
from email.message import EmailMessage
import json
import os

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

SECRET_KEY = "activation_secret"
ALGORITHM = "HS256"
USER_DB_PATH = "users.json"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SMTP_EMAIL = "vjaypunyapu26@gmail.com"
SMTP_PASSWORD = "tajm czva ktnn uein"  # App Password
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def get_password_hash(password):
    return pwd_context.hash(password)

def load_users():
    if not os.path.exists(USER_DB_PATH):
        return {}
    with open(USER_DB_PATH, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_DB_PATH, "w") as f:
        json.dump(users, f)

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

@app.post("/send-activation")
def send_activation(email: EmailStr, role: str):
    token = jwt.encode({"email": email, "role": role}, SECRET_KEY, algorithm=ALGORITHM)
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
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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
