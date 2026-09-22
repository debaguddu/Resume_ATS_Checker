"""Interactive Structured Resume Builder Studio.

Provides an accordion-based section checklist matching enterprise resume builders.
Allows customizing contact info, target titles, professional summary, work experiences
with selective bullet checkboxes, education, skills, and projects.
Supports cross-navigation from ATS Checker or standalone direct upload/paste.
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
from resume_ats_checker.rag.builder_chain import (
    StructuredResume,
    WorkExperienceEntry,
    EducationEntry,
    ProjectEntry,
    decompose_and_tailor_resume,
    generate_default_sample_resume,
)
from resume_ats_checker.utils.exporter import (
    generate_docx_from_structured_resume,
    generate_pdf_from_structured_resume,
    generate_txt_from_structured_resume,
)
from resume_ats_checker.ui.styles import apply_custom_styles
from resume_ats_checker.ui.components import render_header

st.set_page_config(
    page_title="Interactive Resume Builder",
    page_icon="📝",
    layout="wide",
)

apply_custom_styles()
settings = get_settings()

render_header(
    title="📝 Interactive Structured Resume Builder",
    subtitle="Customize your resume section-by-section with AI suggestions. Expand accordions to select, edit, and toggle individual accomplishment bullets, experience entries, and qualifications.",
)

# Initialize Session State
if "structured_resume" not in st.session_state:
    st.session_state["structured_resume"] = generate_default_sample_resume()
if "builder_selections" not in st.session_state:
    st.session_state["builder_selections"] = {}

# Check if auto-trigger is requested from ATS Checker
if st.session_state.get("builder_auto_trigger") and st.session_state.get("builder_resume_text"):
    st.session_state["builder_auto_trigger"] = False
    with st.spinner("🤖 Decomposing resume and tailoring sections to Job Description..."):
        try:
            decomposed = decompose_and_tailor_resume(
                resume_text=st.session_state["builder_resume_text"],
                job_description=st.session_state.get("builder_jd_text", ""),
            )
            st.session_state["structured_resume"] = decomposed
            st.toast("✅ Resume decomposed and populated from ATS Checker!", icon="🎯")
        except Exception as exc:
            st.warning(f"Could not auto-decompose with AI: {exc}. Loaded structured defaults.")

# Top Context Banner (Navigated from ATS Checker vs Standalone)
is_from_ats = st.session_state.get("from_ats_checker", False)

with st.container():
    if is_from_ats:
        c_banner1, c_banner2 = st.columns([4, 1])
        with c_banner1:
            st.success("🎯 **Connected to ATS Checker**: Suggestions are actively tailored to your uploaded resume and Job Description.")
        with c_banner2:
            if st.button("🔁 Reset / New Input", use_container_width=True):
                st.session_state["from_ats_checker"] = False
                st.session_state["builder_resume_text"] = ""
                st.session_state["builder_jd_text"] = ""
                st.rerun()
    else:
        with st.expander("📥 Standalone Setup: Upload Reference Resume or Paste Job Description", expanded=not bool(st.session_state.get("structured_resume"))):
            col_ref, col_jd = st.columns(2, gap="medium")
            with col_ref:
                st.markdown("**1. Reference Resume (Optional)**")
                ref_file = st.file_uploader(
                    "Upload PDF, Word, or PowerPoint resume reference:",
                    type=["pdf", "docx", "pptx", "txt"],
                    key="builder_ref_uploader",
                )
                ref_text = ""
                if ref_file:
                    try:
                        ref_text, _ = parse_document(ref_file.name, ref_file.getvalue())
                        st.caption(f"Loaded {len(ref_text):,} characters from `{ref_file.name}`")
                    except Exception as e:
                        st.error(f"Error reading file: {e}")

            with col_jd:
                st.markdown("**2. Target Job Description (Optional)**")
                jd_input = st.text_area(
                    "Paste target JD for alignment:",
                    height=130,
                    placeholder="Paste role responsibilities or required technologies here...",
                    key="builder_jd_input",
                )

            btn_col1, btn_col2 = st.columns([1, 1])
            with btn_col1:
                if st.button("✨ Generate Section Suggestions with AI", type="primary", use_container_width=True):
                    if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
                        st.error("Please configure OPENAI_API_KEY in `.env` to run AI section decomposition.")
                    elif not ref_text and not jd_input:
                        st.warning("Please upload a reference resume or paste a Job Description.")
                    else:
                        with st.spinner("Analyzing and decomposing into structured resume sections..."):
                            try:
                                res = decompose_and_tailor_resume(
                                    resume_text=ref_text or "General software and data engineering background.",
                                    job_description=jd_input,
                                )
                                st.session_state["structured_resume"] = res
                                st.success("✅ Generated tailored section suggestions!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Generation failed: {e}")
            with btn_col2:
                if st.button("💡 Load Data Engineering Sample Data", use_container_width=True):
                    st.session_state["structured_resume"] = generate_default_sample_resume()
                    st.success("Loaded Capgemini Data Engineering Lead sample data!")
                    st.rerun()

st.markdown("---")

resume: StructuredResume = st.session_state["structured_resume"]

# Main Layout: Two Columns (Left = Interactive Section Accordions, Right = Live Compiled Preview)
col_editor, col_preview = st.columns([3, 2], gap="large")

with col_editor:
    st.subheader("🛠️ Resume Sections & Accomplishment Checklists")
    st.caption("Click to expand each section. Use the checkboxes to select which accomplishments and details to include.")

    # 1. Contact Information
    with st.expander("👤 Contact Information", expanded=False):
        c_n1, c_n2 = st.columns(2)
        with c_n1:
            resume.full_name = st.text_input("Full Name", value=resume.full_name)
            resume.email = st.text_input("Email", value=resume.email)
            resume.phone = st.text_input("Phone Number", value=resume.phone)
        with c_n2:
            resume.location = st.text_input("Location (City, Country)", value=resume.location)
            resume.linkedin = st.text_input("LinkedIn URL", value=resume.linkedin)
            resume.github_portfolio = st.text_input("GitHub / Portfolio URL", value=resume.github_portfolio)

    # 2. Target Title
    with st.expander("🎯 Target Title", expanded=False):
        resume.target_title = st.text_input(
            "Desired Role Headline",
            value=resume.target_title or "Data Engineering Lead",
            help="This title aligns directly with the job description for high ATS keyword relevance.",
        )

    # 3. Professional Summary (Matching Screenshot 3)
    with st.expander("📄 Professional Summary", expanded=True):
        sum_key = "include_summary"
        include_summary = st.checkbox(
            "Include Professional Summary in Resume",
            value=st.session_state["builder_selections"].get(sum_key, True),
            key=sum_key,
        )
        st.session_state["builder_selections"][sum_key] = include_summary

        if include_summary:
            resume.professional_summary = st.text_area(
                "Tailored Professional Summary:",
                value=resume.professional_summary,
                height=110,
                help="AI-tailored summary weaving core competencies, metrics, and leadership impact.",
            )

    # 4. Work Experience (Matching Screenshot 2)
    with st.expander("💼 Work Experience", expanded=True):
        st.markdown("Select company roles and toggle individual accomplishment bullets:")

        for exp_idx, exp in enumerate(resume.work_experience):
            st.markdown(f"#### Experience #{exp_idx + 1}")
            c_exp_head1, c_exp_head2 = st.columns([3, 1])
            with c_exp_head1:
                comp_key = f"exp_comp_{exp_idx}"
                include_comp = st.checkbox(
                    f"**{exp.company}**",
                    value=st.session_state["builder_selections"].get(comp_key, True),
                    key=comp_key,
                )
                st.session_state["builder_selections"][comp_key] = include_comp

            if include_comp:
                # Sub-details
                c_sub1, c_sub2, c_sub3 = st.columns(3)
                with c_sub1:
                    exp.role = st.text_input("Role Title", value=exp.role, key=f"role_{exp_idx}")
                with c_sub2:
                    exp.location = st.text_input("Location", value=exp.location, key=f"loc_{exp_idx}")
                with c_sub3:
                    c_d1, c_d2 = st.columns(2)
                    with c_d1:
                        exp.start_date = st.text_input("Start", value=exp.start_date, key=f"start_{exp_idx}")
                    with c_d2:
                        exp.end_date = st.text_input("End", value=exp.end_date, key=f"end_{exp_idx}")

                st.markdown("**Accomplishment & Metric Bullets:**")
                # Checkbox list for each bullet point
                for b_idx, bullet in enumerate(exp.bullets):
                    b_key = f"b_{exp_idx}_{b_idx}"
                    c_b_check, c_b_text = st.columns([0.08, 0.92])
                    with c_b_check:
                        b_checked = st.checkbox(
                            "",
                            value=st.session_state["builder_selections"].get(b_key, True),
                            key=b_key,
                        )
                        st.session_state["builder_selections"][b_key] = b_checked
                    with c_b_text:
                        if b_checked:
                            exp.bullets[b_idx] = st.text_area(
                                f"Bullet {b_idx + 1}",
                                value=bullet,
                                height=68,
                                key=f"txt_{exp_idx}_{b_idx}",
                                label_visibility="collapsed",
                            )
                        else:
                            st.markdown(f"<span style='color: #64748b; text-decoration: line-through;'>{bullet}</span>", unsafe_allow_html=True)

                # Add new bullet input
                new_b_key = f"new_bullet_{exp_idx}"
                new_bullet = st.text_input("+ Add custom bullet point", key=new_b_key, placeholder="e.g. Optimized SQL queries reducing processing cost by 25%...")
                if st.button(f"➕ Add Bullet to {exp.company}", key=f"add_b_btn_{exp_idx}"):
                    if new_bullet.strip():
                        exp.bullets.append(new_bullet.strip())
                        st.rerun()

            st.markdown("---")

        # Add new experience entry
        if st.button("➕ Add New Company / Role"):
            resume.work_experience.append(
                WorkExperienceEntry(
                    company="New Company",
                    role="Software Engineer",
                    location="City, Country",
                    employment_type="Full-time",
                    start_date="01/2021",
                    end_date="Present",
                    bullets=["Led project delivering scalable cloud services with 99.9% uptime."],
                )
            )
            st.rerun()

    # 5. Education (Matching Screenshot 4)
    with st.expander("🎓 Education", expanded=True):
        st.markdown("Select degrees and institutions to display:")

        for edu_idx, edu in enumerate(resume.education):
            edu_key = f"edu_item_{edu_idx}"
            include_edu = st.checkbox(
                f"**{edu.institution}** — *{edu.degree}* ({edu.start_date} - {edu.end_date})",
                value=st.session_state["builder_selections"].get(edu_key, True),
                key=edu_key,
            )
            st.session_state["builder_selections"][edu_key] = include_edu

            if include_edu:
                c_e1, c_e2 = st.columns(2)
                with c_e1:
                    edu.institution = st.text_input("Institution", value=edu.institution, key=f"inst_{edu_idx}")
                    edu.degree = st.text_input("Degree / Qualification", value=edu.degree, key=f"deg_{edu_idx}")
                with c_e2:
                    edu.location = st.text_input("Location", value=edu.location, key=f"eduloc_{edu_idx}")
                    c_ed1, c_ed2 = st.columns(2)
                    with c_ed1:
                        edu.start_date = st.text_input("Start", value=edu.start_date, key=f"edustart_{edu_idx}")
                    with c_ed2:
                        edu.end_date = st.text_input("End", value=edu.end_date, key=f"eduend_{edu_idx}")

        if st.button("➕ Add Education Credential"):
            resume.education.append(
                EducationEntry(
                    institution="University Name",
                    degree="Degree Name",
                    location="City, Country",
                    start_date="2016",
                    end_date="2020",
                )
            )
            st.rerun()

    # 6. Skills & Interests
    with st.expander("💻 Skills & Interests", expanded=False):
        st.markdown("**Languages & Querying:**")
        langs = st.text_input("Languages (comma separated)", value=", ".join(resume.skills_languages))
        resume.skills_languages = [s.strip() for s in langs.split(",") if s.strip()]

        st.markdown("**Frameworks & Libraries:**")
        fworks = st.text_input("Frameworks & Platforms", value=", ".join(resume.skills_frameworks))
        resume.skills_frameworks = [s.strip() for s in fworks.split(",") if s.strip()]

        st.markdown("**Cloud, DevOps & Databases:**")
        cloud = st.text_input("Cloud & Tools", value=", ".join(resume.skills_cloud_tools))
        resume.skills_cloud_tools = [s.strip() for s in cloud.split(",") if s.strip()]

    # 7. Certifications
    with st.expander("📜 Certifications", expanded=False):
        for c_idx, cert in enumerate(resume.certifications):
            cert_key = f"cert_{c_idx}"
            inc_cert = st.checkbox(
                cert,
                value=st.session_state["builder_selections"].get(cert_key, True),
                key=cert_key,
            )
            st.session_state["builder_selections"][cert_key] = inc_cert
        new_cert = st.text_input("+ Add Certification", key="new_cert_input")
        if st.button("➕ Add Certification"):
            if new_cert.strip():
                resume.certifications.append(new_cert.strip())
                st.rerun()

    # 8. Projects
    with st.expander("🚀 Projects", expanded=False):
        for p_idx, proj in enumerate(resume.projects):
            p_key = f"proj_{p_idx}"
            inc_proj = st.checkbox(
                f"**{proj.title}** ({proj.technologies})",
                value=st.session_state["builder_selections"].get(p_key, True),
                key=p_key,
            )
            st.session_state["builder_selections"][p_key] = inc_proj
            if inc_proj:
                proj.description = st.text_input("Objective", value=proj.description, key=f"pdesc_{p_idx}")
                for pb_idx, pbullet in enumerate(proj.bullets):
                    proj.bullets[pb_idx] = st.text_input(f"Project Bullet {pb_idx + 1}", value=pbullet, key=f"pbullet_{p_idx}_{pb_idx}")

    # 9. Awards, Leadership & Publications
    with st.expander("🏆 Awards, Leadership & Publications", expanded=False):
        st.markdown("**Awards & Honors:**")
        for a_idx, award in enumerate(resume.awards_scholarships):
            st.markdown(f"• {award}")
        st.markdown("**Volunteering & Leadership:**")
        for l_idx, lead in enumerate(resume.volunteering_leadership):
            st.markdown(f"• {lead}")


# Right Column: Live Compiled Resume Output
with col_preview:
    st.subheader("👁️ Live Compiled Resume")
    st.caption("Dynamically formatted using only your selected (checked) accomplishments and sections.")

    # Build compiled Markdown representation
    lines = []
    lines.append(f"# {resume.full_name}")
    contact_parts = []
    if resume.target_title:
        contact_parts.append(f"**{resume.target_title}**")
    if resume.location:
        contact_parts.append(resume.location)
    if resume.email:
        contact_parts.append(resume.email)
    if resume.phone:
        contact_parts.append(resume.phone)
    if resume.linkedin:
        contact_parts.append(f"[{resume.linkedin}](https://{resume.linkedin})")
    if resume.github_portfolio:
        contact_parts.append(f"[{resume.github_portfolio}](https://{resume.github_portfolio})")

    lines.append(" | ".join(contact_parts))
    lines.append("")

    # Summary
    if st.session_state["builder_selections"].get("include_summary", True) and resume.professional_summary:
        lines.append("## PROFESSIONAL SUMMARY")
        lines.append(resume.professional_summary)
        lines.append("")

    # Skills
    if resume.skills_languages or resume.skills_frameworks or resume.skills_cloud_tools:
        lines.append("## TECHNICAL SKILLS")
        if resume.skills_languages:
            lines.append(f"- **Languages**: {', '.join(resume.skills_languages)}")
        if resume.skills_frameworks:
            lines.append(f"- **Frameworks & Platforms**: {', '.join(resume.skills_frameworks)}")
        if resume.skills_cloud_tools:
            lines.append(f"- **Cloud & Tools**: {', '.join(resume.skills_cloud_tools)}")
        lines.append("")

    # Work Experience
    has_exp = False
    exp_lines = ["## PROFESSIONAL EXPERIENCE"]
    for exp_idx, exp in enumerate(resume.work_experience):
        if st.session_state["builder_selections"].get(f"exp_comp_{exp_idx}", True):
            has_exp = True
            header_line = f"**{exp.company}** — *{exp.role}*"
            date_loc = f"({exp.location} | {exp.start_date} – {exp.end_date})"
            exp_lines.append(f"{header_line} {date_loc}")
            for b_idx, bullet in enumerate(exp.bullets):
                if st.session_state["builder_selections"].get(f"b_{exp_idx}_{b_idx}", True):
                    exp_lines.append(f"- {bullet}")
            exp_lines.append("")

    if has_exp:
        lines.extend(exp_lines)

    # Education
    has_edu = False
    edu_lines = ["## EDUCATION"]
    for edu_idx, edu in enumerate(resume.education):
        if st.session_state["builder_selections"].get(f"edu_item_{edu_idx}", True):
            has_edu = True
            edu_lines.append(f"- **{edu.degree}** — {edu.institution}, {edu.location} ({edu.start_date} – {edu.end_date})")
    if has_edu:
        edu_lines.append("")
        lines.extend(edu_lines)

    # Certifications
    has_cert = False
    cert_lines = ["## CERTIFICATIONS"]
    for c_idx, cert in enumerate(resume.certifications):
        if st.session_state["builder_selections"].get(f"cert_{c_idx}", True):
            has_cert = True
            cert_lines.append(f"- {cert}")
    if has_cert:
        cert_lines.append("")
        lines.extend(cert_lines)

    # Projects
    has_proj = False
    proj_lines = ["## PROJECTS"]
    for p_idx, proj in enumerate(resume.projects):
        if st.session_state["builder_selections"].get(f"proj_{p_idx}", True):
            has_proj = True
            proj_lines.append(f"**{proj.title}** ({proj.technologies})")
            if proj.description:
                proj_lines.append(f"*{proj.description}*")
            for b in proj.bullets:
                proj_lines.append(f"- {b}")
            proj_lines.append("")
    if has_proj:
        lines.extend(proj_lines)

    compiled_text = "\n".join(lines)

    # Render Preview Box
    st.markdown(
        f'<div class="document-preview-box" style="max-height: 650px;">{compiled_text}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("### 📥 Download Customized Resume")
    c_btn1, c_btn2, c_btn3 = st.columns(3)

    # Word (.docx) Export
    with c_btn1:
        docx_data = generate_docx_from_structured_resume(resume, st.session_state["builder_selections"])
        st.download_button(
            label="📄 Word (.docx)",
            data=docx_data,
            file_name=f"Resume_{resume.full_name.replace(' ', '_')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True,
        )

    # PDF (.pdf) Export
    with c_btn2:
        pdf_data = generate_pdf_from_structured_resume(resume, st.session_state["builder_selections"])
        st.download_button(
            label="📕 PDF (.pdf)",
            data=pdf_data,
            file_name=f"Resume_{resume.full_name.replace(' ', '_')}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )

    # Plain Text (.txt) Export
    with c_btn3:
        txt_data = generate_txt_from_structured_resume(resume, st.session_state["builder_selections"])
        st.download_button(
            label="📝 Text (.txt)",
            data=txt_data,
            file_name=f"Resume_{resume.full_name.replace(' ', '_')}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    # Markdown (.md) Export
    st.download_button(
        label="⬇️ Markdown (.md)",
        data=compiled_text,
        file_name=f"Resume_{resume.full_name.replace(' ', '_')}.md",
        mime="text/markdown",
        use_container_width=True,
    )
