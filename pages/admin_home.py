import streamlit as st

def create_admin_sidebar():
    with st.sidebar:
        st.subheader("Admin Navigation")
        if st.button("Admin Home"):
            st.switch_page("pages/admin_home.py")
        if st.button("Admin Edits"):
            st.switch_page("pages/admin_edits.py")
        if st.button("Admin Dash"):
            st.switch_page("pages/admin_dash.py")

def create_student_view_button():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col3:
        if st.button("Student View"):
            st.switch_page("student.py")

# Display the page content
st.header("Admin Home")

# Create the navigation elements
create_admin_sidebar()
create_student_view_button()