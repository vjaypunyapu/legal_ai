from fastapi import FastAPI, UploadFile, Form, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt
import requests

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth setup
SECRET_KEY = "secret"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def fake_decode_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"username": payload.get("sub")}
    except Exception:
        return None

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username == "test" and form_data.password == "test123":
        token = jwt.encode({"sub": form_data.username}, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/ask")
async def ask_question(
    token: str = Depends(oauth2_scheme),
    file: UploadFile = File(...),
    question: str = Form(...)
):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(status_code=403, detail="Invalid token")

    # Call local Ollama LLM
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "mistral",
        "prompt": f"Answer this legal question: {question}",
        "stream": False
    })

    if response.ok:
        return {"answer": response.json().get("response", "")}
    else:
        raise HTTPException(status_code=500, detail="LLM error")
