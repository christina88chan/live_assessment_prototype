import streamlit as st
from pages.admin_home import create_admin_sidebar, create_student_view_button # Import the functions

# Initialize session state for rubric and prompt if they don't exist
if 'rubric_content' not in st.session_state:
    st.session_state.rubric_content = ""

if 'ai_prompt' not in st.session_state:
    st.session_state.ai_prompt = ""

# Display the page content
st.header("Admin Edits")

# Create the navigation elements by calling the imported functions
create_admin_sidebar()
create_student_view_button()

# Add some spacing
st.markdown("---")

# Main content area for rubric and prompt management
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 Assessment Rubric")
    
    # Rubric editing section
    with st.expander("Edit Rubric", expanded=True):
        rubric_input = st.text_area(
            "Rubric Content",
            value=st.session_state.rubric_content,
            height=400,
            placeholder="Enter your assessment rubric here. You can use markdown formatting for better presentation.",
            help="Define your assessment criteria and scoring guidelines.",
            key="rubric_textarea"
        )
        
        col1_1, col1_2 = st.columns([1, 1])
        
        with col1_1:
            if st.button("💾 Save Rubric", type="primary"):
                st.session_state.rubric_content = rubric_input
                st.success("✅ Rubric saved successfully!")
                st.rerun()
        
        with col1_2:
            if st.button("🗑️ Clear Rubric"):
                st.session_state.rubric_content = ""
                st.success("🗑️ Rubric cleared!")
                st.rerun()
    
    # Rubric preview section
    with st.expander("Preview Rubric", expanded=False):
        if st.session_state.rubric_content:
            st.markdown(st.session_state.rubric_content)
        else:
            st.info("No rubric content to preview. Enter your rubric above to see the preview.")

with col2:
    st.subheader("🤖 AI Assessment Prompt")
    
    # AI Prompt editing section
    with st.expander("Edit AI Prompt", expanded=True):
        prompt_input = st.text_area(
            "AI Prompt Content",
            value=st.session_state.ai_prompt,
            height=400,
            placeholder="Configure how the AI should assess student submissions based on your rubric. Be specific about the format and tone you want.",
            help="Define instructions for the AI to follow when assessing student work.",
            key="prompt_textarea"
        )
        
        col2_1, col2_2 = st.columns([1, 1])
        
        with col2_1:
            if st.button("💾 Save Prompt", type="primary"):
                st.session_state.ai_prompt = prompt_input
                st.success("✅ AI Prompt saved successfully!")
                st.rerun()
        
        with col2_2:
            if st.button("🗑️ Clear Prompt"):
                st.session_state.ai_prompt = ""
                st.success("🗑️ AI Prompt cleared!")
                st.rerun()
    
    # AI Prompt preview section
    with st.expander("Preview AI Prompt", expanded=False):
        if st.session_state.ai_prompt:
            st.text(st.session_state.ai_prompt)
        else:
            st.info("No AI prompt content to preview. Enter your prompt above to see the preview.")