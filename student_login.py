import streamlit as st
import google.generativeai as genai

# Streamlit needs this BEFORE any UI calls
st.set_page_config(page_title="Blossom Assessment - Login", layout="wide")

header_col, admin_col = st.columns([8, 1])
with header_col: 
    st.header("Blossom Assessment - Student View")
with admin_col:
    if st.button("Admin Login"):
        st.switch_page("pages/auth.py")


# ---------- Styles ----------
st.markdown("""
<style>
/* Full screen layout */
.stApp {
    height: 100vh;  /* Ensures full height of the screen */
    margin: 0;
    display: flex;
    flex-direction: column;
}

/* Ensure that app container takes up the full screen */
[data-testid="stAppViewContainer"] {
    flex: 1;
    display: flex;
    flex-direction: column;
}

/* Make Streamlit's top header transparent so it doesn't look like a black bar */
[data-testid="stHeader"] {
  background: transparent !important;
  backdrop-filter: none !important;
  border-bottom: none !important;
}

/* Main app background color */
.stApp {
    background-color: #3a2c3f;
    color: #f2f2f2;
}

/* Adjust font color */
.stMarkdown, .stText, .stDataFrame, .stTable, .stSelectbox, .stButton {
    color: #f2f2f2 !important;
}

/* Input fields styling */
div.stTextInput > div > div > input,
div.stTextArea > div > div > textarea,
div.stNumberInput > div > div > input {
    background-color: #5c4a5f;
    color: #ffffff;
    border: 1px solid #c49bb4;
    border-radius: 6px;
    padding: 10px;
}

/* Buttons styling */
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

/* Right Column Box */
.col_right_border {
    border: 2px solid #c49bb4;
    border-radius: 10px;
    padding: 20px;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ---------- Session State ----------
if 'api_key_set' not in st.session_state:
    st.session_state.api_key_set = ""   # "", "ok", or "error: ..."
if 'api_key_value' not in st.session_state:
    st.session_state.api_key_value = ""
if 'api_key_status' not in st.session_state:
    st.session_state.api_key_status = ""   # "", "ok", or "error: ..."

def _uk(base: str) -> str:
    """Unique widget keys per assignment + user to avoid collisions."""
    return f"{base}_{st.session_state.get('selected_assignment_id') or 'na'}_{st.session_state.get('visitor_id_input') or 'anon'}"


# ---------- Layout with adjusted column sizes ----------
col_left, col_right = st.columns([3, 4])  # Adjusted to make the right column wider

# Left Column: Input form for student information
with col_left:
    st.subheader("Fill in the information below to begin your assessment.")
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    api_key = st.text_input("API Key", type="password")

    # Checkbox for affirmation
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
                    # Configure Gemini API
                    genai.configure(api_key=api_key)
                    st.session_state.api_key_set = True
                    st.session_state.api_key_value = api_key
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
    # If API key is already set
    c_label, c_change = st.columns([2, 1])
    with c_label:
        st.success("Gemini API configured.")
    with c_change:
        if st.button("Change API Key", key="api_key_change"):
            st.session_state.api_key_set = False
            st.session_state.api_key_value = ""
            st.session_state.api_key_status = ""
            st.experimental_rerun()

# ---------- Button to Begin and Store Session Data ----------
if st.button("Click to begin"):
    if first_name and last_name and api_key and affirmation:
        # Store session data
        st.session_state.first_name = first_name
        st.session_state.last_name = last_name
        st.session_state.api_key = api_key
        st.session_state.api_key_set = True  # API key is set
        st.experimental_rerun()
    else:
        st.warning("Please fill in all fields and check the affirmation.")

# Right Column: Welcome message and instruction
with col_right:
    st.markdown('<div class="col_right_border">', unsafe_allow_html=True)
    st.markdown('<div class="col_right_box_content">', unsafe_allow_html=True)  
    st.subheader("Welcome to your assessment")
    st.markdown("""
        Once you have logged in, a timer will begin and you will have **1 hour** to complete this assessment. 
        You will have the opportunity to read over the assessment and record your response using a microphone. 
        Once **submit** is pressed, the assignment will be evaluated and sent to the instructor.
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
