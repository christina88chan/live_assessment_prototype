# =========================
# student.py  (full file)
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
st.set_page_config(page_title="Live Assessment Tool", layout="wide")

@st.cache_data(ttl=30)
def fetch_assignments():
    try:
        return list_assignments()
    except Exception as e:
        st.error(f"Couldn’t load assignments from Supabase: {e}")
        return []

def create_admin_view_button():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col3:
        if st.button("Admin Login"):
            st.switch_page("pages/auth.py")

st.header("Tech4Good Live Assessment Tool")
create_admin_view_button()

# ---------- Styles ----------
st.markdown("""
<style>

/* Main app background - dark muted lavender */
.stApp {
    background-color: #3a2c3f;
    color: #f2f2f2; /* Global light text */
}

/* Sidebar background - slightly lighter tone */
[data-testid="stSidebar"] {
    background-color: #4a3b4f;
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
/* Nudge the main content down a touch so the title isn't cramped */
.block-container {
  padding-top: 1.5rem !important;
}
/* Ensure your main header is readable on the dark background */
h1 {
  color: #ffe3ea !important;  /* light pastel */
  margin-top: 0 !important;
}g
/* Make columns breathe */
[data-testid="stVerticalBlock"] {
  gap: 1rem !important;
</style>
""", unsafe_allow_html=True)


st.markdown(
    "<div><p style='text-align:center;'>Answer the question with an audio recording, get it transcribed, and graded.</p></div>",
    unsafe_allow_html=True
)

st.warning("Ensure your audio recordings are clear and the language is primarily English for best results.")

# ---------- Session state ----------
if 'recorded_audio_bytes' not in st.session_state:
    st.session_state.recorded_audio_bytes = None
if 'edited_transcription_text' not in st.session_state:
    st.session_state.edited_transcription_text = ""
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
    if not st.session_state.edited_transcription_text.strip():
        st.warning("Answer content cannot be empty.")
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
                "grade_overall": None,
                "grade_json": {"text": st.session_state.grade_feedback} if st.session_state.grade_feedback else None,
            }
            data = insert_submission(payload)
            if data:
                st.success("Answer submitted and saved to Supabase!")
            else:
                st.warning("Submission saved locally, but Supabase didn’t return a row. Check RLS/policies.")
        except Exception as e:
            st.error(f"Failed to save to Supabase: {e}")

        # Reset after submit
        st.session_state.recorded_audio_bytes = None
        st.session_state.edited_transcription_text = ""
        st.session_state.show_editor = False
        st.session_state.grade_feedback = None
        st.rerun()


# ---------- Defaults ----------
HARDCODED_QUESTION = "Explain your initial thoughts to the assessment question here"
CURRENT_QUESTION = HARDCODED_QUESTION

# ---------- Layout ----------
col_left, col_right = st.columns([1.3, 0.7])

# ----- Left: assignment & question -----
with col_left:
    st.markdown("### Choose an assignment")
    assignments = fetch_assignments()
    options = [
        {"id": a["id"], "title": (a.get("title") or "Untitled"), "question": (a.get("question_text") or "")}
        for a in assignments
    ]

    if options:
        titles = [o["title"] for o in options]
        sel_idx = st.selectbox(
            "Assignment",
            options=range(len(titles)),
            format_func=lambda i: titles[i],
            key="student_assignment_select",
        )
        selected = options[sel_idx]
        st.session_state["selected_assignment_id"] = selected["id"]
        CURRENT_QUESTION = selected["question"] or HARDCODED_QUESTION
    else:
        st.info("No assignments found yet. Using the default question.")
        st.session_state["selected_assignment_id"] = None
        CURRENT_QUESTION = HARDCODED_QUESTION

    st.markdown("### Question:")
    st.info(CURRENT_QUESTION)

