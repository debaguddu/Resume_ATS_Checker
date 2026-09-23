"""Tavily RAG Job Match Finder Workspace.

Allows candidates to upload resumes, specify job titles, experience level,
country, and location, and uses Tavily Web Search to retrieve up to 100 active jobs
across major portals (LinkedIn, Indeed, Glassdoor, Wellfound, ZipRecruiter, Lever, Greenhouse).
Ranks jobs by semantic ATS match score and provides 20-per-page pagination with
direct application links and 1-click ATS Checker handoff.
"""

import sys
from pathlib import Path

# Ensure src package is importable
src_path = str(Path(__file__).resolve().parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import streamlit as st
from resume_ats_checker.config import get_settings
from resume_ats_checker.parsers.document_parser import parse_document
from resume_ats_checker.rag.job_searcher import (
    search_jobs_with_tavily,
    rank_jobs_with_rag,
    paginate_jobs,
)
from resume_ats_checker.ui.styles import apply_custom_styles
from resume_ats_checker.ui.components import render_header

# 1. Page Configuration
st.set_page_config(
    page_title="Job Match Finder | AI Resume ATS Suite",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_custom_styles()
render_header(
    title="💼 RAG Job Match Finder & Web Scout",
    subtitle="Search top active job postings across LinkedIn, Indeed, Glassdoor, and Greenhouse using Tavily AI, then rank every listing by semantic ATS alignment with your resume.",
)

settings = get_settings()


# Initialize session state for Job Match Finder
if "discovered_jobs" not in st.session_state:
    st.session_state["discovered_jobs"] = []
if "job_current_page" not in st.session_state:
    st.session_state["job_current_page"] = 1
if "job_search_executed" not in st.session_state:
    st.session_state["job_search_executed"] = False

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Search Configuration")
    st.markdown("### 🌐 Tavily API Status")

    tavily_env_key = settings.tavily_api_key
    if tavily_env_key and len(tavily_env_key.strip()) > 5:
        st.success("✅ Tavily API Key loaded from `.env`")
        custom_tavily_key = st.text_input(
            "Tavily Key Override (Optional)",
            type="password",
            value="",
            help="Leave blank to use key from .env",
        )
        active_tavily_key = custom_tavily_key.strip() if custom_tavily_key.strip() else tavily_env_key
    else:
        st.warning("⚠️ `TAVILY_API_KEY` not detected in `.env`.")
        custom_tavily_key = st.text_input(
            "Enter Tavily API Key:",
            type="password",
            help="Enter your Tavily API key here to search live web job boards.",
        )
        active_tavily_key = custom_tavily_key.strip() if custom_tavily_key.strip() else ""

    st.caption("Don't have a key? Get one free at [tavily.com](https://tavily.com). (App includes curated live listings fallback if no key is entered).")
    st.divider()
    st.info("💡 **How It Works**: Tavily searches live postings across LinkedIn, Indeed, Glassdoor, Greenhouse, and Lever. OpenAI RAG embeddings then rank each job against your resume.")

st.markdown("---")


# Section 1: Candidate Inputs
col_res, col_search_params = st.columns([1, 1], gap="large")

with col_res:
    st.subheader("1. 📄 Candidate Resume")
    has_prior_resume = bool(st.session_state.get("parsed_resume_text"))

    if has_prior_resume:
        st.success(f"✅ Loaded resume from active session: **{st.session_state.get('uploaded_file_name', 'Active Resume')}**")
        use_existing = st.checkbox("Use this existing resume", value=True)
    else:
        use_existing = False

    if not use_existing:
        uploaded_file = st.file_uploader(
            "Upload resume (PDF, DOCX, PPTX, TXT):",
            type=["pdf", "docx", "pptx", "txt"],
            key="job_search_file_uploader",
        )
        if uploaded_file is not None:
            try:
                f_bytes = uploaded_file.getvalue()
                text_content, meta = parse_document(uploaded_file.name, f_bytes)
                st.session_state["parsed_resume_text"] = text_content
                st.session_state["uploaded_file_name"] = uploaded_file.name
                st.success(f"✅ Loaded {len(text_content):,} characters from `{uploaded_file.name}`.")
            except Exception as exc:
                st.error(f"Error parsing resume: {exc}")

with col_search_params:
    st.subheader("2. 🎯 Job Target & Location")
    
    col_t1, col_t2 = st.columns([2, 1])
    with col_t1:
        target_title = st.text_input(
            "Target Job Title *",
            value=st.session_state.get("job_target_title", "Technical Lead Data Platforms"),
            placeholder="e.g. Senior Data Engineer, Staff AI Engineer, Technical Lead",
        )
    with col_t2:
        years_exp = st.number_input(
            "Experience (Years) *",
            min_value=0,
            max_value=30,
            value=int(st.session_state.get("job_years_exp", 8)),
            step=1,
        )

    col_loc1, col_loc2 = st.columns([1, 1])
    with col_loc1:
        country_options = [
            "India",
            "United States",
            "United Kingdom",
            "Canada",
            "Germany",
            "Singapore",
            "Australia",
            "Remote / Worldwide",
        ]
        country = st.selectbox("Country *", country_options, index=0)
    with col_loc2:
        location = st.text_input(
            "City / Region",
            value=st.session_state.get("job_location", "Bengaluru"),
            placeholder="e.g. Bengaluru, San Francisco, Remote",
        )

st.markdown("<br>", unsafe_allow_html=True)
col_sub_btn, col_sub_info = st.columns([1, 2])
with col_sub_btn:
    search_clicked = st.button("🚀 Search & RAG-Rank Top 100 Jobs", type="primary", use_container_width=True)

with col_sub_info:
    st.caption("Scans active job boards using Tavily, generates 1536-d semantic embeddings, and ranks listings top-to-bottom.")

# 2. Execution Logic
if search_clicked:
    if not target_title or len(target_title.strip()) < 3:
        st.warning("Please provide a valid Target Job Title to search.")
    else:
        st.session_state["job_target_title"] = target_title
        st.session_state["job_years_exp"] = years_exp
        st.session_state["job_location"] = location

        with st.spinner(f"🔍 Searching live web job boards via Tavily for '{target_title}' in {location or country}..."):
            raw_jobs = search_jobs_with_tavily(
                job_title=target_title,
                years_exp=years_exp,
                country=country,
                location=location,
                api_key=active_tavily_key,
                max_results=100,
            )

        with st.spinner("🧠 Computing RAG semantic embeddings & ranking jobs against your resume..."):
            resume_text = st.session_state.get("parsed_resume_text", "")
            ranked_jobs = rank_jobs_with_rag(resume_text, raw_jobs)

        st.session_state["discovered_jobs"] = ranked_jobs
        st.session_state["job_current_page"] = 1
        st.session_state["job_search_executed"] = True
        st.success(f"🎉 Successfully discovered and RAG-ranked **{len(ranked_jobs)} active jobs**!")

# 3. Display Results
all_jobs = st.session_state.get("discovered_jobs", [])

if all_jobs:
    st.markdown("---")
    st.markdown(f"### 📋 Discovered Job Listings for **{target_title}** ({len(all_jobs)} Total Found)")

    # Metrics Summary
    avg_score = round(sum(j["match_score"] for j in all_jobs) / len(all_jobs), 1)
    top_score = max(j["match_score"] for j in all_jobs)
    remote_count = sum(1 for j in all_jobs if j.get("is_remote"))

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Jobs Found", len(all_jobs))
    with m2:
        st.metric("Top Match Score", f"{top_score}%")
    with m3:
        st.metric("Average Match", f"{avg_score}%")
    with m4:
        st.metric("Remote Opportunities", f"{remote_count} / {len(all_jobs)}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Filter Controls
    col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
    with col_f1:
        min_score = st.slider("Filter by Minimum Match Score (%):", min_value=50, max_value=95, value=65, step=5)
    with col_f2:
        only_remote = st.checkbox("🌐 Remote Jobs Only", value=False)
    with col_f3:
        sort_choice = st.selectbox("Sort Order:", ["Highest Match Score", "Most Recent Posting"])

    # Apply Filters
    filtered_jobs = [j for j in all_jobs if j["match_score"] >= min_score]
    if only_remote:
        filtered_jobs = [j for j in filtered_jobs if j.get("is_remote")]

    if sort_choice == "Most Recent Posting":
        filtered_jobs = sorted(filtered_jobs, key=lambda x: x.get("published_date", ""), reverse=False)
    else:
        filtered_jobs = sorted(filtered_jobs, key=lambda x: x["match_score"], reverse=True)

    st.markdown(f"**Showing {len(filtered_jobs)} matching jobs** (Filtered from {len(all_jobs)} total)")

    # Pagination: 20 per page
    PAGE_SIZE = 20
    current_page = st.session_state.get("job_current_page", 1)
    page_jobs, total_pages = paginate_jobs(filtered_jobs, page=current_page, page_size=PAGE_SIZE)

    # Pagination Nav Header
    c_prev, c_page_info, c_next = st.columns([1, 2, 1])
    with c_prev:
        if st.button("◀ Previous 20 Jobs", disabled=(current_page <= 1), use_container_width=True):
            st.session_state["job_current_page"] = max(1, current_page - 1)
            st.rerun()
    with c_page_info:
        st.markdown(
            f"<div style='text-align: center; font-weight: 600; padding-top: 6px;'>"
            f"Page {current_page} of {total_pages} (Displaying jobs {(current_page - 1) * PAGE_SIZE + 1} - "
            f"{min(current_page * PAGE_SIZE, len(filtered_jobs))})"
            f"</div>",
            unsafe_allow_html=True,
        )
    with c_next:
        if st.button("Next 20 Jobs ▶", disabled=(current_page >= total_pages), use_container_width=True):
            st.session_state["job_current_page"] = min(total_pages, current_page + 1)
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Render 20 Job Cards
    for idx, job in enumerate(page_jobs, start=(current_page - 1) * PAGE_SIZE + 1):
        score = job["match_score"]
        score_color = "#10b981" if score >= 88 else ("#f59e0b" if score >= 75 else "#6b7280")
        score_badge = f"<span style='background: {score_color}22; color: {score_color}; border: 1px solid {score_color}; padding: 4px 10px; border-radius: 9999px; font-weight: 700; font-size: 0.9rem;'>🎯 {score}% Match</span>"
        
        remote_badge = "<span style='background: #3b82f622; color: #3b82f6; border: 1px solid #3b82f6; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; margin-left: 6px;'>🌐 Remote</span>" if job.get("is_remote") else ""
        source_badge = f"<span style='background: #64748b22; color: #94a3b8; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;'>🔗 {job.get('source_domain', 'Web')}</span>"

        with st.container():
            st.markdown(
                f"""
                <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem; border-left: 5px solid {score_color};">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <h4 style="margin: 0; color: #f8fafc; font-size: 1.15rem;">#{idx}. {job['title']}</h4>
                            <p style="margin: 4px 0; color: #94a3b8; font-weight: 500;">
                                🏢 <strong style="color: #cbd5e1;">{job['company']}</strong> &nbsp;|&nbsp; 📍 {job['location']} {remote_badge} &nbsp;|&nbsp; 🕒 {job.get('published_date', 'Recent')} &nbsp;|&nbsp; {source_badge}
                            </p>
                        </div>
                        <div>
                            {score_badge}
                        </div>
                    </div>
                    <p style="color: #cbd5e1; font-size: 0.92rem; margin: 10px 0 8px 0; line-height: 1.45;">
                        {job['snippet']}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Action buttons for this job
            c_act1, c_act2, c_spacer = st.columns([1.5, 1.8, 3])
            with c_act1:
                st.link_button(
                    label="🔗 View & Apply on Site",
                    url=job["url"],
                    type="secondary",
                    use_container_width=True,
                )
            with c_act2:
                btn_key = f"ats_handoff_{job['id']}_{idx}"
                if st.button(f"🎯 Analyze in ATS Checker", key=btn_key, use_container_width=True):
                    # Handoff snippet to ATS Checker cached JD
                    st.session_state["cached_jd"] = (
                        f"Job Title: {job['title']}\n"
                        f"Company: {job['company']}\n"
                        f"Location: {job['location']}\n\n"
                        f"Job Description & Requirements:\n{job['snippet']}"
                    )
                    st.switch_page("pages/1_🎯_ATS_Checker.py")

    # Bottom Pagination Nav
    st.markdown("---")
    b_prev, b_page_info, b_next = st.columns([1, 2, 1])
    with b_prev:
        if st.button("◀ Previous Page", key="bottom_prev", disabled=(current_page <= 1), use_container_width=True):
            st.session_state["job_current_page"] = max(1, current_page - 1)
            st.rerun()
    with b_page_info:
        st.markdown(
            f"<div style='text-align: center; color: #94a3b8; padding-top: 6px;'>"
            f"Showing {len(page_jobs)} of {len(filtered_jobs)} matching jobs (Page {current_page} of {total_pages})"
            f"</div>",
            unsafe_allow_html=True,
        )
    with b_next:
        if st.button("Next Page ▶", key="bottom_next", disabled=(current_page >= total_pages), use_container_width=True):
            st.session_state["job_current_page"] = min(total_pages, current_page + 1)
            st.rerun()
elif st.session_state.get("job_search_executed"):
    st.info("No jobs found matching your filters. Try lowering the minimum match score or relaxing search terms.")
