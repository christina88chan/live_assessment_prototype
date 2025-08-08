# pages/admin_dash.py

import streamlit as st
from datetime import datetime
import pandas as pd

from ui_shared import admin_sidebar, student_top_button
from supabase_client import list_assignments, list_submissions

st.header("Admin Dash")
admin_sidebar()
student_top_button()

# Refresh + timestamp
c1, c2 = st.columns([1, 3])
with c1:
    if st.button("Refresh"):
        st.cache_data.clear()
        st.rerun()
with c2:
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Pull latest data from Supabase
try:
    assignments = list_assignments()
except Exception as e:
    st.error(f"Failed to load assignments: {e}")
    st.stop()

if not assignments:
    st.info("No assignments yet. Create one in Admin Edits.")
    st.stop()

st.markdown("---")

# Render each assignment with a submissions table
for a in assignments:
    a_id = a.get("id")
    a_title = a.get("title") or "Untitled"

    try:
        subs = list_submissions(a_id)
    except Exception as e:
        subs = []
        st.warning(f"Could not load submissions for '{a_title}': {e}")

    numeric_grades = [s.get("grade_overall") for s in subs if isinstance(s.get("grade_overall"), (int, float))]
    avg = round(sum(numeric_grades) / len(numeric_grades), 2) if numeric_grades else None
    last_sub_time = max((s.get("created_at") for s in subs if s.get("created_at")), default="—")

    with st.container(border=True):
        t1, t2, t3 = st.columns([3, 1, 1])
        with t1:
            st.markdown(f"**{a_title}**")
            st.caption(f"Created: {a.get('created_at')}")
        with t2:
            st.metric("Submissions", len(subs))
        with t3:
            st.metric("Average", avg if avg is not None else "—")

        st.caption(f"Last submission: {last_sub_time}")

        with st.expander("Submissions table", expanded=False):
            if subs:
                rows = [
                    {
                        "Student": s.get("student_name") or "—",
                        "Submitted": s.get("created_at"),
                        "Grade": s.get("grade_overall"),
                        "Transcript chars": len((s.get("transcript_text") or "")),
                    }
                    for s in subs
                ]
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No submissions yet for this assignment.")

        with st.expander("Question & Rubric", expanded=False):
            st.markdown("**Question**")
            st.text(a.get("question_text") or "—")
            st.markdown("**Rubric**")
            st.text(a.get("rubric_text") or "—")

        b1, b2 = st.columns(2)
        with b1:
            if st.button("Edit assignment", key=f"edit_{a_id}"):
                st.session_state.current_assignment_id = a_id
                st.session_state.assignment_title = a.get("title") or ""
                st.session_state.question_text = a.get("question_text") or ""
                st.session_state.rubric_content = a.get("rubric_text") or ""
                st.switch_page("pages/admin_edits.py")
        with b2:
            st.caption(" ")
            st.caption(" ")

st.markdown("---")
st.caption("Data shown is pulled live from Supabase on each refresh.")
