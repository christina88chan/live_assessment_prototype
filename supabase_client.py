from typing import List, Dict, Any
import streamlit as st
from supabase import create_client, Client

# ---------------------------
# Supabase Client Setup
# ---------------------------
def get_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)

# ---------------------------
# Submissions (Only Blossom)
# ---------------------------
def get_submissions() -> List[Dict[str, Any]]:
    """Return all student submissions for Blossom assignment."""
    sb = get_client()
    try:
        res = sb.table("submissions") \
            .select("id, student_name, transcript_text, grade_json, created_at") \
            .order("created_at", desc=True) \
            .execute()
        return res.data or []
    except Exception as e:
        st.error(f"Failed to fetch submissions: {e}")
        return []

def insert_submission(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    sb = get_client()
    res = sb.table("submissions").insert(payload).execute()
    return res.data or []
    
def get_all_submissions() -> List[Dict[str, Any]]:
    sb = get_client()
    res = sb.table("submissions").select("*").order("created_at", desc=True).execute()
    return res.data or []

# ---------------------------
# Assignment Editor (Optional)
# ---------------------------
def upsert_assignment(payload: Dict[str, Any]) -> Dict[str, Any]:
    """payload keys: id (optional), title, question_text, rubric_text"""
    sb = get_client()
    res = sb.table("assignments").upsert(payload).execute()
    return {"count": len(res.data or []), "data": res.data or []}

# ---------------------------
# Auth
# ---------------------------
def sign_up(email: str, password: str):
    sb = get_client()
    try:
        user = sb.auth.sign_up({"email": email, "password": password})
        return user
    except Exception as e:
        st.error(f"Registration failed: {e}")
        return None

def sign_in(email: str, password: str):
    sb = get_client()
    try:
        user = sb.auth.sign_in_with_password({"email": email, "password": password})
        return user
    except Exception as e:
        st.error(f"Login failed: {e}")
        return None

def sign_out():
    sb = get_client()
    try:
        sb.auth.sign_out()
        st.session_state.user_email = None
        st.rerun()
    except Exception as e:
        st.error(f"Logout failed: {e}")
