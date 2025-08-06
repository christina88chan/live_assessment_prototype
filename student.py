import streamlit as st
import google.generativeai as genai
import io
import os
from streamlit_mic_recorder import mic_recorder
from google.api_core.exceptions import GoogleAPIError
from datetime import datetime
import json

def create_admin_view_button():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col3:
        if st.button("Admin Login"):
            st.switch_page("pages/admin_home.py")

st.header("Tech4Good Live Assessment Tool")
create_admin_view_button()


### code copy pasted from Aashna's streamlit demo: ###

st.set_page_config(page_title="Live Assessment Tool", layout="centered")

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
<div  
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


# --- Hardcoded Question ---
HARDCODED_QUESTION = """Explain your initial thoughts to the assessment question here"""

# --- Layout Start ---
col_left, col_right = st.columns([1, 1])

# --- Left Half --- 
with col_left: 
    
    st.markdown("### Question:")
    st.info(HARDCODED_QUESTION)
    st.subheader("Your Gemini API Key")
    api_key = st.text_input("Enter API Key", type="password", help="Used for transcription only. Not stored")
#st.subheader("Question:")
#st.info(HARDCODED_QUESTION)

# ---Right Half ---
with col_right:
    visitor_input_id = st.text_input("Name", key="visitor_id_input")
  
    

# --- Core App Logic ---
# Visitor ID Input
#visitor_input_id = st.text_input("Name:", key="visitor_id_input")

# Gemini API Key Input
#st.subheader("your Gemini API key")
#api_key = st.text_input(
    #"enter your Gemini API Key:",
    #type="password",
   #help="This key is used only for your message transcription and is not stored.",
   # key="gemini_api_key_input"
#)


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
        api_key = None # Invalidate API key for this session if configuration fails

