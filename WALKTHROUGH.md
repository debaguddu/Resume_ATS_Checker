# Resume ATS Checker - Complete Technical Specifications & Feature Walkthrough

This document serves as the **single living source of truth** for the technical architecture, module contracts, database schemas, feature workflows, and verification test suite of the **Resume ATS Checker** application.

---

## 📋 Table of Contents
1. [System Architecture & Data Flow](#1-system-architecture--data-flow)
2. [Directory Structure](#2-directory-structure)
3. [Technical Module & API Specifications](#3-technical-module--api-specifications)
   - [A. Document Parser (`parsers/document_parser.py`)](#a-document-parser-parsersdocument_parserpy)
   - [B. RAG & Vectorstore Engine (`rag/vectorstore.py`)](#b-rag--vectorstore-engine-ragvectorstorepy)
   - [C. ATS Scoring Chain (`rag/chains.py`)](#c-ats-scoring-chain-ragchainspy)
   - [D. Resume Rewrite Engine (`rag/rewrite_chain.py`)](#d-resume-rewrite-engine-ragrewrite_chainpy)
   - [E. Cover Letter Generator (`rag/cover_letter_chain.py`)](#e-cover-letter-generator-ragcover_letter_chainpy)
   - [F. Structured Resume Builder Engine (`rag/builder_chain.py`)](#f-structured-resume-builder-engine-ragbuilder_chainpy)
   - [G. Multi-Format Exporter (`utils/exporter.py`)](#g-multi-format-exporter-utilsexporterpy)
   - [H. Database Persistence (`database/`)](#h-database-persistence-database)
4. [End-to-End Feature Walkthrough](#4-end-to-end-feature-walkthrough)
   - [Feature 1: Multi-Format Document Ingestion](#feature-1-multi-format-document-ingestion)
   - [Feature 2: RAG-Powered ATS Scoring & Match Analysis](#feature-2-rag-powered-ats-scoring--match-analysis)
   - [Feature 3: Strategic Complete Resume Rewriting & Regeneration](#feature-3-strategic-complete-resume-rewriting--regeneration)
   - [Feature 4: Tailored Cover Letter Generator](#feature-4-tailored-cover-letter-generator)
   - [Feature 5: Interactive Structured Resume Builder](#feature-5-interactive-structured-resume-builder)
   - [Feature 6: Multi-Format Document Exporter (Word / PDF / Text / Markdown)](#feature-6-multi-format-document-exporter-word--pdf--text--markdown)
   - [Feature 7: PostgreSQL Audit Logging & Vector Store](#feature-7-postgresql-audit-logging--vector-store)
5. [Automated Verification & Test Suite](#5-automated-verification--test-suite)
6. [Maintenance Protocol: Keeping This Document Updated](#6-maintenance-protocol-keeping-this-document-updated)

---

## 1. System Architecture & Data Flow

```mermaid
flowchart TD
    User([Candidate / Recruiter]) -->|Uploads PDF / Word / PPTX| Parser[document_parser.py]
    User -->|Pastes Job Description| UI_ATS[pages/1_🎯_ATS_Checker.py]

    Parser -->|Normalized Text| Chunker[RecursiveCharacterTextSplitter]
    UI_ATS -->|JD Text| Chunker

    Chunker -->|Chunks| Embedder[OpenAI text-embedding-3-small]
    Embedder -->|Vectors| Similarity[Cosine Similarity Engine]

    Similarity -->|Ranked Matches & Gaps| LangChain[rag/chains.py: evaluate_resume_ats]
    LangChain -->|ChatOpenAI gpt-4o-mini| Pydantic[Structured ATSEvaluationResult]

    Pydantic -->|Persist Audit Log| DB[(PostgreSQL evaluations & embeddings)]
    Pydantic -->|Display Scorecard & Badges| UI_ATS

    UI_ATS -->|Regenerate Angle| Rewrite[rag/rewrite_chain.py]
    Rewrite -->|Tailored Resume| UI_ATS

    UI_ATS -->|Generate Cover Letter| Cover[rag/cover_letter_chain.py]
    Cover -->|Tailored Cover Letter| UI_ATS

    UI_ATS -->|Handoff Resume & JD| Builder[pages/2_📝_Resume_Builder.py]
    Builder -->|AI Suggestion Engine| Decomp[rag/builder_chain.py: decompose_and_tailor_resume]
    Decomp -->|Structured Sections & Bullets| Builder
    Builder -->|Toggle Checkboxes| LivePreview[Live Dynamic Resume Preview]

    LivePreview -->|Word Export| ExpDocx[exporter.py: .docx]
    LivePreview -->|PDF Export| ExpPdf[exporter.py: .pdf]
    LivePreview -->|Text Export| ExpTxt[exporter.py: .txt]
    LivePreview -->|Markdown Export| ExpMd[exporter.py: .md]
```

### Core Technologies:
- **Frontend / UI**: [Streamlit](https://streamlit.io/) with custom glassmorphism styles, responsive columns, and real-time session state management.
- **LLM Orchestration**: [LangChain](https://www.langchain.com/) with OpenAI `gpt-4o-mini` and `text-embedding-3-small`.
- **Database**: PostgreSQL 18 with relational audit logging and vector embeddings fallback.
- **Document Processing**: `pypdf`, `python-docx`, `python-pptx`, and `reportlab`.

---

## 2. Directory Structure

```
Resume ATS Checker/
├── app.py                                # Streamlit entrypoint, navigation & executive dashboard
├── pages/
│   ├── 1_🎯_ATS_Checker.py              # Core ATS Checker & RAG analysis workspace
│   └── 2_📝_Resume_Builder.py           # Interactive Accordion Resume Builder & export studio
├── src/
│   └── resume_ats_checker/
│       ├── config.py                    # Environment settings loaded via Pydantic
│       ├── database/
│       │   ├── connection.py            # PostgreSQL connection pool & automatic table schema creation
│       │   └── repository.py            # Database CRUD operations for evaluations and embeddings
│       ├── parsers/
│       │   └── document_parser.py       # Robust ingestion for PDF, DOCX, PPTX, and TXT files
│       ├── rag/
│       │   ├── vectorstore.py           # Chunking, vector embedding, and cosine similarity matching
│       │   ├── chains.py                # LangChain ATS scoring chain with Pydantic output validation
│       │   ├── rewrite_chain.py         # Full resume rewrite engine with 4 strategic angles
│       │   ├── cover_letter_chain.py    # Persuasive, tailored cover letter generator
│       │   └── builder_chain.py         # Resume decomposition & bullet generation into StructuredResume
│       ├── ui/
│       │   ├── styles.py                # Glassmorphism dark mode CSS tokens & styling
│       │   └── components.py            # Reusable UI cards, skill chips, and metric gauges
│       └── utils/
│           ├── __init__.py
│           └── exporter.py              # Document exporter generating Word (.docx), PDF (.pdf), Text (.txt)
├── tests/
│   └── test_suite.py                    # Automated verification test suite
├── README.md                            # Public overview, quickstart & setup guide
├── WALKTHROUGH.md                       # Complete technical specifications & living feature walkthrough
└── AGENTS.md                            # Workspace synchronization rules
```

---

## 3. Technical Module & API Specifications

### A. Document Parser (`parsers/document_parser.py`)
- **Location**: [`src/resume_ats_checker/parsers/document_parser.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/parsers/document_parser.py)
- **Functions**:
  - `parse_document(filename: str, file_bytes: bytes) -> Tuple[str, Dict[str, Any]]`
  - `parse_pdf(file_bytes: bytes) -> str`
  - `parse_docx(file_bytes: bytes) -> str`
  - `parse_pptx(file_bytes: bytes) -> str`
  - `clean_text(raw_text: str) -> str`
- **Inputs**: File name and raw binary byte stream.
- **Outputs**: Cleaned plain text string, metadata dictionary (`format`, `char_count`, `word_count`).
- **Dependencies**: `pypdf`, `python-docx`, `python-pptx`.

### B. RAG & Vectorstore Engine (`rag/vectorstore.py`)
- **Location**: [`src/resume_ats_checker/rag/vectorstore.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/rag/vectorstore.py)
- **Functions**:
  - `chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 100) -> List[str]`
  - `get_embeddings_model() -> OpenAIEmbeddings`
  - `cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float`
  - `perform_rag_analysis(resume_text: str, jd_text: str) -> Dict[str, Any]`
- **Inputs**: Raw resume text, target Job Description text.
- **Outputs**: Top requirement-to-evidence matches, mean semantic similarity score.
- **Dependencies**: `langchain-openai`, `langchain-text-splitters`, `numpy`.

### C. ATS Scoring Chain (`rag/chains.py`)
- **Location**: [`src/resume_ats_checker/rag/chains.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/rag/chains.py)
- **Pydantic Schema**: `ATSEvaluationResult`
  - `overall_score: int` (0-100)
  - `skills_score: int` (45% weight: must-have tools, languages, certifications)
  - `experience_score: int` (40% weight: scope, impact, relevant seniority)
  - `formatting_score: int` (15% weight: readability, standard headers, bullet structure)
  - `candidate_name: str`
  - `matched_keywords: List[str]`
  - `missing_keywords: List[str]`
  - `strengths: List[str]`
  - `weaknesses: List[str]`
  - `actionable_recommendations: List[str]` (Google X-Y-Z formula recommendations)
  - `executive_summary: str`
- **Functions**: `evaluate_resume_ats(resume_text: str, jd_text: str, rag_context: Dict[str, Any]) -> ATSEvaluationResult`
- **Dependencies**: `langchain-openai`, `pydantic`.

### D. Resume Rewrite Engine (`rag/rewrite_chain.py`)
- **Location**: [`src/resume_ats_checker/rag/rewrite_chain.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/rag/rewrite_chain.py)
- **Functions**: `generate_suggested_resume(resume_text: str, jd_text: str, missing_keywords: List[str], variation_focus: str = "Targeted ATS Optimization") -> str`
- **Supported Strategic Angles**:
  1. *Targeted ATS Optimization*
  2. *Executive & Leadership Impact*
  3. *Technical & Architectural Depth*
  4. *Metric-Heavy & Data-Driven*
- **Outputs**: Full Markdown rewrite tailored to JD requirements.

### E. Cover Letter Generator (`rag/cover_letter_chain.py`)
- **Location**: [`src/resume_ats_checker/rag/cover_letter_chain.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/rag/cover_letter_chain.py)
- **Functions**: `generate_cover_letter(resume_text: str, jd_text: str, candidate_name: str, target_role: str = "") -> str`
- **Outputs**: Formatted, persuasive Markdown cover letter.

### F. Structured Resume Builder Engine (`rag/builder_chain.py`)
- **Location**: [`src/resume_ats_checker/rag/builder_chain.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/rag/builder_chain.py)
- **Pydantic Schemas**:
  - `WorkExperienceEntry`: `company`, `role`, `location`, `employment_type`, `start_date`, `end_date`, `bullets: List[str]`
  - `EducationEntry`: `institution`, `degree`, `location`, `start_date`, `end_date`
  - `ProjectEntry`: `title`, `technologies`, `description`, `bullets: List[str]`
  - `StructuredResume`: `full_name`, `target_title`, `email`, `phone`, `location`, `linkedin`, `github_portfolio`, `professional_summary`, `skills_languages`, `skills_frameworks`, `skills_cloud_tools`, `work_experience`, `education`, `certifications`, `projects`, `awards`, `leadership_activities`, `publications`
- **Functions**:
  - `decompose_and_tailor_resume(resume_text: str, job_description: str) -> StructuredResume`
  - `generate_default_sample_resume() -> StructuredResume`

### G. Multi-Format Exporter (`utils/exporter.py`)
- **Location**: [`src/resume_ats_checker/utils/exporter.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/utils/exporter.py)
- **Functions**:
  - `generate_docx_from_structured_resume(resume: StructuredResume, selections: Dict[str, Any]) -> bytes`
  - `generate_pdf_from_structured_resume(resume: StructuredResume, selections: Dict[str, Any]) -> bytes`
  - `generate_txt_from_structured_resume(resume: StructuredResume, selections: Dict[str, Any]) -> str`
  - `generate_docx_from_markdown(markdown_text: str, candidate_name: str) -> bytes`
  - `generate_pdf_from_markdown(markdown_text: str, candidate_name: str) -> bytes`
- **Outputs**: Byte streams (`.docx`, `.pdf`) and plain text string (`.txt`).
- **Dependencies**: `python-docx`, `reportlab`.

### H. Database Persistence (`database/`)
- **Location**: [`src/resume_ats_checker/database/`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/database/)
- **Modules**:
  - `connection.py`: `check_connection()`, `init_db()`, SQLAlchemy engine pool creation.
  - `repository.py`: `save_evaluation()`, `get_evaluation_by_id()`, `get_recent_evaluations()`, `update_suggested_resume()`, `update_cover_letter()`, `save_resume_embeddings()`.
- **Database Tables**:
  - `evaluations`: Primary evaluation records (scores, keywords, recommendations, outputs).
  - `resume_embeddings`: Document chunks and vectors (`pgvector` or `JSONB`).

---

## 4. End-to-End Feature Walkthrough

### Feature 1: Multi-Format Document Ingestion
- Upload PDF, Word (`.docx`), PowerPoint (`.pptx`), or plain text resumes.
- Automatically handles complex slide shapes, speaker notes, and embedded table cells.
- Normalizes whitespace, strips invalid characters, and extracts structural text.

### Feature 2: RAG-Powered ATS Scoring & Match Analysis
- RAG pipeline chunks both documents, embeds them with OpenAI `text-embedding-3-small`, and performs cosine similarity retrieval.
- Evaluates skills match, experience relevance, and ATS formatting with clear breakdown scorecards.
- Highlights missing keywords in red chips, matched skills in green chips, and provides Google X-Y-Z formula recommendations.

### Feature 3: Strategic Complete Resume Rewriting & Regeneration
- Full resume rewrite tailored to the JD.
- Interactive multi-angle dropdown allowing the candidate to regenerate using 4 strategic perspectives:
  1. *Targeted ATS Optimization*
  2. *Executive & Leadership Impact*
  3. *Technical & Architectural Depth*
  4. *Metric-Heavy & Data-Driven*

### Feature 4: Tailored Cover Letter Generator
- Crafts a personalized 3-4 paragraph cover letter aligning candidate achievements with the employer's specific mission.
- Downloadable in plain text or Markdown.

### Feature 5: Interactive Structured Resume Builder
- **Cross-Navigation**: Easily hand off parsed resume and JD directly from the ATS Checker.
- **Standalone Mode**: Upload reference resumes or paste JDs independently, or load sample data.
- **Accordion Checklists**: Granular control with checkboxes next to each role, credential, and individual bullet point.
- **Live Preview**: Real-time compilation displaying only checked elements.

### Feature 6: Multi-Format Document Exporter (Word / PDF / Text / Markdown)
- One-click downloads available in both the **Interactive Resume Builder** and the **ATS Checker**:
  - **Word (`.docx`)**: Clean typography, 0.75" margins, bold titles, native Word bullets.
  - **PDF (`.pdf`)**: Publication-grade vector PDF generated via ReportLab with zero GTK dependencies.
  - **Text (`.txt`)**: Clean ASCII layout for legacy ATS job portals.
  - **Markdown (`.md`)**: Formatted markdown for developer profiles.

### Feature 7: PostgreSQL Audit Logging & Vector Store
- Automated audit trail saving scores, keywords, and generated documents.
- Fallback vector storage supporting both native `pgvector` and standard `JSONB`.

---

## 5. Automated Verification & Test Suite

The comprehensive automated test suite is located in [`tests/test_suite.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/tests/test_suite.py).

### Running Tests:
```bash
uv run python tests/test_suite.py
```

### Verification Matrix:
| Test Component | Target Module | Verification Scope | Status |
| :--- | :--- | :--- | :---: |
| `test_pdf_parsing` | `document_parser.py` | Validates `pypdf` extraction on binary streams | `PASSED` |
| `test_docx_parsing` | `document_parser.py` | Validates `python-docx` heading & body extraction | `PASSED` |
| `test_pptx_parsing` | `document_parser.py` | Validates `python-pptx` presentation extraction | `PASSED` |
| `test_database_integration` | `connection.py` & `repository.py` | Validates PostgreSQL connection, DDL & CRUD | `PASSED` |
| `test_builder_schema` | `builder_chain.py` | Validates Pydantic `StructuredResume` schema | `PASSED` |
| `test_exporter` | `exporter.py` | Validates Word, PDF, and Text byte streams | `PASSED` |

---

## 6. Maintenance Protocol: Keeping This Document Updated

Whenever new features, database tables, UI pages, or export capabilities are added:
1. **Update Architecture & Diagrams**: Update Section 1 and Section 2 if modules or data flow change.
2. **Update Module & API Specifications**: Document new functions, inputs, outputs, schemas, and dependencies in Section 3.
3. **Update Feature Walkthrough**: Add user interactions, screenshots, and workflows in Section 4.
4. **Update Test Matrix**: Add newly created test cases to Section 5.
5. **Synchronize with README.md**: Keep `README.md` and `WALKTHROUGH.md` synchronized and committed to git.
