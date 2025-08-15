import streamlit as st
import google.generativeai as genai
import io
import os
from streamlit_mic_recorder import mic_recorder
from google.api_core.exceptions import GoogleAPIError
from datetime import datetime
import json
from supabase_client import insert_submission

# Streamlit needs this BEFORE any UI calls
st.set_page_config(page_title="Blossom Assessment - Assessment", layout="wide")

header_col, button_col = st.columns([8, 1])
with header_col:
    st.header("Blossom Assessment")
with button_col:
    if st.session_state.get("is_admin_logged_in"):
        if st.button("Return to Admin Home"):
            st.switch_page("pages/admin_home.py")
    else:
        if st.button("Log Out"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.switch_page("student_login.py")
            st.rerun()

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

def _uk(base: str) -> str:
    """Unique widget keys per user to avoid collisions."""
    return f"{base}_{st.session_state.get('visitor_id_input') or 'anon'}"

def _submit_answer():
    if not st.session_state.get("visitor_id_input"):
        st.warning("Please enter your Name / ID before submitting.")
        return
    if not st.session_state.student_prompt_text.strip():
        st.warning("Final prompt cannot be empty.")
        return

    with st.spinner("Saving your response..."):
        try:
            payload = {
                "student_name": st.session_state.get("visitor_id_input"),
                "transcript_text": st.session_state.edited_transcription_text,
                "student_prompt": st.session_state.student_prompt_text,
                "grade_json": {"text": st.session_state.grade_feedback} if st.session_state.grade_feedback else None,
            }
            data = insert_submission(payload)
            if data:
                st.success("Answer submitted and saved to Supabase!")
            else:
                st.warning("Submission saved locally, but Supabase didn’t return a row. Check RLS/policies.")
        except Exception as e:
            st.error(f"Failed to save to Supabase: {e}")

        # Reset
        st.session_state.recorded_audio_bytes = None
        st.session_state.edited_transcription_text = ""
        st.session_state.student_prompt_text = ""
        st.session_state.show_editor = False
        st.session_state.grade_feedback = None
        st.rerun()


# ---------- Layout ----------
col_left, col_right = st.columns([3, 3])

# ----- Left: assignment & question -----
with col_left:
    with st.container():
        st.subheader("1. Read the Assessment Document")

        google_doc_url = "https://docs.google.com/document/d/1NZ5R_MOlGGjB58Ynw7AtfwR7lsapZGhP6Dux7JwHnVQ/edit?usp=sharing"
    
        # Embed the Google Doc in an iframe
        st.markdown(f"""
        <iframe src="{google_doc_url}" width="100%" height="700px" frameborder="0">
        </iframe>
        """, unsafe_allow_html=True)

    
        
    
# ----- Right: name, API key, tabs -----
with col_right:
    st.subheader("2. Key Concepts")
    st.markdown("""
        1. **Prompt Engineering**
        2. **Prompt Workflows**
        3. **Evaluation Metrics**
        """)

    st.subheader("3. Record Your Response")
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

    st.subheader("4. Transcribe Your Response")
    if st.button("Transcribe Recording"):
        with st.spinner("Transcribing your audio..."):
            try:
                mime_type = "audio/wav"
                audio_io = io.BytesIO(st.session_state.recorded_audio_bytes)
                audio_file = genai.upload_file(
                    path=audio_io,
                    mime_type=mime_type,
                )

                # Poll until processed
                while getattr(audio_file, "state", None) and getattr(audio_file.state, "name", "") == "PROCESSING":
                    st.info("File is still processing on Gemini's side...")
                    import time
                    time.sleep(1)
                    audio_file = genai.get_file(audio_file.name)
                
                prompt = "Transcribe the given audio accurately. Provide only the spoken text."
                model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
                response = model.generate_content([audio_file, prompt])
                transcription_text = response.text or ""

                # Debugging: Check what is returned from the API
                # Check if this is populated

                st.session_state.edited_transcription_text = transcription_text
                

            except GoogleAPIError as api_err:
                st.error(f"Gemini API Error: {api_err.message}")
                st.info("Please check your API key validity, ensure billing is enabled, or audio is not too long.")
                st.exception(api_err)
            except Exception as e:
                st.error(f"An unexpected error occurred during transcription: {e}")
                st.info("Ensure the audio recording was successful.")
                st.exception(e)
                               
           # Editor for transcription (thoughts)
    if st.session_state.edited_transcription_text:
        st.info("Edit the transcription text below as needed")
        st.session_state.edited_transcription_text = st.text_area(
            "Edit your transcribed thoughts here:",
            value=st.session_state.edited_transcription_text,  # Text to edit
            height=200,
            key="transcription_editor"
        )
    

        # Student's final prompt input
    
    st.subheader("5. Prompt")          
    st.session_state.student_prompt_text = st.text_area(
        "Write your initial prompt here:",
        value=st.session_state.student_prompt_text,
        height=250,
        placeholder="Enter your final prompt or solution here...",
        key="student_prompt_editor"
    )


           # Grade button and submit button
    col_grade, col_submit = st.columns(2)
          
    with col_grade:
        if st.button("Grade Response", key=_uk("grade_response_button")):
            if not st.session_state.student_prompt_text.strip():
                st.warning("Final prompt is empty. Please enter your final prompt first.")
            else:
                with st.spinner("Getting evaluation from Gemini..."):
                    try:
                        grading_model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
                              
                        student_thoughts = st.session_state.edited_transcription_text
                        student_final_prompt = st.session_state.student_prompt_text


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
                               â€¢ a brief outline of initial thoughts about how they might break down the task,
                               â€¢ discussion of how they created and initial prompt how they plan to iterate on it next based on results,
                               â€¢ initial thoughts on evaluation metrics they will use to evaluate results of their prompts.'''


                        purpose = f'''You are a Teaching Assistant and you will be evaluating student submissions based on a given rubric. Students are taking part in a {course_name} course to {course_goals}. This includes learning the key concepts of {key_concepts}. If a students submission does not include anything to grade (empty submission) then provide 0s for all the concepts and say missing submission for the reasoning since every student still requires a grade.'''


                        assessment_details = f'''Students were given an assessment where they had to solve a complex problem to test their understanding of {key_concepts}.
                               Students were required to submit both their initial thoughts/reflections on how they plan to tackle the problem AND their final prompt/solution.
                               {assessment_reflection_instructions}'''


                        model_instructions = ''' Your task is to evaluate both the student's initial thoughts/reflections AND their final prompt/solution to assess their understanding of key concepts given in the rubric below. Consider both components when grading: '''


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


                        expected_output_examples = '(Examples omitted here for brevity â€" keeping your original structure)'


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
                              
                        STUDENT'S INITIAL THOUGHTS/REFLECTIONS:
                        {student_thoughts}


                        STUDENT'S FINAL PROMPT/SOLUTION:
                        {student_final_prompt}
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


    with col_submit:
        if st.button("Submit Answer", key=_uk("save_message_button")):
            if not st.session_state.student_prompt_text.strip():
                st.warning("Final prompt cannot be empty.")
            else:
                 with st.spinner("Saving your response..."):
                    try:
                        payload = {
                        "student_name": st.session_state.get("visitor_id_input"),
                        "transcript_text": st.session_state.edited_transcription_text,
                        "student_prompt": st.session_state.student_prompt_text,
                        "grade_json": {"text": st.session_state.grade_feedback} if st.session_state.grade_feedback else None,
                        }
                        data = insert_submission(payload)
                        if data:
                            st.success("Answer submitted and saved to Supabase!")
                        else:
                            st.warning("Submission saved locally, but Supabase did not return a row. Check RLS/policies.")
                    except Exception as e:
                        st.error(f"Failed to save to Supabase: {e}")


# ---------- Grade feedback ----------
if st.session_state.grade_feedback:
   st.subheader("Gemini Evaluation:")
   st.info(st.session_state.grade_feedback)







   



      