if api_key: # Only show recording/transcription if API key is valid
    with col_right:
        st.subheader("Record Your Answer")

    # Mic Recorder
        recorded_audio_output = mic_recorder(
            start_prompt="Click to Start Recording",
            stop_prompt="Click to Stop Recording",
            use_container_width=True,
            key='audio_recorder'
        )

        if recorded_audio_output and recorded_audio_output['bytes']:
            st.session_state.recorded_audio_bytes = recorded_audio_output['bytes']
            st.audio(st.session_state.recorded_audio_bytes, format="audio/wav")
            st.info("Recorded audio ready for transcription.")
        # Trigger transcription immediately after recording is done
            st.session_state.show_editor = True # Show editor after recording


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
                                path=audio_io,
                                mime_type=mime_type,
                                display_name=f"Answer_from_{visitor_input_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            )

                            while audio_file.state.name == "PROCESSING":
                                st.info("File is still processing on Gemini's side...")
                                import time
                                time.sleep(1)
                                audio_file = genai.get_file(audio_file.name)

                            prompt = "Transcribe the given audio accurately. Provide only the spoken text."
                            model = genai.GenerativeModel('models/gemini-1.5-flash-latest') # Ensure model is available
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
                                student_submission=st.session_state.edited_transcription_text
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

                                Examples:
                                Concept: "Prompt Engineering"
                                Grade: Nearly Proficient
                                Reasoning: The student reflected on how their prompt needs to be detailed and the details it should include. But they did not mention any plan to use strong prompting techniques like adding an example or formatting instructions to design their prompts.

                                Concept: "Prompt Engineering"
                                Grade: Missing
                                Reasoning: The student's reflection does not mention anything about prompt design or how they plan to structure their prompts. They focus only on the end goal without considering how to effectively communicate with the LLM.

                                Concept: "Prompt Engineering"
                                Grade: Major Misconceptions
                                Reasoning: The student mentions wanting to "tell the AI what to do" but shows limited understanding of prompt design principles. Their reflection lacks any consideration of prompt structure, clarity, or techniques beyond basic instruction-giving.

                                Concept: "Prompt Engineering"
                                Grade: Nearly Proficient
                                Reasoning: The student demonstrates understanding that prompts need to be detailed and mentions planning to iterate on prompts based on results. However, their reflection lacks discussion of specific prompt engineering techniques like including examples, formatting requirements, or step-by-step instructions in their initial planning.

                                Concept: "Prompt Engineering"
                                Grade: Nearly Proficient
                                Reasoning: The student understands the importance of clear communication with the LLM and plans to be specific in their instructions. However, their reflection focuses mainly on content rather than considering prompt structure, formatting techniques, or the use of examples to guide the model's responses.

                                Concept: "Prompt Engineering"
                                Grade: Proficient
                                Reasoning: The student shows clear understanding of prompt design principles, mentioning plans to include clear instructions, provide examples, and structure their prompts with specific formatting. They demonstrate awareness of iterative refinement and the importance of prompt clarity.

                                Concept: "Prompt Engineering"
                                Grade: Mastery
                                Reasoning: The student demonstrates exceptional understanding of prompt engineering, discussing plans to use multiple techniques including examples, step-by-step guidance, output formatting, and context setting. They show sophisticated thinking about prompt optimization and mention specific strategies for different types of tasks.

                            Concept: "Prompt Workflow"
                            Grade: Missing
                            Reasoning: The student treats the problem as a single task without any consideration of breaking it down into smaller, manageable steps. Their reflection shows no awareness of workflow design or sequential processing.

                            Concept: "Prompt Workflow"
                            Grade: Major Misconceptions
                            Reasoning: The student mentions wanting to solve the problem but shows minimal understanding of workflow design. They identify only one or two very broad steps without considering how outputs from one step feed into the next.

                            Concept: "Prompt Workflow"
                            Grade: Major Misconceptions
                            Reasoning: The student recognizes that the problem is complex but their planned approach jumps directly to implementation without adequate decomposition. They show some awareness of multiple components but lack systematic thinking about how to sequence and connect these elements.

                            Concept: "Prompt Workflow"
                            Grade: Nearly Proficient
                            Reasoning: The student shows understanding that the task should be broken into steps and identifies several logical phases. However, their reflection lacks detail about how these steps connect or how they plan to handle dependencies between different parts of the workflow.

                            Concept: "Prompt Workflow"
                            Grade: Proficient
                            Reasoning: The student demonstrates clear thinking about workflow design, identifying logical steps and explaining how outputs from one stage inform the next. They show understanding of sequential processing and the rationale behind their chosen breakdown.

                            Concept: "Prompt Workflow"
                            Grade: Mastery
                            Reasoning: The student shows sophisticated understanding of workflow design, identifying not only the main steps but also considering edge cases, error handling, and alternative pathways. They demonstrate comprehensive thinking about how different components interact and feed into each other.

                            Concept: "Evaluation Metrics"
                            Grade: Missing
                            Reasoning: The student's reflection contains no mention of how they plan to evaluate their results or measure success. They focus entirely on the generation process without considering assessment of quality or effectiveness.

                            Concept: "Evaluation Metrics"
                            Grade: Major Misconceptions
                            Reasoning: The student mentions wanting to check if results are "good" but provides no specific metrics or criteria for evaluation. Their approach to assessment is vague and not actionable for systematic evaluation.

                            Concept: "Evaluation Metrics"
                            Grade: Nearly Proficient
                            Reasoning: The student identifies some relevant evaluation criteria such as accuracy or relevance but their metrics lack specificity and measurability. They show awareness of the need for evaluation but haven't fully developed concrete assessment methods.

                            Concept: "Evaluation Metrics"
                            Grade: Proficient
                            Reasoning: The student demonstrates good understanding of evaluation by identifying specific, measurable metrics relevant to the problem context. They show clear thinking about what constitutes success and how to systematically assess their outputs.

                            Concept: "Evaluation Metrics"
                            Grade: Proficient
                            Reasoning: The student thoughtfully considers multiple dimensions of quality including relevance, completeness, and usability. They demonstrate clear thinking about what makes a good bingo square and how to measure whether their approach achieves the intended connection-facilitating goals.

                            Concept: "Evaluation Metrics"
                            Grade: Mastery
                            Reasoning: The student shows exceptional understanding of evaluation design, proposing multiple complementary metrics that cover different aspects of quality. They demonstrate sophisticated thinking about both automated and manual evaluation methods, and consider how metrics relate to the problem's ultimate goals.
                            '''

                                expected_output_examples = f'''
                            Student Submission Example 1:
                            "These 2 prompts iterate off of the initial extraction of the themes. Instead of having to cross reference all the raw data in one prompt, it can simply use the themes and subthemes that are already specified with connections. This way it doesn’t have to run for as long and lowers the risk of hallucination since it already has the data it needs.  For evaluation I would ensure that the number of squares are met and the connections it has created between users is real. I would also search for relevance within the themes to ensure that the initial prompt is not messing up the others."

                            Your output for Submission 1:
                            "Concept: Prompt Engineering
                            Grade: Major Misconcception
                            Reasoning: The student mentions iterative prompt design and reducing hallucination risk by providing pre-processed data to the LLM.  This shows some understanding of prompt engineering principles. However, the reflection lacks detail on the initial prompt structure, specific techniques used (e.g., examples, formatting), and how they plan to refine prompts based on results beyond simply iterating.  There's no mention of best practices like clear instructions or step-by-step guidance within the prompts themselves.

                            Concept: Prompt Workflow Breakdown
                            Grade: Missing
                            Reasoning:The student identifies a key step of pre-processing themes to improve efficiency and reduce errors. This indicates some understanding of breaking down the task into smaller prompts. However, the description of the workflow is quite high-level.  There's no detailed breakdown of the steps involved in generating the different types of squares (general and personalized),  the process for matching participants to themes, or the specific prompt sequence used. The workflow lacks the necessary level of detail to be considered proficient.


                            Concept: Evaluation Metrics
                            Grade: Nearly Proficient
                            Reasoning:The student suggests checking the number of generated squares and the accuracy of the connections, which are relevant metrics. However, the evaluation is lacking in detail. "Real connections" isn't a clearly defined or measurable metric.  Checking for relevance is mentioned but lacks specific criteria. The student needs to define more concrete and measurable metrics for assessing the quality of the generated bingo squares (e.g., how will they measure relevance?).  While the student attempts to identify metrics, the lack of specificity prevents a higher grade."


                            Student Submission Example 2:
                            "Initial Thoughts on Breaking Down the Task
                            Data Analysis Phase:
                            First, extract and categorize all the passions/experiences mentioned by participants
                            Identify which interests are shared by many participants (for the majority squares)
                            Identify niche interests shared by only 1-2 participants (for minority squares)
                            Create a mapping of participants to their interests for easy reference
                            Square Generation Phase:
                            Develop prompts for generating the general squares (both majority and minority)
                            Develop prompts for generating personalized squares for each participant
                            Ensure diversity in topics and engaging language in the squares
                            Evaluation Phase:
                            Test the generated squares against our metrics
                            Iterate on prompts based on results
                            Initial Prompt Design
                            Let me propose an initial prompt structure for the theme extraction part:
                            You are an expert in analyzing survey data and identifying themes. I have responses from 29 participants about their passions and experiences they'd like to connect with others over.

                            Your task is to:
                            1. Analyze all responses and identify distinct themes or categories
                            2. For each theme, list which participants mentioned it
                            3. Classify themes as "majority" (mentioned by many participants) or "minority" (mentioned by only 1-2 participants)
                            4. Ensure a diverse range of themes across different domains (academic, hobby, entertainment, etc.)

                            Here are the participant responses:
                            [Insert participant data]

                            Output your analysis in the following format:
                            THEME: [Name of theme]
                            TYPE: [Majority/Minority]
                            PARTICIPANTS: [List of participant IDs]
                            SAMPLE QUOTES: [Brief excerpts from responses]
                            Iteration Plans
                            After running the initial prompt, I would plan to:
                            Review the themes identified
                            Create a prompt for generating engaging bingo square text based on these themes
                            Test with a few participants to see how well the personalized squares work
                            Adjust the prompts based on the quality of outputs
                            Evaluation Metrics (Expanded)
                            Topic Diversity:
                            Are the general squares covering different domains (academic, creative, social, etc.)?
                            Scale: 1-5, where 5 means excellent diversity across domains
                            Accuracy of Matching:
                            Do the squares correctly match participants to their stated interests?
                            Can we verify that the majority squares truly represent common interests?
                            Scale: % of participants correctly matched to their interests
                            Connection Potential:
                            How likely is each square to facilitate meaningful interaction?
                            Are the prompts specific enough to start a conversation?
                            Scale: 1-5, where 5 means high potential for meaningful connection
                            Clarity and Appeal:
                            Are the squares written in clear, engaging language?
                            Would participants understand what each square is asking for?
                            Scale: 1-5, where 5 means very clear and appealing"

                            Your output for Submission 2:
                            "
                            Concept: Prompt Engineering
                            Grade: Proficient
                            Reasoning: The student provides a well-structured initial prompt designed to extract themes from participant survey data.  The prompt includes clear instructions, specifies the desired output format, and requests categorization of themes. While not explicitly mentioned, the plan to iterate and test with participants suggests an understanding of iterative refinement. The inclusion of  "SAMPLE QUOTES" in the desired output shows awareness of using examples for better model output.  However, it lacks explicit mention of more advanced techniques like few-shot learning or specific formatting instructions beyond the basic outline provided.


                            Concept: Prompt Workflow Breakdown
                            Grade: Proficient
                            Reasoning: The student breaks down the task into three logical phases: Data Analysis, Square Generation, and Evaluation. Each phase contains relevant sub-steps, demonstrating a clear understanding of sequential processing. The plan to iterate based on results further enhances the workflow's effectiveness.  The steps are well-defined and logically sequenced, though  more detail on handling potential issues or variations in the data could elevate it to Mastery.


                            Concept: Evaluation Metrics
                            Grade: Proficient
                            Reasoning: The student defines multiple relevant metrics: Topic Diversity, Accuracy of Matching, Connection Potential, and Clarity and Appeal. Each metric is measurable (using scales or percentages) and directly addresses the problem's goals. The metrics cover different aspects of output quality, ensuring a comprehensive assessment. While the scales are somewhat basic, the metrics are well-chosen and applicable, making them suitable for evaluating the success of the prompt engineering workflow.
                            "

                            Student Submission Example 3:
                            "
                            Asking it to generate 6 squares that follow  the  data given,
                            Major: with 3 of the squares being shared topics by many of the participants ( to help make connections with each other)
                            Minior: While the other 3 squares will only follow a smaller range of shared topics, only shared with 1-2 participants.
                            Ensuring all of these generated squares have a diverse topic outputted.
                            With the other 3 squares, they should be personalized for that said participant, starting with only A generating 9 total squares, then using the same type of layout for those squares, generating for B, C, D, for example.
                            "

                            Your output for Submission 3:
                            "
                            Concept: Prompt Engineering
                            Grade: Nearly Proficient
                            Reasoning:The student's reflection shows an understanding of the need for clear instructions in their prompts (e.g., specifying the number and type of squares). However, it lacks detail on specific prompt engineering techniques.  There's no mention of using examples, formatting requirements, or iterative refinement strategies in their initial prompt design. The plan to generate for participants A, B, C, D sequentially suggests a basic understanding of iterative prompting, but lacks the sophistication of using previous outputs to inform subsequent prompts.


                            Concept: Prompt Workflow Breakdown
                            Grade: Nearly Proficient
                            Reasoning:The student outlines a workflow: generating general squares, then personalized squares.  This shows some understanding of breaking down the problem into steps. However, the description lacks detail on how the process will be managed. For instance, it's unclear how the "data" will be used to generate the squares or how the model's output at each step will be utilized for subsequent steps. There's a mention of using the same "layout" for each participant, which hints at some form of workflow, but isn't fully fleshed out.


                            Concept: Evaluation Metrics
                            Grade: Missing
                            Reasoning:The student's reflection does not define any metrics for evaluating the quality of the generated bingo squares.  While the goal of generating diverse topics is mentioned, there are no concrete or measurable metrics to assess whether this goal was achieved or whether the overall output is successful.  The reflection completely omits crucial elements of an evaluation strategy.
                            "
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


            if st.button("submit answer", key="save_message_button"):
                if not visitor_input_id:
                    st.warning("Please enter your Name / ID before submitting.")
                elif not st.session_state.edited_transcription_text.strip():
                    st.warning("Answer content cannot be empty.")
                else:
                    with st.spinner("Saving your response..."):
                        # Define a unique filename for the saved message
                        save_filename = f"answer_from_{visitor_input_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                        message_metadata = {
                            "source_app": "Streamlit Text-based Grading",
                            "gemini_model": "1.5-flash-latest",
                            "original_audio_length_bytes": len(st.session_state.recorded_audio_bytes) if st.session_state.recorded_audio_bytes else 0,
                            "question": HARDCODED_QUESTION, # Include the hardcoded question
                            "grading_prompt": master_prompt,
                            "grade_feedback": st.session_state.grade_feedback
                        }
                        # Placeholder for saving the answer and question
                        # save_answer(visitor_input_id, HARDCODED_QUESTION, st.session_state.edited_transcription_text, save_filename, message_metadata)
                        st.success("Answer submitted!")

                        # Reset for next message
                        st.session_state.recorded_audio_bytes = None
                        st.session_state.edited_transcription_text = ""
                        st.session_state.show_editor = False
                        st.session_state.grade_feedback = None
                        st.rerun() # Rerun to clear forms for a new message
        else:
            st.info("record your audio answer to begin transcription!")
