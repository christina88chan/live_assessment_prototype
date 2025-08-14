# ui_shared.py
import streamlit as st
from supabase_client import sign_out

def admin_sidebar():
    with st.sidebar:
        st.subheader("Admin")
        if st.button("🏠 Home", use_container_width=True, key="nav_home"):
            st.switch_page("pages/admin_home.py")
        if st.button("✏️ Edits", use_container_width=True, key="nav_edits"):
            st.switch_page("pages/admin_edits.py")
        st.divider()
        if st.button("🎧 Student View", use_container_width=True, key="nav_student"):
            st.switch_page("student_login_.py")
        if st.button("Logout", use_container_width=True, key="nav_logout"):
            # Show confirmation popup
            st.toast("You have successfully logged out. Please redirect to Student View", icon="✅")
            # Optional: Pause briefly so user sees the toast
            # import time
            # time.sleep(2)
            # Redirect to student login
            # Clear session safely
            sign_out()
            # st.switch_page("student_login_.py")


def student_top_button():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col3:
        if st.button("Go to Student View", key="btn_student_view_top"):
            st.switch_page("student_login_.py")
