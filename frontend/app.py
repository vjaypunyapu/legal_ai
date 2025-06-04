
import streamlit as st
import requests

st.set_page_config(page_title="Legal AI Assistant", layout="centered")
st.title("📑 Legal AI Assistant")

st.sidebar.title("🔐 Login")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")
login_btn = st.sidebar.button("Login")

if "token" not in st.session_state:
    st.session_state.token = None

if login_btn:
    res = requests.post(
        "http://localhost:8000/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if res.status_code == 200:
        st.session_state.token = res.json()["access_token"]
        st.sidebar.success("✅ Login successful")
    else:
        st.sidebar.error("❌ Invalid credentials")


if st.session_state.token:
    # continue with file upload & question answering

    uploaded_file = st.file_uploader("📄 Upload a legal PDF", type="pdf")
    question = st.text_input("Ask a legal question:")
    if st.button("Get Answer") and uploaded_file and question:
        files = {"file": uploaded_file}
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        data = {"question": question}
        res = requests.post("http://localhost:8000/ask", headers=headers, files=files, data=data)
        if res.ok:
            st.write("💬", res.json()["answer"])
        else:
            st.error("Error querying backend.")
else:
    st.warning("Please login to use the assistant.")
