"""Tavily RAG Job Match Finder Workspace.

Allows candidates to upload resumes, specify job titles, experience level,
country, and location, and uses Tavily Web Search to retrieve up to 100 active jobs
across major portals (LinkedIn, Naukri, Reddit, Indeed, Glassdoor, Lever, Greenhouse).
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
    extract_job_search_criteria,
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
    title="💼 RAG Job Match Finder & Multi-Channel Scout",
    subtitle="Discover direct job requisitions and recruiter hiring posts across LinkedIn, Naukri, Reddit, Greenhouse, and Lever ranked by ATS semantic alignment.",
)

settings = get_settings()

# Initialize session state for Job Match Finder
if "discovered_jobs" not in st.session_state:
    st.session_state["discovered_jobs"] = []
if "job_current_page" not in st.session_state:
    st.session_state["job_current_page"] = 1
if "job_search_executed" not in st.session_state:
    st.session_state["job_search_executed"] = False
if "job_min_score_filter" not in st.session_state:
    st.session_state["job_min_score_filter"] = 0

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Search Configuration")
    if settings.tavily_api_key and len(settings.tavily_api_key.strip()) > 5:
        st.success("🟢 Tavily API: Connected (`.env`)")
    else:
        st.warning("🟡 Tavily API: Key not detected in `.env`")

    st.divider()
    st.info(
        "💡 **Multi-Channel Scout**:\n"
        "- 💼 Direct LinkedIn Jobs & 📢 Recruiter Posts\n"
        "- 🇮🇳 Naukri Requisitions\n"
        "- 🤖 Reddit Hiring Threads\n"
        "- 🎯 Greenhouse & Lever ATS Boards\n"
        "- 🧠 OpenAI RAG Semantic Ranking"
    )

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

# Auto-extract criteria if resume is present and hasn't been extracted for this version yet
active_resume_text = st.session_state.get("parsed_resume_text", "")
if active_resume_text:
    resume_sig = f"{st.session_state.get('uploaded_file_name', 'resume')}_{len(active_resume_text)}"
    if st.session_state.get("last_extracted_resume_sig") != resume_sig:
        with st.spinner("🤖 Auto-extracting Job Title, Experience, and Location from resume..."):
            extracted = extract_job_search_criteria(active_resume_text)
            st.session_state["job_target_title"] = extracted.get("target_job_title", "Technical Lead Data Platforms")
            st.session_state["job_years_exp"] = extracted.get("years_of_experience", 8)
            st.session_state["job_country"] = extracted.get("country", "India")
            st.session_state["job_location"] = extracted.get("city_or_region", "Bengaluru")
            st.session_state["last_extracted_resume_sig"] = resume_sig
            st.session_state["show_extracted_alert"] = True

with col_res:
    if active_resume_text:
        c_ext1, c_ext2 = st.columns([1.5, 1])
        with c_ext1:
            if st.button("🔄 Re-extract from Resume", help="Re-scan the loaded resume to auto-detect title, experience, and location"):
                with st.spinner("🤖 Re-extracting criteria from resume..."):
                    extracted = extract_job_search_criteria(active_resume_text)
                    st.session_state["job_target_title"] = extracted.get("target_job_title", "Technical Lead Data Platforms")
                    st.session_state["job_years_exp"] = extracted.get("years_of_experience", 8)
                    st.session_state["job_country"] = extracted.get("country", "India")
                    st.session_state["job_location"] = extracted.get("city_or_region", "Bengaluru")
                    st.session_state["show_extracted_alert"] = True
                    st.rerun()

        if st.session_state.get("show_extracted_alert"):
            st.caption(
                f"✨ **Auto-detected from Resume**: Role: `{st.session_state.get('job_target_title')}` | "
                f"Exp: `{st.session_state.get('job_years_exp')} yrs` | "
                f"Location: `{st.session_state.get('job_location')}, {st.session_state.get('job_country')}`"
            )

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
        cur_country = st.session_state.get("job_country", "India")
        if cur_country not in country_options:
            country_options.insert(0, cur_country)
        c_idx = country_options.index(cur_country) if cur_country in country_options else 0
        country = st.selectbox("Country *", country_options, index=c_idx)
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
    st.caption("Scans direct openings across LinkedIn, Naukri, Reddit, Greenhouse, Lever, and Indeed, generating semantic embeddings and ranking listings.")

# 2. Execution Logic
if search_clicked:
    if not target_title or len(target_title.strip()) < 3:
        st.warning("Please provide a valid Target Job Title to search.")
    else:
        st.session_state["job_target_title"] = target_title
        st.session_state["job_years_exp"] = years_exp
        st.session_state["job_country"] = country
        st.session_state["job_location"] = location
        st.session_state["job_min_score_filter"] = 0  # Reset filter so all new jobs are visible

        with st.spinner(f"🔍 Searching live openings (LinkedIn, Naukri, Reddit, ATS) via Tavily for '{target_title}' in {location or country}..."):
            raw_jobs = search_jobs_with_tavily(
                job_title=target_title,
                years_exp=years_exp,
                country=country,
                location=location,
                api_key=settings.tavily_api_key,
                max_results=100,
            )

        with st.spinner("🧠 Computing RAG semantic embeddings & ranking jobs against your resume..."):
            ranked_jobs = rank_jobs_with_rag(active_resume_text, raw_jobs)

        st.session_state["discovered_jobs"] = ranked_jobs
        st.session_state["job_current_page"] = 1
        st.session_state["job_search_executed"] = True
        st.success(f"🎉 Successfully discovered and RAG-ranked **{len(ranked_jobs)} active jobs**!")

# 3. Display Results
all_jobs = st.session_state.get("discovered_jobs", [])

if all_jobs:
    st.markdown("---")
    current_search_title = st.session_state.get("job_target_title", target_title)
    st.markdown(f"### 📋 Discovered Job Listings for **{current_search_title}** ({len(all_jobs)} Total Found)")

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
        min_score = st.slider(
            "Filter by Minimum Match Score (%):",
            min_value=0,
            max_value=95,
            value=int(st.session_state.get("job_min_score_filter", 0)),
            step=5,
            key="job_min_score_filter",
        )
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

    # Empty filtered state handling
    if not filtered_jobs:
        st.warning(
            f"⚠️ No jobs meet the current filter of **{min_score}% match** "
            f"(Highest match score found in this batch is **{top_score}%**). Lower the filter to view listings."
        )
        if st.button("🔄 Reset Match Filter to 0% (Show All Jobs)", type="primary"):
            st.session_state["job_min_score_filter"] = 0
            st.session_state["job_current_page"] = 1
            st.rerun()
    else:
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
            start_num = (current_page - 1) * PAGE_SIZE + 1
            end_num = min(current_page * PAGE_SIZE, len(filtered_jobs))
            st.markdown(
                f"<div style='text-align: center; font-weight: 600; padding-top: 6px;'>"
                f"Page {current_page} of {total_pages} (Displaying jobs {start_num} - {end_num})"
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
            score_color = "#10b981" if score >= 85 else ("#f59e0b" if score >= 72 else "#94a3b8")
            score_badge = f"<span style='background: {score_color}22; color: {score_color}; border: 1px solid {score_color}; padding: 4px 10px; border-radius: 9999px; font-weight: 700; font-size: 0.9rem;'>🎯 {score}% Match</span>"

            remote_badge = "<span style='background: #3b82f622; color: #3b82f6; border: 1px solid #3b82f6; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; margin-left: 6px;'>🌐 Remote</span>" if job.get("is_remote") else ""
            channel_badge_text = job.get("channel_badge") or f"🔗 {job.get('source_domain', 'Web')}"
            channel_badge = f"<span style='background: #3b82f622; color: #60a5fa; border: 1px solid rgba(96, 165, 250, 0.3); padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;'>{channel_badge_text}</span>"

            # Skill chips
            matched_skills = job.get("matched_skills", [])
            skills_html = "".join([
                f"<span style='background: rgba(148, 163, 184, 0.15); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.2); padding: 2px 8px; border-radius: 4px; font-size: 0.78rem; margin-right: 6px;'>{s}</span>"
                for s in matched_skills
            ])

            with st.container():
                st.markdown(
                    f"""
                    <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem; border-left: 5px solid {score_color};">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div>
                                <h4 style="margin: 0; color: #f8fafc; font-size: 1.15rem;">#{idx}. {job['title']}</h4>
                                <p style="margin: 4px 0; color: #94a3b8; font-weight: 500;">
                                    🏢 <strong style="color: #cbd5e1;">{job['company']}</strong> &nbsp;|&nbsp; 📍 {job['location']} {remote_badge} &nbsp;|&nbsp; 🕒 {job.get('published_date', 'Recent')} &nbsp;|&nbsp; {channel_badge}
                                </p>
                            </div>
                            <div>
                                {score_badge}
                            </div>
                        </div>
                        <p style="color: #cbd5e1; font-size: 0.92rem; margin: 10px 0 8px 0; line-height: 1.45;">
                            {job['snippet']}
                        </p>
                        <div style="margin-top: 8px;">
                            {skills_html}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Action buttons for this job
                c_act1, c_act2, c_spacer = st.columns([1.6, 1.8, 3])
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

