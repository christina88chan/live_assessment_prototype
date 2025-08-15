import streamlit as st
from supabase_client import get_all_submissions
from ui_shared import create_admin_sidebar, create_student_view_button, render_admin_logout
from collections import defaultdict

# Set wide layout and custom background
st.set_page_config(page_title="Admin Dashboard", layout="wide")

# Shared sidebar
create_admin_sidebar()
create_student_view_button()
render_admin_logout()


# Custom Blossom UI Styling (same as student side)
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

/* Headers */
h1, h2, h3, h4, h5 {
    color: #ffb6c1 !important;
}

/* Transcript and grade display boxes */
.transcript-box, .grade-box {
    background-color: #5c4a5f;
    padding: 10px;
    border-radius: 8px;
    color: white;
    white-space: pre-wrap;
    font-size: 16px;
}
</style>
""", unsafe_allow_html=True)

# Title
st.title("📊 Blossom Admin Dashboard")
st.markdown("""
Welcome to the **admin view** of the Blossom Assessment Tool.  
As an instructor, you can:
- View all student submissions
- See grades given (if any)
- Update student grades if needed
""")

# Fetch data
submissions = get_all_submissions()
num_submissions = len(submissions)

if not submissions:
    st.info("No submissions found yet.")
    st.stop()

st.success(f"📦 Total Submissions: {num_submissions}")
st.divider()

# Group by student name
grouped = defaultdict(list)
for sub in submissions:
    grouped[sub["student_name"]].append(sub)

# Loop through students
for student_name, subs in grouped.items():
    with st.expander(f"👤 {student_name} ({len(subs)} submission{'s' if len(subs) != 1 else ''})", expanded=False):
        for i, sub in enumerate(subs):
            st.markdown(f"### Submission #{i + 1}")
            st.markdown(f"**Submitted at:** {sub['created_at']}")

            # Transcript
            st.markdown("**Transcript:**")
            st.markdown(f"<div class='transcript-box'>{sub['transcript_text']}</div>", unsafe_allow_html=True)

            # Grade
            grade = sub.get("grade_json") or sub.get("grade_json")
            st.markdown("**Grade:**")
            if grade:
                st.markdown(f"<div class='grade-box'>{grade}</div>", unsafe_allow_html=True)
            else:
                st.markdown("⚠️ No grade assigned yet.")

            # Edit button
            if st.button(f"✏️ Edit Grade for {student_name} (#{i+1})", key=f"edit_{sub['id']}"):
                st.session_state.edit_target = {
                    "id": sub["id"],
                    "student_name": student_name,
                    "transcript_text": sub["transcript_text"],
                    "grade": grade
                }
                st.switch_page("pages/admin_edits.py")

            st.divider()
