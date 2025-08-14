# pages/admin_edits.py

# in progress

import streamlit as st
from ui_shared import admin_sidebar, student_top_button
from supabase_client import upsert_assignment, sign_out

# -----------------------------
# Init state
# -----------------------------
DEFAULTS = {
    "assignment_title": "",
    "question_text": "",
    "rubric_content": "",
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -----------------------------
# Page chrome
# -----------------------------
header_col, student_col = st.columns ([8, 1])
with header_col: 
    st.header("✏️ Edits")
with student_col:
    if st.button("Logout", use_container_width=True, key="button_logout"):
            st.toast("You have successfully logged out. Click on the student view to log out", icon="✅")
            sign_out()

admin_sidebar()

st.markdown("Create assignments for your students. Define the question and the grading criteria below.")

# -----------------------------
# Title at the top
# -----------------------------
st.subheader("Title")
col_t1, col_t2, col_t3 = st.columns([4, 1, 1])
with col_t1:
    new_title = st.text_input("Assignment title", value=st.session_state.assignment_title, key="title_input")
with col_t2:
    if st.button("Save Title", key="save_title"):
        st.session_state.assignment_title = new_title
        st.success("Title saved.")
        st.rerun()
with col_t3:
    if st.button("Clear Title", key="clear_title"):
        st.session_state.assignment_title = ""
        st.success("Title cleared.")
        st.rerun()

st.caption(f"Current title: {st.session_state.assignment_title or 'Untitled'}")

# -----------------------------
# Two-column editor
# -----------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📝 Question")
    with st.expander("Edit question", expanded=True):
        q_val = st.text_area(
            "Write the question students will answer:",
            value=st.session_state.question_text,
            height=220,
            key="question_text_area",
        )
        q1, q2 = st.columns(2)
        with q1:
            if st.button("💾 Save Question", key="save_question"):
                st.session_state.question_text = q_val
                st.success("Question saved.")
                st.rerun()
        with q2:
            if st.button("🗑️ Clear Question", key="clear_question"):
                st.session_state.question_text = ""
                st.success("Question cleared.")
                st.rerun()
    with st.expander("Preview question", expanded=False):
        if st.session_state.question_text:
            st.text(st.session_state.question_text)
        else:
            st.info("No question saved yet.")

with col_right:
    st.subheader("📋 Assessment Rubric")
    with st.expander("Edit rubric", expanded=True):
        rubric_val = st.text_area(
            "Paste or write your rubric:",
            value=st.session_state.rubric_content,
            height=220,
            key="rubric_text_area",
        )
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            if st.button("💾 Save Rubric", key="save_rubric"):
                st.session_state.rubric_content = rubric_val
                st.success("Rubric saved.")
                st.rerun()
        with col_r2:
            if st.button("🗑️ Clear Rubric", key="clear_rubric"):
                st.session_state.rubric_content = ""
                st.success("Rubric cleared.")
                st.rerun()
    with st.expander("Preview rubric", expanded=False):
        if st.session_state.rubric_content:
            st.text(st.session_state.rubric_content)
        else:
            st.info("No rubric content to preview.")

# -----------------------------
# Bottom actions
# -----------------------------
col_b1, col_b2 = st.columns(2)
with col_b1:
    if st.button("New Assignment", key="new_assignment"):
        for k in DEFAULTS:
            st.session_state[k] = DEFAULTS[k]
        st.success("Cleared. Start a new assignment.")
        st.rerun()
with col_b2:
    st.caption("Fill in Title, Question, and Rubric below, then save.")

# -----------------------------
# Save to Supabase
# -----------------------------
if st.button("Save assignment to Supabase", type="primary", key="save_to_supabase"):
    title = (st.session_state.assignment_title or "Untitled").strip()
    question = (st.session_state.question_text or "").strip()
    rubric = (st.session_state.rubric_content or "").strip()

    if not title:
        st.warning("Please enter a title before saving.")
    elif not question:
        st.warning("Please enter a question before saving.")
    else:
        try:
            payload = {
                "title": title,
                "description": "",  # optional
                "question_text": question,
                "rubric_text": rubric,
            }
            if st.session_state.get("current_assignment_id"):
                payload["id"] = st.session_state["current_assignment_id"]

            result = upsert_assignment(payload)
            data = (result or {}).get("data") or []
            if data:
                st.session_state["current_assignment_id"] = data[0].get("id")
                st.success("Assignment saved to Supabase.")
            else:
                st.info("No data returned from Supabase. Check RLS policies and keys.")
        except Exception as e:
            st.error(f"Failed to save to Supabase: {e}")
