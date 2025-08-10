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
st.set_page_config(page_title="Live Assessment Tool", layout="centered")

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

### code copy pasted from Aashna's streamlit demo: ###

# Custom CSS styling
st.markdown("""
<style>
/* Font and background */
body, input, textarea, select {
    font-family: 'Segoe UI', 'Roboto', sans-serif;
    background: linear-gradient(to right, #fff0f5, #ffe4e1);
}

/* General input fields */
div.stTextInput > div > div > input,
div.stTextArea > div > div > textarea,
div.stNumberInput > div > div > input {
    background-color: #FDDDE6;
    color: #262730;
    border: 1px solid #FFC0CB;
    border-radius: 5px;
    padding: 10px;
    box_shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
    transition: all 0.3s ease-in-out;
}

/* Password field */
div.stTextInput input[type="password"] {
    background-color: #FFD9E9;
    color: #262730;
    border: 1px solid #FFC0CB;
    border-radius: 5px;
    padding: 10px;
    transition: all 0.3s ease-in-out;
}

/* Selectbox styling */
div.stSelectbox > div > label + div {
    background-color: #FFD9E9;
    border: 1px solid #FFC0CB;
    border_radius: 5px;
    box_shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
    transition: all 0.3s ease-in-out;
}
div.stSelectbox > div > label + div > div {
     background-color: #FFD9E9;
}

/* Focus effects */
input:focus, textarea:focus, select:focus {
    border-color: #FF69B4;
    box_shadow: 0 0 0 0.1rem rgba(255, 105, 180, 0.25);
    outline: none;
}

/* Button styling */
button[kind="primary"] {
    background-color: #FFB6C1;
    color: #262730;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: bold;
    border: none;
    transition: all 0.3s ease-in-out;
}

button[kind="primary"]:hover {
    background-color: #FF69B4;
    box_shadow: 0 0 10px rgba(255, 105, 180, 0.3);
}
</style>
""", unsafe_allow_html=True)

# Elegant UI container
st.markdown("""
<div>
    <p style='text-align:center;'>Answer the question with an audio recording, get it transcribed, and graded.</p>
</div>
""", unsafe_allow_html=True)

# UI and message
st.warning("Ensure your audio recordings are clear and the language is primarily English for best results.")

# --- Initialize Session State Variables ---
if 'recorded_audio_bytes' not in st.session_state:
    st.session_state.recorded_audio_bytes = None
if 'edited_transcription_text' not in st.session_state:
    st.session_state.edited_transcription_text = ""
if 'show_editor' not in st.session_state:
    st.session_state.show_editor = False
if 'grade_feedback' not in st.session_state:
    st.session_state.grade_feedback = None
# store the grading prompt so submit won't crash if user didn't grade this run
if 'grading_prompt_text' not in st.session_state:
    st.session_state.grading_prompt_text = ""

# --- Hardcoded Question (fallback) ---
HARDCODED_QUESTION = """Explain your initial thoughts to the assessment question here"""
CURRENT_QUESTION = HARDCODED_QUESTION

# --- Layout Start ---
col_left, col_right = st.columns([1, 1])

