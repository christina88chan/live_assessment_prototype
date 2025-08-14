# =========================
# student_login_.py  (full file)
# =========================

import streamlit as st
import google.generativeai as genai
import io
import os
from streamlit_mic_recorder import mic_recorder
from google.api_core.exceptions import GoogleAPIError
from datetime import datetime
import json
from supabase_client import list_assignments, insert_submission

# Streamlit needs this BEFORE any UI calls
st.set_page_config(page_title="Blossom Assessment - Login", layout="wide")

@st.cache_data(ttl=30)
def fetch_assignments():
    try:
        return list_assignments()
    except Exception as e:
        st.error(f"Couldnâ€™t load assignments from Supabase: {e}")
        return []


header_col, admin_col = st.columns ([8, 1])
with header_col: 
    st.header("Blossom Assessment - Student View")
with admin_col:
    if st.button("Admin Login"):
        st.switch_page("pages/auth.py")

# ---------- Styles ----------
st.markdown("""
<style>

/* Make sure the content inside columns stretches */
    .block-container {
        flex: 1;
        display: flex;
        justify-content: center;
        align-items: center;
    }
/* Inputs & textareas */
div.stTextInput > div > div > input,
div.stTextArea > div > div > textarea,
div.stNumberInput > div > div > input {
    background-color: #5c4a5f;
    color: #ffffff;
    border: 1px solid #c49bb4;
    border-radius: 6px;
    padding: 10px;
}
/* Password input */
div.stTextInput input[type="password"] {
    background-color: #5c4a5f;
    color: #ffffff;
    border: 1px solid #c49bb4;
}
/* Buttons */
.stButton > button, button[kind="primary"] {
    background-color: #d46a8c;
    color: white !important;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    border: none;
}
.stButton > button:hover, button[kind="primary"]:hover {
    background-color: #b45873;
}

/* Headers */
h1, h2, h3, h4, h5 {
    color: #ffb6c1 !important;
}

/* Card / panel */
.block-container {
    background-color: #2f2433;
    border-radius: 10px;
    padding: 12px;
    color: #f2f2f2;
}
 
/* Make Streamlit's top header transparent so it doesn't look like a black bar */
[data-testid="stHeader"] {
  background: transparent !important;
  backdrop-filter: none !important;
  border-bottom: none !important;
}
</style>
""", unsafe_allow_html=True)



# ---------- Session state ----------
if 'recorded_audio_bytes' not in st.session_state:
    st.session_state.recorded_audio_bytes = None
if 'edited_transcription_text' not in st.session_state:
    st.session_state.edited_transcription_text = ""
if 'student_prompt_text' not in st.session_state:
    st.session_state.student_prompt_text = ""
if 'show_editor' not in st.session_state:
    st.session_state.show_editor = False
if 'grade_feedback' not in st.session_state:
    st.session_state.grade_feedback = None
if 'grading_prompt_text' not in st.session_state:
    st.session_state.grading_prompt_text = ""
if 'api_key_set' not in st.session_state:
    st.session_state.api_key_set = ""   # "", "ok", or "error: ..."
if 'api_key_value' not in st.session_state:
    st.session_state.api_key_value = ""
if 'api_key_status' not in st.session_state:
    st.session_state.api_key_status = ""   # "", "ok", or "error: ..."

def _uk(base: str) -> str:
    """Unique widget keys per assignment + user to avoid collisions."""
    return f"{base}_{st.session_state.get('selected_assignment_id') or 'na'}_{st.session_state.get('visitor_id_input') or 'anon'}"


def _submit_answer():
    if not st.session_state.get("visitor_id_input"):
        st.warning("Please enter your Name / ID before submitting.")
        return
    if not st.session_state.student_prompt_text.strip():
        st.warning("Final prompt cannot be empty.")
        return
    if not st.session_state.get("selected_assignment_id"):
        st.warning("Please choose an assignment before submitting.")
        return

    with st.spinner("Saving your response..."):
        try:
            payload = {
                "assignment_id": st.session_state["selected_assignment_id"],
                "student_name": st.session_state.get("visitor_id_input"),
                "transcript_text": st.session_state.edited_transcription_text,
                "student_prompt": st.session_state.student_prompt_text,
                "grade_overall": None,
                "grade_json": {"text": st.session_state.grade_feedback} if st.session_state.grade_feedback else None,
            }
            data = insert_submission(payload)
            if data:
                st.success("Answer submitted and saved to Supabase!")
            else:
                st.warning("Submission saved locally, but Supabase didnâ€™t return a row. Check RLS/policies.")
        except Exception as e:
            st.error(f"Failed to save to Supabase: {e}")

        # Reset after submit
        st.session_state.recorded_audio_bytes = None
        st.session_state.edited_transcription_text = ""
        st.session_state.student_prompt_text = ""
        st.session_state.show_editor = False
        st.session_state.grade_feedback = None
        st.rerun()

# ---------- Layout ----------
col_left, col_mid, col_right = st.columns([2, .2, 3])

# ----- Left: assignment & question -----
with col_left:
    st.markdown("Fill in the information below to begin your assessment.")
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    api_key = st.text_input("API Key", type="password", help="Used for transcription only. Not stored.", key="api_key_input")
    
    affirmation = st.checkbox("I affirm that I will not give or receive any unauthorized help on this exam, and that all work will be my own.")

# ---------- API Key Setup Logic ----------

if not st.session_state.get("api_key_set", False):
    c_btn, c_msg = st.columns([1, 2])
    with c_btn:
        if st.button("Use API Key", key="api_key_submit"):
            if not api_key:
                st.session_state.api_key_status = "error: Please paste your Gemini API key."
            else:
                try:
                    genai.configure(api_key=api_key)
                    st.session_state.api_key_set = True
                    st.session_state.api_key_status = "ok"
                except Exception as e:
                    st.session_state.api_key_status = f"error: Failed to configure Gemini API. Check your key. Error: {e}"
    with c_msg:
        status = st.session_state.get("api_key_status", "")
        if status == "ok":
            st.success("Gemini API configured!")
        elif status.startswith("error:"):
            st.error(status.replace("error: ", ""))

else:
            # configured state
    c_label, c_change = st.columns([2, 1])
    with c_label:
        st.success("Gemini API configured.")
    with c_change:
        if st.button("Change API Key", key="api_key_change"):
            st.session_state.api_key_set = False
            st.session_state.api_key_value = ""
            st.session_state.api_key_status = ""
            st.rerun()

if st.button("Click to begin"):
    if first_name and last_name and api_key and affirmation:
    # Store session data
        st.session_state.first_name = first_name
        st.session_state.last_name = last_name
        st.session_state.api_key = api_key
        st.session_state.api_key_set = True  # API key is set
        st.switch_page("pages/student_assessment.py")

    else:
        st.warning("Please fill in all fields and check the affirmation.")
    # Checkbox for affirmation
    


# ----- Right: name, API key, tabs -----
with col_right:
    with st.container(border=True):
        st.markdown("<h2 style='text-align: center;'>Welcome to your assessment</h2>", unsafe_allow_html=True)

        st.markdown("""
            <div style="text-align: center; font-size: 24px;">
            Once you have logged in, you will have 1 hour to complete this assessment. 
            You will have the opportunity to read over the assessment and record your response using a microphone. 
            After you evaluate your response and click submit, the assignment will be evaluated and sent to the instructor.
            </div>
        """, unsafe_allow_html=True)

        st.text("")
        st.text("")
    


      