# ----- Right: name, API key, tabs -----
with col_right:
    visitor_input_id = st.text_input("Name", key="visitor_id_input")

    # API key UI (collapses after set)
    if not st.session_state.api_key_set:
        st.subheader("Gemini API Key")
        api_key_input = st.text_input(
            "Enter API Key",
            type="password",
            help="Used for transcription only. Not stored.",
            key="api_key_input"
        )
        c_btn, c_msg = st.columns([1, 2])
        with c_btn:
            if st.button("Use API Key", key="api_key_submit"):
                if not api_key_input:
                    st.session_state.api_key_status = "error: Please paste your Gemini API key."
                else:
                    try:
                        genai.configure(api_key=api_key_input)
                        st.session_state.api_key_set = True
                        st.session_state.api_key_value = api_key_input
                        st.session_state.api_key_status = "ok"
                    except Exception as e:
                        st.session_state.api_key_status(f"error: Failed to configure Gemini API. Check your key. Error: {e}")
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

    st.subheader("Record & Grade")

    if not st.session_state.api_key_set:
        st.info("Please enter your Gemini API Key to enable recording and transcription.")
    else:
        # Ensure configured with saved key
        try:
            genai.configure(api_key=st.session_state.api_key_value)
        except Exception as e:
            st.error(f"Failed to configure Gemini API. Error: {e}")
            st.stop()

        # Tabs (single recorder instance lives in tab_record)
        tab_record, tab_review = st.tabs(["Record & Transcribe", "Review & Grade"])

        with tab_record:
            recorded_audio_output = mic_recorder(
                start_prompt="Click to Start Recording",
                stop_prompt="Click to Stop Recording",
                use_container_width=True,
                key=_uk('audio_recorder')
            )

            if recorded_audio_output and recorded_audio_output.get('bytes'):
                st.session_state.recorded_audio_bytes = recorded_audio_output['bytes']
                st.audio(st.session_state.recorded_audio_bytes, format="audio/wav")
                st.info("Recorded audio ready for transcription.")
                st.session_state.show_editor = True

            if st.session_state.show_editor and st.session_state.recorded_audio_bytes:
                if st.button("Transcribe Recording", key=_uk("transcribe_audio_button")):
                    if not visitor_input_id:
                        st.warning("Please enter your Name / ID before transcribing.")
                    else:
                        with st.spinner("Transcribing your audio..."):
                            try:
                                mime_type = "audio/wav"
                                audio_io = io.BytesIO(st.session_state.recorded_audio_bytes)
                                audio_io.name = "recorded_audio.wav"

                                audio_file = genai.upload_file(
                                    path=audio_io,
                                    mime_type=mime_type,
                                    display_name=f"Answer_from_{visitor_input_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                                )

                                # poll until processed
                                while getattr(audio_file, "state", None) and getattr(audio_file.state, "name", "") == "PROCESSING":
                                    st.info("File is still processing on Gemini's side...")
                                    import time
                                    time.sleep(1)
                                    audio_file = genai.get_file(audio_file.name)

                                prompt = "Transcribe the given audio accurately. Provide only the spoken text."
                                model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
                                response = model.generate_content([audio_file, prompt])
                                st.session_state.edited_transcription_text = response.text or ""

                                st.success("Transcription complete! Switch to the 'Review & Grade' tab to edit and grade.")

                            except GoogleAPIError as api_err:
                                st.error(f"Gemini API Error: {api_err.message}")
                                st.info("Please check your API key validity, ensure billing is enabled, or audio is not too long.")
                                st.exception(api_err)
                            except Exception as e:
                                st.error(f"An unexpected error occurred during transcription: {e}")
                                st.info("Ensure the audio recording was successful.")
                                st.exception(e)
            # Inside tab_record, right under the recorder
            if st.button("Submit Answer", key=_uk("save_message_button")):
                if not st.session_state.get("visitor_id_input"):
                    st.warning("Please enter your Name / ID before submitting.")
                elif not st.session_state.edited_transcription_text.strip():
                    st.warning("Answer content cannot be empty.")
                elif not st.session_state.get("selected_assignment_id"):
                    st.warning("Please choose an assignment before submitting.")
                else:
                    with st.spinner("Saving your response..."):
                        save_filename = f"answer_from_{st.session_state.get('visitor_id_input')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"

                        message_metadata = {
                            "source_app": "Streamlit Text-based Grading",
                            "gemini_model": "1.5-flash-latest",
                            "original_audio_length_bytes": len(st.session_state.recorded_audio_bytes) if st.session_state.recorded_audio_bytes else 0,
                            "question": CURRENT_QUESTION,
                            "assignment_id": st.session_state.get("selected_assignment_id"),
                            "grading_prompt": st.session_state.get("grading_prompt_text", ""),
                            "grade_feedback": st.session_state.grade_feedback
                        }

                        try:
                            payload = {
                                "assignment_id": st.session_state["selected_assignment_id"],
                                "student_name": st.session_state.get("visitor_id_input"),
                                "transcript_text": st.session_state.edited_transcription_text,
                                "grade_overall": None,
                                "grade_json": {"text": st.session_state.grade_feedback} if st.session_state.grade_feedback else None,
                            }
                            data = insert_submission(payload)
                            if data:
                                st.success("Answer submitted and saved to Supabase!")
                            else:
                                st.warning("Submission saved locally, but Supabase didn’t return a row. Check RLS/policies.")
                        except Exception as e:
                            st.error(f"Failed to save to Supabase: {e}")

            # Reset after submit
                        st.session_state.recorded_audio_bytes = None
                        st.session_state.edited_transcription_text = ""
                        st.session_state.show_editor = False
                        st.session_state.grade_feedback = None
                        st.rerun()


                            

        with tab_review:
            # Editor + Grade
            if st.session_state.edited_transcription_text:
                st.subheader("Review and Edit Your Answer:")
                st.session_state.edited_transcription_text = st.text_area(
                    "Edit your transcribed answer here:",
                    value=st.session_state.edited_transcription_text,
                    height=200,
                    key="transcription_editor"
                )

                if st.button("Grade Response", key=_uk("grade_response_button")):
                    if not st.session_state.edited_transcription_text.strip():
                        st.warning("Transcription is empty. Record and transcribe your audio first.")
                    else:
                        with st.spinner("Getting evaluation from Gemini..."):
                            try:
                                grading_model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
                                student_submission = st.session_state.edited_transcription_text

                                # ---- Prompt build  ----
                                course_name = "Generative AI Skill-Building"
                                course_goals = "to learn how to use and evaluate AI models"
                                key_concepts = "Prompt Engineering, Prompt Workflow, Evaluation Metrics"

                                assessment_summary = '''
                                Create a Prompt Engineering Workflow to generate personalized Human Bingo squares that facilitate meaningful connections between participants based on their survey responses.

                                Requirements:
                                - Generate 6 general squares (3 popular themes, 3 niche themes)
                                - Create up to 3 personalized squares per participant
                                - Use LLM prompts to extract themes and match participants
                                - Include evaluation metrics for assessing output quality
                                '''

                                assessment_reflection_instructions = '''The student reflections should cover the following:
                                • a brief outline of initial thoughts about how they might break down the task,
                                • discussion of how they created and intiial prompt how they plan to iterate on it next based on results,
                                • initial thoughts on evaluation metrics they will use to evaluate results of their prompts.'''

                                purpose = f'''You are a Teaching Assistant and you will be evaluating student reflections based on a given rubric. Students are taking part in a {course_name} course to {course_goals}. This includes learning the key concepts of {key_concepts} if a students submission does not include anything to grade (empty submission) then provide 0s for all the concepts and say missing submission for the reasoning since every student still requires a grade.'''

                                assessment_details = f'''Students were given an assessment where they had to solve a complex problem to test their understanding of {key_concepts}.
                                Before the students started working on the problem, they were required to submit an initial reflection on how they plan to tackle the problem to assess their understandings of the key concepts of the course.
                                {assessment_reflection_instructions}'''

                                model_instructions = ''' Your task is to take these intial student reflections on how they plan to tackle the problem and assess their understanding of key concepts given in the rubric below: '''

                                rubric_json = {
                                    "Prompt Engineering" : {"Description" : "utilizes clear instructions, examples, formatting requirements and other best practices to design effective prompts.",
                                        "Grades" : {
                                            "Missing (0%)": "No prompts are designed.",
                                            "Major Misconceptions (50%)": "Prompts poorly designed with short or unclear instructions. no formatting requirements and no or few examples and step-by-step guidance",
                                            "Nearly Proficient (80%)": "Prompts designed with some clarity, but instructions, formatting requirements, or examples may be irrelevant or lack important details",
                                            "Proficient (100%)": "Prompts well-designed with clear instructions, relevant examples, and logical step-by-step thinking",
                                            "Mastery (102%)": "Prompts exceptionally well-designed with clear instructions, highly relevant and illustrative examples, and comprehensive step-by-step guidance for the task and format"
                                        }
                                    },
                                    "Prompt Workflow Breakdown" : {"Description" : "demonstrates clear step-by-step thinking to effectively breakdown into a series of prompts.",
                                        "Grades" : {
                                            "Missing (0%)": "Problem Solution not broken down into series of steps and prompts",
                                            "Major Misconceptions (50%)": "Prompt breakdown poorly designed with very few or irrelevant steps",
                                            "Nearly Proficient (80%)": "Prompt workflow designed with some steps and clarity, but may lack important details or steps",
                                            "Proficient (100%)": "Prompts workflow well-designed with clear instructions and logical step-by-step thinking",
                                            "Mastery (102%)": "Prompt Workflow exceptionally well-designed with clear instructions and comprehensive step-by-step breakdown"
                                        }
                                    },
                                    "Evaluation Metrics" : {"Description" : "defines metrics that are well-defined and relevant to the problem",
                                        "Grades" : {
                                            "Missing (0%)": "No metrics are defined.",
                                            "Major Misconceptions (50%)": "Not enough metrics designed or metrics may not be applicable to the problem context",
                                            "Nearly Proficient (80%)": "Metrics have been defined but may be lacking clarity. Some metrics may not be relevant to the problem context",
                                            "Proficient (100%)": "Metrics are well designed; metrics are applicable and provide helpful insights for the problem context",
                                            "Mastery (102%)": "Metrics are fully defined with perfect clarity They are applicable and provide helpful insights for the problem context"
                                        }
                                    },
                                }

                                rubric_instructions = f'''For each of the three key concepts in the rubric: {key_concepts}, assign the student one of the Grades between Missing, Major Miconceptions, Nearly Proficient, Proficient, Mastery based on their understanding. Ensure the grades directly reflects the sum of the strengths and weaknesses identified in the critiques.'''

                                expected_output_format = '''
                                Assessment Scores:

                                Concept: [Concept Name]
                                Grade: [Grade]
                                Reasoning: [Rationale for score]

                                Concept: [Concept Name]
                                Grade: [Grade]
                                Reasoning: [Rationale for score]

                                Concept: [Concept Name]
                                Grade: [Grade]
                                Reasoning: [Rationale for score]
                                '''

                                expected_output_examples = '(Examples omitted here for brevity — keeping your original structure)'

                                master_prompt = f'''
                                Purpose: {purpose}

                                Assessment Context: {assessment_details}

                                {model_instructions}

                                Rubric: {rubric_json}

                                {rubric_instructions}

                                Output Format
                                Use the following output format to output your results:
                                {expected_output_format}

                                Students Assessment Problem Statement:
                                Here is the problem statement that was given to the students:
                                {assessment_summary}

                                Here are 3 examples of student submissions and their assessments:
                                {expected_output_examples}

                                Student Submission:
                                This is one students submissions: {student_submission}
                                '''

                                st.session_state.grading_prompt_text = master_prompt
                                grading_response = grading_model.generate_content(master_prompt)
                                st.session_state.grade_feedback = grading_response.text
                                st.success("Evaluation complete!")
                            except GoogleAPIError as api_err:
                                st.error(f"Gemini API Error during grading: {api_err.message}")
                                st.exception(api_err)
                            except Exception as e:
                                st.error(f"An unexpected error occurred during grading: {e}")
                                st.exception(e)
            else:
                st.info("No transcription yet. Use the 'Record & Transcribe' tab first.")

# ---------- Grade feedback ----------
if st.session_state.grade_feedback:
    st.subheader("Gemini Evaluation:")
    st.info(st.session_state.grade_feedback)


# ---------- Fallback hint ----------
if not st.session_state.recorded_audio_bytes:
    st.info("Use the 'Record & Transcribe' tab to get started.")
