import streamlit as st
import requests

SMTP_EMAIL = "vjaypunyapu26@gmail.com"
SMTP_PASSWORD = "wpof jbvu xzqw zvkb"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

st.title("🛠 Admin Dashboard")

st.subheader("📋 Current Users")
users_response = requests.get("http://localhost:8000/admin/users")
if users_response.status_code == 200:
    users = users_response.json()
    user_table = [{"Username": u, "Role": users[u]["role"]} for u in users]
    st.table(user_table)
else:
    st.error("Failed to load users")

st.subheader("📧 Send Activation Email")
email = st.text_input("Enter new user's email")
role = st.selectbox("Select role", ["assistant", "admin"])

if st.button("Send Activation Email"):
    if not email:
        st.error("Please enter a valid email address.")
    else:
        response = requests.post("http://localhost:8000/send-activation", json={
            "email": email,
            "role": role
        })
        if response.status_code == 200:
            data = response.json()
            st.success(f"✅ Activation email sent to {email}")
            st.code(data.get("activation_link", "No link returned"), language="text")
        else:
            st.error(f"❌ Failed to send activation email: {response.text}")
