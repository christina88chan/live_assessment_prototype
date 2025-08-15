import streamlit as st
from supabase_client import sign_up, sign_in

# Redirect to dashboard if already logged in
if "user_email" in st.session_state and st.session_state.user_email:
    st.switch_page("pages/admin_home.py")

# Blossom style: background, fonts, inputs, buttons
st.set_page_config(page_title="Admin Login", layout="wide")
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #2f2433 !important;
    color: #f2f2f2 !important;
    height: 100%;
    width: 100%;
    margin: 0;
    padding: 0;
}
[data-testid="stHeader"] {
    background: transparent !important;
    height: 0 !important;
    border-bottom: none !important;
}

/* Input styles */
input, textarea {
    background-color: #5c4a5f !important;
    color: white !important;
    border: 1px solid #c49bb4 !important;
    border-radius: 6px !important;
    padding: 10px !important;
    font-size: 16px !important;
}

/* Buttons */
.stButton > button {
    background-color: #d46a8c;
    color: white !important;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    border: none;
}
.stButton > button:hover {
    background-color: #b45873;
}

/* Titles */
h1, h2, h3 {
    color: #ffb6c1 !important;
}

/* Fix selectbox dropdown colors */
div[data-baseweb="select"] {
    background-color: #5c4a5f !important;
    color: white !important;
    border-radius: 8px;
    border: 1px solid #c49bb4 !important;
}

div[data-baseweb="select"] div {
    color: white !important;
}
<style>
/* Selectbox input fix */
[data-baseweb="select"] {
    background-color: #5c4a5f !important;
    color: white !important;
    border: 1px solid #c49bb4 !important;
    border-radius: 6px !important;
    padding: 10px !important;
    font-size: 16px !important;
}

/* Inside the select dropdown */
[data-baseweb="select"] div {
    color: white !important;
}

/* Fix the focus ring too */
[data-baseweb="select"]:focus-within {
    box-shadow: 0 0 0 2px #ffb6c1 !important;
}
</style>

</style>
""", unsafe_allow_html=True)

# Back button
if st.button("🔙 Back to Student Login"):
    st.switch_page("student_login.py")

# Title and instructions
st.title("🔐 Admin Login")

st.markdown("""
Welcome to the **Admin Portal** for Blossom.

Use this page to securely sign up or log in as an instructor.

### 📝 Sign Up Instructions:
- Enter your **email** and a **secure password**
- After signing up, check your inbox to verify your account
- Then come back here and log in

### 🔑 Login Instructions:
- Enter your credentials
- If your email isn't verified yet, login will fail
""")

# Toggle between login and signup
if "is_signup" not in st.session_state:
    st.session_state.is_signup = False

mode_text = "Sign Up" if st.session_state.is_signup else "Login"
st.subheader(mode_text)

email = st.text_input("Email", value=st.session_state.get("temp_email", ""))
password = st.text_input("Password", type="password", value=st.session_state.get("temp_password", ""))


if st.session_state.is_signup:
    if st.button("Register"):
        user = sign_up(email, password)
        if user and user.user:
            st.session_state.temp_email = email
            st.session_state.temp_password = password
            st.session_state.is_signup = False
            st.session_state.just_registered = True
            st.rerun()  # ← forces immediate UI refresh

else:
    if st.button("Login"):
        user = sign_in(email, password)
        if user and user.user:
            st.session_state.user_email = user.user.email
            st.success(f"🎉 Welcome, {email}!")
            st.session_state["is_admin_logged_in"] = True
            st.switch_page("pages/admin_home.py")  # triggers rerender
        
# Toggle link
if st.session_state.is_signup:
    if st.button("Already have an account? Log in"):
        st.session_state.is_signup = False
        st.rerun()
else:
    if st.button("Don't have an account? Sign up"):
        st.session_state.is_signup = True
        st.rerun()

