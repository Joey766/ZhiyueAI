"""Session State 初始化与页面跳转工具。"""
import streamlit as st
from uuid import uuid4


def new_record():
    return {"id": uuid4().hex}


def default_profile():
    return {
        "basic": {},
        "education": [new_record()],
        "experience": [new_record()],
        "projects": [new_record()],
        "skills": [],
        "application": {},
    }


def init_state():
    defaults = {
        "page": "首页", "profile_saved": False, "preferences_saved": False,
        "selected_job": None, "uploaded_resume_name": None,
        "profile": default_profile(), "preferences": {}, "expanded_job_id": None,
        "ai_job_analysis": None,
        "resume_parse_result": None, "resume_upload_nonce": 0,
        "real_jobs": [], "current_job_search": None, "application_job": None,
        "job_source_errors": [], "jobs_updated_at": None, "jobs_raw_count": 0,
        "job_refresh_token": 0, "custom_job_sources": [], "saved_jobs": [], "show_all_matching_jobs": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if st.session_state.page == "AI 申请助手":
        st.session_state.page = "岗位分析"


def go_to(page):
    st.session_state.page = page
    st.rerun()
