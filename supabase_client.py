from typing import List, Dict, Any
import streamlit as st
from supabase import create_client, Client

# Single place to create the client

def get_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)

# --- Convenience helpers ---

def list_assignments() -> List[Dict[str, Any]]:
    sb = get_client()
    res = sb.table("assignments").select("*").order("created_at", desc=True).execute()
    return res.data or []


def upsert_assignment(payload: Dict[str, Any]) -> Dict[str, Any]:
    """payload keys: id (optional), title, description, question_text, rubric_text, ai_prompt"""
    sb = get_client()
    res = sb.table("assignments").upsert(payload).execute()
    return {"count": len(res.data or []), "data": res.data or []}


def list_submissions(assignment_id: str) -> List[Dict[str, Any]]:
    sb = get_client()
    res = (
        sb.table("submissions")
        .select("id, student_name, transcript_text, grade_overall, created_at")
        .eq("assignment_id", assignment_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


def insert_submission(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    sb = get_client()
    res = sb.table("submissions").insert(payload).execute()
    return res.data or []
    
def assignment_summaries() -> List[Dict[str, Any]]:
    """Returns [{id, title, created_at, avg_grade, submissions_count}]"""
    import statistics
    a = list_assignments()
    if not a:
        return []
    sb = get_client()
    # Pull all submissions once to avoid N queries
    s = sb.table("submissions").select("assignment_id, grade_overall, created_at").execute().data or []
    by_id = {}
    for row in a:
        by_id[row["id"]] = {
            "id": row["id"],
            "title": row.get("title"),
            "created_at": row.get("created_at"),
            "avg_grade": None,
            "submissions_count": 0,
        }
    for sub in s:
        aid = sub["assignment_id"]
        if aid in by_id:
            info = by_id[aid]
            info.setdefault("grades", []).append(sub.get("grade_overall"))
    for aid, info in by_id.items():
        grades = [g for g in info.get("grades", []) if isinstance(g, (int, float))]
        info["submissions_count"] = len(grades)
        info["avg_grade"] = round(sum(grades) / len(grades), 2) if grades else None
        info.pop("grades", None)
    return list(by_id.values())
