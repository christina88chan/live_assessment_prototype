import streamlit as st
from supabase_client import sign_up, sign_in, sign_out

if "user_email" in st.session_state and st.session_state.user_email:
    st.switch_page("pages/admin_home.py")

def auth_screen():
    if st.button("← Back to Student Login"):
        st.switch_page("student_login_.py")
    
    st.title("🔐 Admin Login")
    st.markdown("""
    Welcome to the Admin Portal.  
    Please choose **Sign Up** if you're a new user, or **Login** if you already have an account.

    ### Sign Up Instructions:
    - Enter your email and a secure password.
    - After signing up, check your email inbox for a verification link from Supabase.
    - Once verified, return here and log in using your credentials.

    ### Login Instructions:
    - Enter the email and password you used during sign-up.
    - If you haven't verified your email yet, login may fail until you do.
    """)
    option = st.selectbox("Choose an action:", ["Login", "Sign Up"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if option == "Sign Up" and st.button("Register"):
        user = sign_up(email, password)
        if user and user.user:
            st.success("Registration successful. Please check your email to verify your account before logging in.")

    if option == "Login" and st.button("Login"):
        user = sign_in(email, password)
        if user and user.user:
            st.session_state.user_email = user.user.email
            st.success(f"Welcome back, {email}!")
            st.switch_page("pages/admin_home.py")
        else:
            st.error("Login failed. Make sure your email is verified and your credentials are correct.")

if "user_email" not in st.session_state:
    st.session_state.user_email = None

auth_screen()
