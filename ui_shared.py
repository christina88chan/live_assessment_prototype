# ui_shared.py
import streamlit as st

def admin_sidebar():
    with st.sidebar:
        st.subheader("Admin")
        if st.button("🏠 Admin Home", use_container_width=True, key="nav_home"):
            st.switch_page("pages/admin_home.py")
        if st.button("✏️ Admin Edits", use_container_width=True, key="nav_edits"):
            st.switch_page("pages/admin_edits.py")
        if st.button("📊 Admin Dash", use_container_width=True, key="nav_dash"):
            st.switch_page("pages/admin_dash.py")
        st.divider()
        if st.button("🎧 Student View", use_container_width=True, key="nav_student"):
            st.switch_page("student.py")

def student_top_button():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col3:
        if st.button("Go to Student View", key="btn_student_view_top"):
            st.switch_page("student.py")