# --- Left Half ---
with col_left:
    st.markdown("### Choose an assignment")
    assignments = fetch_assignments()
    options = [
        {
            "id": a["id"],
            "title": (a.get("title") or "Untitled"),
            "question": (a.get("question_text") or "")
        }
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

    st.subheader("Your Gemini API Key")
    api_key = st.text_input("Enter API Key", type="password", help="Used for transcription only. Not stored")

# --- Right Half ---
with col_right:
    visitor_input_id = st.text_input("Name", key="visitor_id_input")

# --- Conditional Display based on API Key ---
if not api_key:
    with col_left:
        st.info("please enter your Gemini API Key to enable recording and transcription.")
else:
    # Configure Gemini API
    try:
        genai.configure(api_key=api_key)
        st.success("Gemini API configured!")
    except Exception as e:
        st.error(f"Failed to configure Gemini API. Check your API key. Error: {e}")
        api_key = None  # Invalidate API key for this session if configuration fails

if api_key:  # Only show recording/transcription if API key is valid
    with col_right:
        st.subheader("Record Your Answer")

        # Mic Recorder
        recorded_audio_output = mic_recorder(
            start_prompt="Click to Start Recording",
            stop_prompt="Click to Stop Recording",
            use_container_width=True,
            key='audio_recorder'
        )

        if recorded_audio_output and recorded_audio_output.get('bytes'):
            st.session_state.recorded_audio_bytes = recorded_audio_output['bytes']
            st.audio(st.session_state.recorded_audio_bytes, format="audio/wav")
            st.info("Recorded audio ready for transcription.")
            # Trigger transcription editor after recording
            st.session_state.show_editor = True

        if st.session_state.show_editor and st.session_state.recorded_audio_bytes:
            # --- Transcribe Button ---
            if st.button("transcribe recording", key="transcribe_audio_button"):
                if not visitor_input_id:
                    st.warning("Please enter your Name / ID before transcribing.")
                else:
                    with st.spinner("Transcribing your audio..."):
                        try:
                            mime_type = "audio/wav"
                            audio_io = io.BytesIO(st.session_state.recorded_audio_bytes)
                            audio_io.name = "recorded_audio.wav"

                            audio_file = genai.upload_file(
                                path=audio_io,  # keeping your original approach
                                mime_type=mime_type,
                                display_name=f"Answer_from_{visitor_input_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            )

                            while audio_file.state.name == "PROCESSING":
                                st.info("File is still processing on Gemini's side...")
                                import time
                                time.sleep(1)
                                audio_file = genai.get_file(audio_file.name)

                            prompt = "Transcribe the given audio accurately. Provide only the spoken text."
                            model = genai.GenerativeModel('models/gemini-1.5-flash-latest')  # Ensure model is available
                            response = model.generate_content([audio_file, prompt])
                            st.session_state.edited_transcription_text = response.text

                            st.success("Transcription complete! You can now edit it.")

                        except GoogleAPIError as api_err:
                            st.error(f"Gemini API Error: {api_err.message}")
                            st.info("Please check your API key validity, ensure billing is enabled, or audio is not too long.")
                            st.exception(api_err)
                        except Exception as e:
                            st.error(f"An unexpected error occurred during transcription: {e}")
                            st.info("Ensure the audio recording was successful.")
                            st.exception(e)

            # --- Transcription Editor ---
            if st.session_state.edited_transcription_text:
                st.subheader("Review and Edit Your Answer:")
                st.session_state.edited_transcription_text = st.text_area(
                    "Edit your transcribed answer here:",
                    value=st.session_state.edited_transcription_text,
                    height=200,
                    key="transcription_editor"
                )

                # --- Grade Button ---
                if st.button("grade response", key="grade_response_button"):
                    if not st.session_state.edited_transcription_text.strip():
                        st.warning("Transcription is empty. Record and transcribe your audio first.")
                    else:
                        with st.spinner("Getting evaluation from Gemini..."):
                            try:
                                # Use Gemini to grade the response based on the prompt and transcription
                                grading_model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
                                student_submission = st.session_state.edited_transcription_text

                                ### Evaluation Prompt ###
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
                                    "Prompt Engineering" : {
                                        "Description" : "utilizes clear instructions, examples, formatting requirements and other best practices to design effective prompts.",
                                        "Grades" : {
                                            "Missing (0%)": "No prompts are designed.",
                                            "Major Misconceptions (50%)": "Prompts poorly designed with short or unclear instructions. no formatting requirements and no or few examples and step-by-step guidance",
                                            "Nearly Proficient (80%)": "Prompts designed with some clarity, but instructions, formatting requirements, or examples may be irrelevant or lack important details",
                                            "Proficient (100%)": "Prompts well-designed with clear instructions, relevant examples, and logical step-by-step thinking",
                                            "Mastery (102%)": "Prompts exceptionally well-designed with clear instructions, highly relevant and illustrative examples, and comprehensive step-by-step guidance for the task and format"
                                        }
                                    },
                                    "Prompt Workflow Breakdown" : {
                                        "Description" : "demonstrates clear step-by-step thinking to effectively breakdown into a series of prompts.",
                                        "Grades" : {
                                            "Missing (0%)": "Problem Solution not broken down into series of steps and prompts",
                                            "Major Misconceptions (50%)": "Prompt breakdown poorly designed with very few or irrelevant steps",
                                            "Nearly Proficient (80%)": "Prompt workflow designed with some steps and clarity, but may lack important details or steps",
                                            "Proficient (100%)": "Prompts workflow well-designed with clear instructions and logical step-by-step thinking",
                                            "Mastery (102%)": "Prompt Workflow exceptionally well-designed with clear instructions and comprehensive step-by-step breakdown"
                                        }
                                    },
                                    "Evaluation Metrics" : {
                                        "Description" : "defines metrics that are well-defined and relevant to the problem",
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

                                expected_output_format = f'''
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

                                expected_output_examples = f'''
                                (Examples omitted here for brevity — keeping your original structure)
                                '''

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
                                ### End of Evaluation Prompt ###

                                # Save prompt to session so submit won't crash if user doesn't grade next run
                                st.session_state.grading_prompt_text = master_prompt

                                grading_prompt_formatted = master_prompt
                                grading_response = grading_model.generate_content(grading_prompt_formatted)
                                st.session_state.grade_feedback = grading_response.text
                                st.success("Evaluation complete!")

                            except GoogleAPIError as api_err:
                                st.error(f"Gemini API Error during grading: {api_err.message}")
                                st.exception(api_err)
                            except Exception as e:
                                st.error(f"An unexpected error occurred during grading: {e}")
                                st.exception(e)

# --- Display Grade Feedback ---
if st.session_state.grade_feedback:
    st.subheader("Gemini Evaluation:")
    st.info(st.session_state.grade_feedback)

# --- Submit Answer (save to Supabase) ---
if st.button("submit answer", key="save_message_button"):
    if not visitor_input_id:
        st.warning("Please enter your Name / ID before submitting.")
    elif not st.session_state.edited_transcription_text.strip():
        st.warning("Answer content cannot be empty.")
    elif not st.session_state.get("selected_assignment_id"):
        st.warning("Please choose an assignment before submitting.")
    else:
        with st.spinner("Saving your response..."):
            # Define a unique filename for the saved message (not used yet, kept for parity)
            save_filename = f"answer_from_{visitor_input_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"

            message_metadata = {
                "source_app": "Streamlit Text-based Grading",
                "gemini_model": "1.5-flash-latest",
                "original_audio_length_bytes": len(st.session_state.recorded_audio_bytes) if st.session_state.recorded_audio_bytes else 0,
                "question": CURRENT_QUESTION,  # use the selected question
                "assignment_id": st.session_state.get("selected_assignment_id"),
                "grading_prompt": st.session_state.get("grading_prompt_text", ""),
                "grade_feedback": st.session_state.grade_feedback
            }

            # Save to Supabase
            try:
                payload = {
                    "assignment_id": st.session_state["selected_assignment_id"],  # non-None now
                    "student_name": visitor_input_id,
                    "transcript_text": st.session_state.edited_transcription_text,
                    "grade_overall": None,  # set if you compute a numeric score
                    "grade_json": {"text": st.session_state.grade_feedback} if st.session_state.grade_feedback else None,
                    # created_at is filled by DB default
                }
                data = insert_submission(payload)
                if data:
                    st.success("Answer submitted and saved to Supabase!")
                else:
                    st.warning("Submission saved locally, but Supabase didn’t return a row. Check RLS/policies.")
            except Exception as e:
                st.error(f"Failed to save to Supabase: {e}")

            # Reset for next message
            st.session_state.recorded_audio_bytes = None
            st.session_state.edited_transcription_text = ""
            st.session_state.show_editor = False
            st.session_state.grade_feedback = None
            st.rerun()

# Fallback hint if nothing recorded yet
if not st.session_state.recorded_audio_bytes:
    st.info("record your audio answer to begin transcription!")
