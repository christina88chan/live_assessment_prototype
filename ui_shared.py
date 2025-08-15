import streamlit as st


def style_sidebar():
    st.markdown("""
    <style>
        /* Sidebar background and text */
        section[data-testid="stSidebar"] {
            background-color: #5c3a4e;
            color: white;
        }

        /* Sidebar title and headers */
        section[data-testid="stSidebar"] .css-ng1t4o {
            color: white;
        }

        /* Sidebar links and hover */
        .css-1aumxhk a {
            color: white !important;
        }

        .css-1aumxhk a:hover {
            color: #d087b3 !important;
        }

        /* Sidebar button override (e.g. Switch to Student View if added here) */
        .stButton button {
            background-color: #d087b3;
            color: black;
        }
    </style>
    """, unsafe_allow_html=True)

def create_admin_sidebar():
    style_sidebar()
    st.sidebar.title("Admin Navigation")
    st.sidebar.page_link("pages/admin_home.py", label="🏠 Dashboard")
    st.sidebar.page_link("pages/admin_edit_grades.py", label="✏️ Edit Grades")

def create_student_view_button():
    top_right = st.columns([8, 2])  # 90% space + 10% button
    with top_right[1]:
        if st.button("🔁 Student View"):
            st.switch_page("pages/student_assessment.py")

def render_admin_logout():
    # Spacer to push the button down (optional)
    st.sidebar.markdown("<br><br><br><br><br><br><br><br>", unsafe_allow_html=True)

    # Logout Button
    if st.sidebar.button("🚪 Log Out", key="logout_admin"):
        st.session_state.clear()
        st.switch_page("student_login.py")  # Or your main student page