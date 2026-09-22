"""Core ATS Checker & RAG Analyzer Workspace.

Performs document extraction, RAG semantic similarity matching,
calculates ATS score, lists missing keywords/suggestions,
and generates/regenerates tailored resumes and cover letters.
"""

import sys
import uuid
from pathlib import Path

# Ensure src package is importable
src_path = str(Path(__file__).resolve().parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import streamlit as st
import json
from resume_ats_checker.config import get_settings
from resume_ats_checker.parsers.document_parser import parse_document
from resume_ats_checker.rag.vectorstore import perform_rag_analysis
from resume_ats_checker.rag.chains import evaluate_resume_ats
from resume_ats_checker.rag.rewrite_chain import generate_suggested_resume
from resume_ats_checker.rag.cover_letter_chain import generate_cover_letter
from resume_ats_checker.database.repository import (
    save_evaluation,
    save_resume_embeddings,
    get_embeddings_by_evaluation_id,
    update_suggested_resume,
    update_cover_letter,
)
from resume_ats_checker.utils.exporter import (
    generate_docx_from_markdown,
    generate_pdf_from_markdown,
)
from resume_ats_checker.ui.styles import apply_custom_styles
from resume_ats_checker.ui.components import (
    render_header,
    render_metric_cards,
    render_keyword_badges,
    render_suggestions_list,
)

st.set_page_config(
    page_title="ATS Checker Workspace",
    page_icon="🎯",
    layout="wide",
)

apply_custom_styles()
settings = get_settings()

render_header(
    title="🎯 ATS Resume Auditor & RAG Matcher",
    subtitle="Upload your resume in PDF, Word, or PowerPoint format, paste the Job Description, and receive an instant ATS scorecard with RAG-backed diagnostics and full resume rewriting.",
)

# Initialize session state for holding analysis results
if "current_eval_id" not in st.session_state:
    st.session_state["current_eval_id"] = None
if "eval_result" not in st.session_state:
    st.session_state["eval_result"] = None
if "rag_matches" not in st.session_state:
    st.session_state["rag_matches"] = []
if "suggested_resume" not in st.session_state:
    st.session_state["suggested_resume"] = None
if "cover_letter" not in st.session_state:
    st.session_state["cover_letter"] = None
if "parsed_resume_text" not in st.session_state:
    st.session_state["parsed_resume_text"] = ""
if "cached_jd" not in st.session_state:
    st.session_state["cached_jd"] = ""

# Sidebar Settings Check
with st.sidebar:
    st.header("⚙️ Configuration")
    st.text_input("OpenAI Model", value=settings.openai_model, disabled=True)
    st.text_input("Database Target", value=f"{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}", disabled=True)
    
    if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
        st.error("⚠️ OpenAI API Key is missing. Add OPENAI_API_KEY in `.env` to enable analysis.")

# Input Layout
col_upload, col_jd = st.columns([1, 1], gap="large")

with col_upload:
    st.subheader("1. 📄 Upload Your Resume")
    uploaded_file = st.file_uploader(
        "Supported formats: PDF, DOCX, PPTX, TXT",
        type=["pdf", "docx", "pptx", "txt", "doc", "ppt"],
        help="Upload your existing resume to extract and compare against job specifications.",
    )

    if uploaded_file is not None:
        try:
            # Check if user switched to a different resume file in this session
            if uploaded_file.name != st.session_state.get("uploaded_file_name"):
                # Clear stale evaluation state for the previous candidate/resume
                for key in ["eval_result", "current_eval_id", "rag_matches", "embedded_chunks", "suggested_resume", "cover_letter"]:
                    st.session_state.pop(key, None)

            file_bytes = uploaded_file.getvalue()
            resume_text, metadata = parse_document(uploaded_file.name, file_bytes)
            st.session_state["parsed_resume_text"] = resume_text
            st.session_state["uploaded_file_name"] = uploaded_file.name
            st.session_state["resume_format"] = metadata.get("format", "unknown")

            st.success(
                f"✅ Extracted {len(resume_text):,} characters from `{uploaded_file.name}` "
                f"({metadata.get('format', '').upper()})"
            )
            with st.expander("👁️ Preview Extracted Resume Text", expanded=False):
                st.text_area("Extracted Resume", value=resume_text, height=200, disabled=True)
        except Exception as exc:
            st.error(f"Error reading document: {exc}")

with col_jd:
    st.subheader("2. 📋 Paste Job Description")
    job_description = st.text_area(
        "Target Job Description / Requirements:",
        height=240,
        placeholder="Paste full job posting, required qualifications, technical stack, and core responsibilities here...",
    )
    if job_description:
        st.session_state["cached_jd"] = job_description

st.divider()

# Analyze Button
col_btn, col_info = st.columns([1, 3])
with col_btn:
    analyze_clicked = st.button("🚀 Run RAG & ATS Analysis", type="primary", use_container_width=True)

with col_info:
    if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
        st.warning("⚠️ Please provide a valid `OPENAI_API_KEY` in `.env` to execute RAG embeddings and LLM analysis.")

if analyze_clicked:
    if not st.session_state.get("parsed_resume_text"):
        st.warning("Please upload a resume file first.")
    elif not job_description or len(job_description.strip()) < 30:
        st.warning("Please paste a comprehensive Job Description (at least 30 characters).")
    else:
        with st.spinner("🔍 Chunking documents, embedding vectors, and evaluating ATS match..."):
            try:
                # 1. RAG semantic analysis
                rag_matches, avg_rag_score, embedded_chunks = perform_rag_analysis(
                    resume_text=st.session_state["parsed_resume_text"],
                    job_description=job_description,
                )
                st.session_state["rag_matches"] = rag_matches
                st.session_state["embedded_chunks"] = embedded_chunks

                # 2. LangChain ATS scoring & diagnostic chain
                eval_res = evaluate_resume_ats(
                    resume_text=st.session_state["parsed_resume_text"],
                    job_description=job_description,
                    rag_matches=rag_matches,
                )
                st.session_state["eval_result"] = eval_res

                # Generate globally unique UUID4 for this evaluation
                eval_id = str(uuid.uuid4())
                st.session_state["current_eval_id"] = eval_id
                st.session_state["suggested_resume"] = None
                st.session_state["cover_letter"] = None

                # 3. Save to PostgreSQL database
                save_data = {
                    "id": eval_id,
                    "candidate_name": eval_res.candidate_name,

                    "resume_filename": st.session_state.get("uploaded_file_name", "resume"),
                    "resume_format": st.session_state.get("resume_format", "pdf"),
                    "job_title": eval_res.job_title,
                    "job_description": job_description,
                    "resume_text": st.session_state["parsed_resume_text"],
                    "overall_score": eval_res.overall_score,
                    "skills_score": eval_res.skills_score,
                    "experience_score": eval_res.experience_score,
                    "formatting_score": eval_res.formatting_score,
                    "summary": eval_res.summary,
                    "missing_keywords": eval_res.missing_keywords,
                    "strengths": eval_res.strengths,
                    "weaknesses": eval_res.weaknesses,
                    "suggestions": eval_res.suggestions,
                }
                save_evaluation(save_data)
                if embedded_chunks:
                    save_resume_embeddings(eval_id, embedded_chunks)
                st.success("✅ Analysis completed and saved to PostgreSQL (including vector embeddings)!")
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")

# Display Analysis Results Dashboard
eval_res = st.session_state.get("eval_result")
if eval_res is not None:
    st.markdown("---")
    st.markdown(f"### 📊 ATS Audit Scorecard for **{eval_res.candidate_name}** — Target: *{eval_res.job_title}*")

    # 1. Metric Cards
    render_metric_cards(
        overall=eval_res.overall_score,
        skills=eval_res.skills_score,
        experience=eval_res.experience_score,
        formatting=eval_res.formatting_score,
    )

    # Executive Summary Banner
    st.markdown(
        f"""
        <div class="callout-box" style="border-left-color: #10b981; margin-top: 1.5rem;">
            <h4>📋 Executive Recruiter Summary</h4>
            <p>{eval_res.summary}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Cross-Navigation to Resume Builder
    col_build_btn, col_build_info = st.columns([2, 3])
    with col_build_btn:
        if st.button("🛠️ Customize in Interactive Resume Builder", type="primary", use_container_width=True):
            st.session_state["builder_resume_text"] = st.session_state.get("parsed_resume_text", "")
            st.session_state["builder_jd_text"] = st.session_state.get("cached_jd", "")
            st.session_state["from_ats_checker"] = True
            st.session_state["builder_auto_trigger"] = True
            st.switch_page("pages/2_📝_Resume_Builder.py")
    with col_build_info:
        st.caption("✨ Takes your uploaded resume and JD to customize sections, toggle accomplishment checkboxes, and edit bullet points.")

    # 2. Detailed Tabs for Results
    tab_diagnostics, tab_suggestions, tab_resume, tab_cover = st.tabs([
        "🔍 Diagnostics & RAG Evidence",
        "💡 Suggestions Box",
        "📄 Suggested Complete Resume",
        "✉️ Tailored Cover Letter",
    ])

    # TAB 1: Diagnostics
    with tab_diagnostics:
        render_keyword_badges(
            matched=eval_res.matched_keywords,
            missing=eval_res.missing_keywords,
        )

        col_str, col_weak = st.columns(2)
        with col_str:
            st.markdown("### 💪 Standout Strengths")
            for s in eval_res.strengths:
                st.markdown(f"• {s}")
        with col_weak:
            st.markdown("### ⚠️ Key Deficiencies / Gaps")
            for w in eval_res.weaknesses:
                st.markdown(f"• {w}")

        st.markdown("### 🔬 Semantic RAG Retrieval Breakdown")
        rag_matches = st.session_state.get("rag_matches", [])
        if rag_matches:
            for idx, match in enumerate(rag_matches[:6], 1):
                status_color = "🟢" if match["status"] == "Strong Match" else ("🟡" if match["status"] == "Partial Match" else "🔴")
                with st.expander(f"{status_color} Requirement #{idx}: {match['requirement_chunk'][:80]}... ({match['similarity_score']}%)"):
                    st.markdown(f"**Job Requirement:**\n> {match['requirement_chunk']}")
                    st.markdown(f"**Best Matching Resume Evidence:**\n> {match['best_resume_evidence']}")
                    st.caption(f"Status: {match['status']} | Similarity: {match['similarity_score']}%")

        # Vector Database & Embeddings Inspector
        st.markdown("---")
        st.markdown("### 🧠 Vector Database Inspector (`resume_embeddings` Table)")
        st.caption("Inspect chunk embeddings stored in PostgreSQL with 1536-dimensional float vectors (`text-embedding-3-small`).")

        curr_id = st.session_state.get("current_eval_id")
        stored_vectors = get_embeddings_by_evaluation_id(curr_id) if curr_id else []

        if stored_vectors:
            resume_count = sum(1 for v in stored_vectors if v["chunk_type"] == "resume")
            jd_count = sum(1 for v in stored_vectors if v["chunk_type"] == "job_description")

            c_v1, c_v2, c_v3, c_v4 = st.columns(4)
            with c_v1:
                st.metric("Total Stored Vectors", len(stored_vectors))
            with c_v2:
                st.metric("Resume Chunks", resume_count)
            with c_v3:
                st.metric("JD Chunks", jd_count)
            with c_v4:
                st.metric("Vector Dimensions", 1536)

            with st.expander("📊 View Stored Vector Embeddings & Records", expanded=True):
                filter_type = st.radio(
                    "Filter by Document Chunk Type:",
                    ["All", "resume", "job_description"],
                    horizontal=True,
                    key="vector_filter_radio",
                )
                filtered = (
                    stored_vectors
                    if filter_type == "All"
                    else [v for v in stored_vectors if v["chunk_type"] == filter_type]
                )

                preview_rows = []
                for v in filtered:
                    emb = v.get("embedding")
                    dim_count = 1536
                    if isinstance(emb, str):
                        try:
                            parsed_emb = json.loads(emb)
                            dim_count = len(parsed_emb)
                            preview_emb = f"[{parsed_emb[0]:.4f}, {parsed_emb[1]:.4f}, {parsed_emb[2]:.4f}, ...]"
                        except Exception:
                            preview_emb = emb[:30] + "..."
                    elif isinstance(emb, (list, tuple)):
                        dim_count = len(emb)
                        preview_emb = f"[{emb[0]:.4f}, {emb[1]:.4f}, {emb[2]:.4f}, ...]"
                    else:
                        preview_emb = str(emb)[:30] + "..."

                    snippet = v["content"][:80] + "..." if len(v["content"]) > 80 else v["content"]
                    preview_rows.append({
                        "ID": v["id"],
                        "Type": v["chunk_type"],
                        "Chunk #": v["chunk_index"],
                        "Dims": dim_count,
                        "Vector Preview (Float Array)": preview_emb,
                        "Chunk Text Snippet": snippet,
                    })

                st.dataframe(preview_rows, use_container_width=True)

                st.markdown("##### 💻 How to query directly in PostgreSQL / pgAdmin / DBeaver / psql:")
                st.code(
                    f"-- Query vector embeddings for this evaluation:\n"
                    f"SELECT id, evaluation_id, chunk_type, chunk_index,\n"
                    f"       LEFT(content, 60) AS text_preview,\n"
                    f"       LEFT(embedding::text, 50) AS vector_preview\n"
                    f"FROM resume_embeddings\n"
                    f"WHERE evaluation_id = '{curr_id}'\n"
                    f"ORDER BY chunk_type, chunk_index;",
                    language="sql",
                )
        else:
            st.info("Run an ATS analysis above to generate and persist 1536-dimensional vector embeddings into the database.")


    # TAB 2: Suggestions Box
    with tab_suggestions:
        render_suggestions_list(eval_res.suggestions)

    # TAB 3: Suggested Complete Resume Window
    with tab_resume:
        st.subheader("📄 Tailored Complete Resume")
        st.markdown(
            "Click **Create Suggested Resume** to generate a complete, 95%+ optimized rewrite incorporating all missing keywords and X-Y-Z achievements. Use **Regenerate** to produce an alternative strategic emphasis."
        )

        c_gen1, c_gen2 = st.columns([1, 1])
        with c_gen1:
            create_resume_clicked = st.button("✨ Create Suggested Resume", type="primary", use_container_width=True)
        with c_gen2:
            regen_focus = st.selectbox(
                "Regeneration Strategy:",
                [
                    "Direct Keyword & Metric Maximization",
                    "Senior Engineering & Architecture Leadership",
                    "Domain & Project Delivery Focus",
                ],
                label_visibility="collapsed",
            )
            regen_resume_clicked = st.button("🔄 Regenerate Resume (Fresh Angle)", use_container_width=True)

        if create_resume_clicked or regen_resume_clicked:
            focus = regen_focus if regen_resume_clicked else None
            with st.spinner("Generating tailored resume rewrite..."):
                try:
                    rewritten = generate_suggested_resume(
                        resume_text=st.session_state["parsed_resume_text"],
                        job_description=st.session_state["cached_jd"],
                        missing_keywords=eval_res.missing_keywords,
                        variation_focus=focus,
                    )
                    st.session_state["suggested_resume"] = rewritten
                    if st.session_state.get("current_eval_id"):
                        update_suggested_resume(st.session_state["current_eval_id"], rewritten)
                    st.success("✅ Suggested Resume Generated!")
                except Exception as exc:
                    st.error(f"Failed to generate resume: {exc}")

        current_suggested = st.session_state.get("suggested_resume")
        if current_suggested:
            st.markdown(
                f'<div class="document-preview-box">{current_suggested}</div>',
                unsafe_allow_html=True,
            )
            st.markdown("##### 📥 Export Rewritten Resume:")
            c_d1, c_d2, c_d3 = st.columns(3)
            with c_d1:
                docx_bytes = generate_docx_from_markdown(current_suggested, eval_res.candidate_name)
                st.download_button(
                    label="📄 Word (.docx)",
                    data=docx_bytes,
                    file_name=f"Rewritten_Resume_{eval_res.candidate_name.replace(' ', '_')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary",
                    use_container_width=True,
                )
            with c_d2:
                pdf_bytes = generate_pdf_from_markdown(current_suggested, eval_res.candidate_name)
                st.download_button(
                    label="📕 PDF (.pdf)",
                    data=pdf_bytes,
                    file_name=f"Rewritten_Resume_{eval_res.candidate_name.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True,
                )
            with c_d3:
                st.download_button(
                    label="📝 Text (.txt)",
                    data=current_suggested,
                    file_name=f"Rewritten_Resume_{eval_res.candidate_name.replace(' ', '_')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

            c_sub1, c_sub2 = st.columns([1, 1])
            with c_sub1:
                st.download_button(
                    label="⬇️ Markdown (.md)",
                    data=current_suggested,
                    file_name=f"Rewritten_Resume_{eval_res.candidate_name.replace(' ', '_')}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            with c_sub2:
                if st.button("🛠️ Open in Interactive Section Builder", use_container_width=True):
                    st.session_state["builder_resume_text"] = st.session_state.get("parsed_resume_text", "")
                    st.session_state["builder_jd_text"] = st.session_state.get("cached_jd", "")
                    st.session_state["from_ats_checker"] = True
                    st.session_state["builder_auto_trigger"] = True
                    st.switch_page("pages/2_📝_Resume_Builder.py")
        else:
            st.info("Click 'Create Suggested Resume' above to generate your customized resume.")

    # TAB 4: Tailored Cover Letter Window
    with tab_cover:
        st.subheader("✉️ Tailored Executive Cover Letter")
        st.markdown(
            "Generate a compelling, personalized cover letter directly mapping your accomplishments to the employer's needs."
        )

        create_cover_clicked = st.button("✨ Create Cover Letter", type="primary")

        if create_cover_clicked:
            with st.spinner("Drafting targeted cover letter..."):
                try:
                    letter = generate_cover_letter(
                        resume_text=st.session_state["parsed_resume_text"],
                        job_description=st.session_state["cached_jd"],
                        candidate_name=eval_res.candidate_name,
                    )
                    st.session_state["cover_letter"] = letter
                    if st.session_state.get("current_eval_id"):
                        update_cover_letter(st.session_state["current_eval_id"], letter)
                    st.success("✅ Cover Letter Generated!")
                except Exception as exc:
                    st.error(f"Failed to generate cover letter: {exc}")

        current_letter = st.session_state.get("cover_letter")
        if current_letter:
            st.markdown(
                f'<div class="document-preview-box">{current_letter}</div>',
                unsafe_allow_html=True,
            )
            st.download_button(
                label="⬇️ Download Cover Letter (.md)",
                data=current_letter,
                file_name=f"Cover_Letter_{eval_res.candidate_name.replace(' ', '_')}.md",
                mime="text/markdown",
            )
        else:
            st.info("Click 'Create Cover Letter' above to generate your custom cover letter.")
