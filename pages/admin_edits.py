import streamlit as st
from pages.admin_home import create_admin_sidebar, create_student_view_button # Import the functions

# Display the page content
st.header("Admin Edits")

# Create the navigation elements by calling the imported functions
create_admin_sidebar()
create_student_view_button()