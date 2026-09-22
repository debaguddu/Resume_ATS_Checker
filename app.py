"""Resume ATS Checker - Enterprise RAG & AI Career Suite.

Main Application Entrypoint & Executive Dashboard.
"""

import sys
from pathlib import Path

# Ensure src package is importable
src_path = str(Path(__file__).resolve().parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import streamlit as st
from resume_ats_checker.config import get_settings
from resume_ats_checker.database.connection import check_connection, init_db
from resume_ats_checker.database.repository import get_recent_evaluations
from resume_ats_checker.ui.styles import apply_custom_styles
from resume_ats_checker.ui.components import render_header

# Streamlit Page Configuration
st.set_page_config(
    page_title="AI Resume ATS Suite",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_custom_styles()
settings = get_settings()

# Initialize DB on first launch
if "db_initialized" not in st.session_state:
    success, msg = init_db()
    st.session_state["db_initialized"] = success
    st.session_state["db_init_msg"] = msg

# Render Hero Header
render_header(
    title="🎯 Enterprise AI Resume ATS Suite",
    subtitle="Semantic RAG analysis, ATS score auditing, tailored resume reconstruction, and executive cover letter generator powered by LangChain, OpenAI, and PostgreSQL.",
)

# Sidebar System Health & Navigation
with st.sidebar:
    st.title("⚙️ System Status")

    # DB Status
    db_ok, db_msg = check_connection()
    if db_ok:
        st.success("🟢 PostgreSQL: Connected (Port 5432)")
    else:
        st.error(f"🔴 PostgreSQL: Disconnected ({db_msg[:35]}...)")
        st.caption("Check your .env settings or local PostgreSQL service.")

    # OpenAI Status
    if settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here":
        st.success(f"🟢 OpenAI: Active ({settings.openai_model})")
    else:
        st.warning("🟡 OpenAI: API Key Not Set")
        st.caption("Please configure `OPENAI_API_KEY` in `.env`.")

    st.divider()
    st.markdown("### 🧭 Available Modules")
    st.markdown(
        """
        - **[🎯 ATS Checker & Matcher](ATS_Checker)**: Upload PDF/DOCX/PPTX, match against JD, view score, get suggestions, and rewrite.
        - **[📝 Resume Builder & Templates](Resume_Builder)**: Future-ready template studio with data & photo placeholders and export tools.
        - **[💼 Job Match Finder](Job_Match_Finder)**: Discover live web jobs across LinkedIn, Indeed, Glassdoor via Tavily and rank by semantic ATS match.
        """
    )
    st.divider()
    st.caption("Resume ATS Suite v0.1.0 • Powered by LangChain & PostgreSQL")

# Main Dashboard View
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("⚡ Quick Start Workflow")
    st.markdown(
        """
        1. **Upload Resume**: Multi-format support for **PDF**, **DOCX**, and **PPTX** presentations.
        2. **Paste Job Description**: Provide the target role or paste complete job specs.
        3. **RAG Vector Analysis**: Semantic similarity matching across skills, responsibilities, and qualifications.
        4. **ATS Scorecard**: Detailed scoring on Skills (45%), Experience (40%), and ATS Readability (15%).
        5. **Suggested Resume & Cover Letter**: Generate and regenerate complete tailored assets with one click.
        6. **Job Match Finder**: Scout top 100 live jobs across LinkedIn/Indeed using Tavily and rank against your resume.
        """
    )

    st.markdown(" ")
    c_act1, c_act2 = st.columns(2)
    with c_act1:
        if st.button("🚀 Launch ATS Checker", type="primary", use_container_width=True):
            st.switch_page("pages/1_🎯_ATS_Checker.py")
    with c_act2:
        if st.button("💼 Find Matching Jobs (Tavily)", type="secondary", use_container_width=True):
            st.switch_page("pages/3_💼_Job_Match_Finder.py")


with col_right:
    st.subheader("📋 Recent Audit History")
    recent_evals = get_recent_evaluations(limit=5)

    if recent_evals:
        for ev in recent_evals:
            with st.container():
                created = str(ev.get("created_at", ""))[:16]
                score = ev.get("overall_score", 0)
                st.markdown(
                    f"""
                    <div style="background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255,255,255,0.06); padding: 0.8rem 1rem; border-radius: 10px; margin-bottom: 0.5rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong style="color: #f1f5f9;">{ev.get('candidate_name', 'Candidate')}</strong>
                                <div style="font-size: 0.8rem; color: #94a3b8;">{ev.get('job_title', 'Role')} • {ev.get('resume_filename', 'file')}</div>
                            </div>
                            <div style="font-size: 1.2rem; font-weight: 700; color: {'#10b981' if score >= 75 else ('#f59e0b' if score >= 50 else '#ef4444')};">
                                {score}%
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("No evaluations in database yet. Run your first resume scan to build your audit log!")
