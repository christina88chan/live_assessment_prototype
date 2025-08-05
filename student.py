import streamlit as st

def create_admin_view_button():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col3:
        if st.button("Admin Login"):
            st.switch_page("pages/admin_home.py")

st.header("Tech4Good Live Assessment Tool")
st.subheader("Student Submission View")
create_admin_view_button()
