import streamlit as st
from ui_shared import create_admin_sidebar, create_student_view_button, render_admin_logout
from supabase_client import get_client

# Set page layout and background fix
st.set_page_config(page_title="Edit Grade", layout="wide")

# Shared sidebar
create_admin_sidebar()
create_student_view_button()
render_admin_logout()

# Background and theme style fix to match student side
st.markdown("""
<style>
/* Match Blossom student theme */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #2f2433 !important;
    color: #f2f2f2 !important;
    height: 100%;
    width: 100%;
    margin: 0;
    padding: 0;
}

/* Remove black header strip */
[data-testid="stHeader"] {
    background: transparent !important;
    height: 0 !important;
    border-bottom: none !important;
}

/* Input and textarea boxes */
div.stTextInput > div > div > input,
div.stTextArea > div > div > textarea {
    background-color: #5c4a5f;
    color: white;
    border: 1px solid #c49bb4;
    border-radius: 6px;
    padding: 10px;
    font-size: 16px;
}

textarea {
    min-height: 300px !important;
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


# =============================
# Main Content Logic
# =============================

if "edit_target" not in st.session_state:
    st.error("No student selected. Please go back to the dashboard.")
    st.stop()

target = st.session_state.edit_target

st.title(f"✏️ Edit Grade for {target['student_name']}")

st.markdown("### 📝 Full Transcript")
st.markdown(f"""
<div style='background-color:#5c4a5f;padding:10px;border-radius:8px;color:white;'>
{target['transcript_text']}
</div>
""", unsafe_allow_html=True)

st.markdown("### 📊 Grade Info")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Current Grade (Full Display):**")
    st.markdown(f"""
    <div style='background-color:#5c4a5f;padding:10px;border-radius:8px;color:white;min-height:300px;white-space:pre-wrap'>
    {target['grade']}
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("**Edit Grade:**")
    with st.form("grade_form"):
        new_grade = st.text_area("Update Grade (JSON or Summary):", value=str(target['grade']), height=300)
        submit = st.form_submit_button("💾 Save Grade")
        if submit:
            sb = get_client()
            try:
                sb.table("submissions").update({
                    "grade_json": new_grade
                }).eq("id", target["id"]).execute()
                st.session_state.edit_target['grade'] = new_grade  # update local session state
                st.success("Grade updated successfully.")
                st.rerun()  # refresh page to reflect change
            except Exception as e:
                st.error(f"Error updating grade: {e}")

