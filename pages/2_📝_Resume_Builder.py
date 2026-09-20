"""Resume Builder & Template Studio (Future Expansion Workspace).

Scaffolded workspace supporting visual resume templates, data & photo placeholders,
and planned export to PDF and DOCX formats.
"""

import sys
from pathlib import Path

# Ensure src package is importable
src_path = str(Path(__file__).resolve().parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import streamlit as st
from resume_ats_checker.ui.styles import apply_custom_styles
from resume_ats_checker.ui.components import render_header

st.set_page_config(
    page_title="Resume Builder & Templates",
    page_icon="📝",
    layout="wide",
)

apply_custom_styles()

render_header(
    title="📝 Resume Builder & Template Studio",
    subtitle="Design professional resumes with structured templates, upload photos, input profile details, and export formatted PDF or Word documents.",
)

st.info("💡 **Modular Feature Preview**: This page provides the modular foundation for future resume templates, profile data entry, and multi-format document exporting.")

# Section 1: Template Selection
st.subheader("1. 🎨 Choose a Resume Template")
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(
        """
        <div class="score-card" style="border: 2px solid #6366f1; text-align: left;">
            <h3 style="color: #818cf8; margin-top: 0;">Modern Tech</h3>
            <p style="color: #cbd5e1; font-size: 0.9rem;">Clean single-column layout optimized for ATS parsers, developer portfolios, and technical roles.</p>
            <span class="badge-matched">Recommended for Tech</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.radio("Select Template", ["Modern Tech", "Executive Suite", "Minimalist Ivory"], index=0, label_visibility="collapsed")

with c2:
    st.markdown(
        """
        <div class="score-card" style="text-align: left;">
            <h3 style="color: #f1f5f9; margin-top: 0;">Executive Suite</h3>
            <p style="color: #94a3b8; font-size: 0.9rem;">Sophisticated layout emphasizing leadership impact, revenue growth, and career progression.</p>
            <span class="badge-matched" style="background: rgba(99,102,241,0.15); color: #818cf8; border-color: rgba(99,102,241,0.3);">Leadership Focus</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        """
        <div class="score-card" style="text-align: left;">
            <h3 style="color: #f1f5f9; margin-top: 0;">Minimalist Ivory</h3>
            <p style="color: #94a3b8; font-size: 0.9rem;">Elegant typography, generous margins, and strict academic/consulting standard layout.</p>
            <span class="badge-matched" style="background: rgba(148,163,184,0.15); color: #cbd5e1; border-color: rgba(148,163,184,0.3);">Classic Standard</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# Section 2: Data Input & Photo Placeholder
st.subheader("2. 👤 Candidate Profile & Data Placeholders")
col_photo, col_info = st.columns([1, 2], gap="large")

with col_photo:
    st.markdown("**📸 Candidate Photo (Optional)**")
    photo_file = st.file_uploader("Upload headshot photo (.png, .jpg)", type=["png", "jpg", "jpeg"])
    if photo_file:
        st.image(photo_file, caption="Profile Preview", width=180)
    else:
        st.markdown(
            """
            <div style="width: 180px; height: 180px; border-radius: 12px; border: 2px dashed #475569; display: flex; align-items: center; justify-content: center; color: #94a3b8;">
                Photo Placeholder
            </div>
            """,
            unsafe_allow_html=True,
        )

with col_info:
    name = st.text_input("Full Name", value="Debaranjan")
    title = st.text_input("Professional Headline", value="Senior AI / Machine Learning Engineer")
    c_mail, c_phone = st.columns(2)
    with c_mail:
        email = st.text_input("Email", value="debaranjanb91@gmail.com")
    with c_phone:
        phone = st.text_input("Phone", value="+91 98765 43210")

summary = st.text_area(
    "Professional Summary",
    value="Results-driven AI Engineer with deep expertise in LLMs, RAG pipelines, PostgreSQL, and scalable cloud architectures.",
    height=100,
)

skills = st.text_area(
    "Core Technical Skills",
    value="Python, LangChain, OpenAI API, PostgreSQL, pgvector, Docker, Streamlit, FastAPI, AWS",
    height=80,
)

st.divider()

# Section 3: Document Export Actions
st.subheader("3. 📤 Export Document")
st.markdown("Generate presentation-ready documents formatted according to your selected template:")

exp_c1, exp_c2, exp_c3 = st.columns([1, 1, 2])
with exp_c1:
    if st.button("📄 Export to PDF", use_container_width=True):
        st.toast("PDF export pipeline triggered! (Configured for future release)")
with exp_c2:
    if st.button("📝 Export to Word (.docx)", use_container_width=True):
        st.toast("DOCX export pipeline triggered! (Configured for future release)")
