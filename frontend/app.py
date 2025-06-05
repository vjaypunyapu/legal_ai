import streamlit as st
import requests
import base64
import json
from streamlit_option_menu import option_menu

st.set_page_config(page_title="Legal AI Admin", layout="wide")

if "token" not in st.session_state:
    st.session_state.token = None
    st.session_state.role = None

def login():
    st.title("🔐 Login to Legal AI")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        response = requests.post("http://localhost:8000/login", data={
            "username": username,
            "password": password
        })
        if response.status_code == 200:
            token = response.json()["access_token"]
            payload = jwt_decode(token)
            st.session_state.token = token
            st.session_state.role = payload["role"]
            st.success(f"Logged in as {payload['role']}")
            st.rerun()
        else:
            st.error("Login failed")

def jwt_decode(token):
    parts = token.split(".")
    padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
    decoded_bytes = base64.urlsafe_b64decode(padded)
    return json.loads(decoded_bytes)

if not st.session_state.token:
    login()
else:
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2884/2884523.png", width=50)
        st.markdown("### Legal AI Navigation")
        st.markdown(f"**Role:** {st.session_state.role}")
        menu = option_menu(
            menu_title="Navigate",
            options=["Dashboard", "Users", "Logs"] + (["Assistant"] if st.session_state.role == "assistant" else []),
            icons=["house", "person-plus", "file-earmark-text", "robot"],
            menu_icon="cast",
            default_index=0,
            orientation="vertical"
        )

        if st.button("Logout"):
            st.session_state.token = None
            st.session_state.role = None
            st.rerun()

    if st.session_state.role == "admin":
        if menu == "Dashboard":
            st.title("🛠 Admin Dashboard")
            st.write("Welcome to the Admin Control Center")

        elif menu == "Logs":
            st.title("📜 Recent Assistant Queries")
            with st.expander("View Recent Queries"):
                try:
                    with open("assistant_queries.log", "r") as f:
                        logs = f.readlines()
                    if logs:
                        st.code("".join(logs[-10:]), language="text")
                        st.download_button("📥 Download Full Log", data="".join(logs), file_name="assistant_queries.log")
                    else:
                        st.info("No recent activity found.")
                except FileNotFoundError:
                    st.info("No activity log available yet.")

        elif menu == "Users":
            st.title("👥 User Management")
            users = requests.get("http://localhost:8000/admin/users", headers={
                "Authorization": f"Bearer {st.session_state.token}"
            }).json()

            with st.expander("➕ Add New User"):
                new_username = st.text_input("New Username")
                new_password = st.text_input("New Password", type="password")
                new_role = st.selectbox("Select Role", ["assistant", "admin"])
                if st.button("Add User"):
                    if new_username and new_password:
                        res = requests.post(
                            f"http://localhost:8000/admin/users?username={new_username}&password={new_password}&role={new_role}",
                            headers={"Authorization": f"Bearer {st.session_state.token}"}
                        )
                        if res.status_code == 200:
                            st.success("User added.")
                            st.rerun()
                        else:
                            st.error(res.json().get("detail"))
                    else:
                        st.warning("Enter both username and password.")

            with st.expander("❌ Delete User"):
                user_to_delete = st.selectbox("Select user to delete", [u for u in users if u != "admin"])
                if st.button("Delete User"):
                    res = requests.delete(
                        f"http://localhost:8000/admin/users?username={user_to_delete}",
                        headers={"Authorization": f"Bearer {st.session_state.token}"}
                    )
                    if res.status_code == 200:
                        st.success("User deleted.")
                        st.rerun()
                    else:
                        st.error(res.json().get("detail"))

            with st.expander("👥 Current Users"):
                st.table([{"Username": u, "Role": users[u]["role"]} for u in users])

            with st.expander("📧 Send Activation Email"):
                email = st.text_input("Enter new user's email")
                role = st.selectbox("Select role", ["assistant", "admin"], key="role_select")
                if st.button("Send Activation Email"):
                    if not email:
                        st.error("Please enter a valid email address.")
                    else:
                        response = requests.post(
                            f"http://localhost:8000/send-activation?email={email}&role={role}",
                            headers={"Authorization": f"Bearer {st.session_state.token}"}
                        )
                        if response.status_code == 200:
                            data = response.json()
                            st.success(f"✅ Activation email sent to {email}")
                            st.code(data.get("activation_link", "No link returned"), language="text")
                        else:
                            st.error(f"❌ Failed to send activation email: {response.text}")

    elif st.session_state.role == "assistant" and menu == "Assistant":
        st.title("📄 Legal AI Assistant")
        uploaded_file = st.file_uploader("Upload a legal document", type=["pdf"])
        question = st.text_input("Ask a question about the document")
        if st.button("Submit") and uploaded_file and question:
            with st.spinner("Thinking..."):
                response = requests.post(
                    "http://localhost:8000/ask",
                    files={"file": uploaded_file},
                    data={"question": question},
                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                )
                if response.status_code == 200:
                    st.success("Answer:")
                    st.write(response.json()["answer"])
                else:
                    st.error(response.json()["detail"])
    else:
        st.error("Unauthorized user role.")
