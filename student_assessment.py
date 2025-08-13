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
st.set_page_config(page_title="Live Assessment Tool - Assessment", layout="wide")

# ---------- Styles ----------
st.markdown("""
<style>
/* Ensure the app takes up the entire viewport height */
.stApp {
    height: 100vh;  /* Ensures full height of the screen is used */
    margin: 0;      /* Remove any default margin */
    display: flex;
    flex-direction: column;
}

/* Make the main content section fill the entire height */
[data-testid="stAppViewContainer"] {
    flex: 1; /* Take up the remaining space */
    display: flex;
    flex-direction: column;
}

/* Main app background - dark muted lavender */
.stApp {
    background-color: #3a2c3f;
    color: #f2f2f2;
}

/* Force text color everywhere */
.stMarkdown, .stText, .stDataFrame, .stTable, .stSelectbox, .stButton {
    color: #f2f2f2 !important;
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

/* Select box */
div.stSelectbox > div > label + div {
    background-color: #5c4a5f;
    color: #ffffff;
    border: 1px solid #c49bb4;
    border-radius: 6px;
}
div.stSelectbox > div > label + div > div {
    background-color: #5c4a5f;
    color: #ffffff;
}

/* Focus state */
input:focus, textarea:focus, select:focus {
    border-color: #ff85a1;
    box-shadow: 0 0 0 0.15rem rgba(255,133,161,0.3);
    outline: none;
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

/* Make columns breathe */
[data-testid="stVerticalBlock"] {
  gap: 1rem !important;
}

/* Box around col_right */
.col_right_border {
    border: 2px solid #c49bb4;  /* Border around the entire right column */
    border-radius: 10px;         /* Rounded corners */
    padding: 20px;               /* Padding inside the box */
    height: 100%;                /* Make the column stretch full height */
    display: flex;
    justify-content: center;
    align-items: center;
    text-align: center;
}

/* Ensuring the content inside col_right is vertically and horizontally centered */
.col_right_box_content {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    height: 100%; /* Full height inside the box */
}
</style>
""", unsafe_allow_html=True)

# ---------- Page Layout ----------
st.header("Blossom Assessment")
 
# Check if the API key is set
 
# Fetch assignments after login
assignments = list_assignments()
options = [
    {"id": a["id"], "title": (a.get("title") or "Untitled"), "question": (a.get("question_text") or "")}
    for a in assignments
]

if options:
    titles = [o["title"] for o in options]
    sel_idx = st.selectbox("Assignment", options=range(len(titles)), format_func=lambda i: titles[i], key="student_assignment_select")
    selected = options[sel_idx]
    st.session_state["selected_assignment_id"] = selected["id"]
    CURRENT_QUESTION = selected["question"] or "Default Question"
else:
    st.info("No assignments found yet. Using the default question.")
    st.session_state["selected_assignment_id"] = None
    CURRENT_QUESTION = "Explain your initial thoughts to the assessment question here"

st.markdown("### Question:")
st.info(CURRENT_QUESTION)

# Recording and Transcription Section
if 'recorded_audio_bytes' not in st.session_state:
    st.session_state.recorded_audio_bytes = None

recorded_audio_output = st.audio("recorded_audio.wav", format="audio/wav")

if st.button("Submit Answer"):
    if not st.session_state.recorded_audio_bytes:
        st.warning("Please record your answer first.")
    else:
        # Submit logic for the answer
        st.success("Answer submitted successfully!")

# Allow students to record answers if audio file exists
if 'recorded_audio_bytes' in st.session_state:
    st.audio(st.session_state.recorded_audio_bytes)
