import streamlit as st
from supabase_client import get_all_submissions
from ui_shared import create_admin_sidebar, create_student_view_button, render_admin_logout
from collections import defaultdict

# Sidebar and button
create_admin_sidebar()
render_admin_logout()

# Apply consistent background and theme colors like admin_home
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
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="top-right-button">', unsafe_allow_html=True)
create_student_view_button()
st.markdown('</div>', unsafe_allow_html=True)

# Page title and instructions
st.markdown("<h1 style='color:#F4AAB9;'>✏️ Edit Grades</h1>", unsafe_allow_html=True)
st.markdown("Use this page to **view and edit all student grades directly** in one place.")

# Fetch and display submissions
submissions = get_all_submissions()
st.success(f"📦 Total Submissions: {len(submissions)}")

if not submissions:
    st.info("No submissions yet.")
    st.stop()

grouped = defaultdict(list)
for sub in submissions:
    grouped[sub["student_name"]].append(sub)

#st.divider()

for student_name, subs in grouped.items():
    with st.expander(f"👤 {student_name} ({len(subs)} submission{'s' if len(subs) != 1 else ''})", expanded=False):
        for i, sub in enumerate(subs):
            st.markdown(f"**Submission #{i + 1}**")
            st.markdown(f"🕒 Submitted: `{sub['created_at']}`")
            st.markdown(f"📜 Transcript:\n\n{sub['transcript_text']}")

            current_grade = sub.get("grade_json") or sub.get("grade_json") or ""
            new_grade = st.text_area(
                f"✏️ Edit Grade (Current: {current_grade})",
                value=current_grade,
                key=f"grade_input_{sub['id']}"
            )

            if st.button(f"💾 Save Grade for #{i + 1}", key=f"save_{sub['id']}"):
                from supabase_client import get_client
                sb = get_client()
                try:
                    sb.table("submissions").update({
                        "grade_json": new_grade
                    }).eq("id", sub["id"]).execute()
                    st.success("Grade saved successfully.")
                    st.rerun()  # This will refresh the page and reflect the updated grade
                except Exception as e:
                    st.error(f"Error saving grade: {e}")

            #st.divider()
