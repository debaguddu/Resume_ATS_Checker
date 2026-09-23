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
│   ├── 2_📝_Resume_Builder.py           # Interactive Accordion Resume Builder & export studio
│   └── 3_💼_Job_Match_Finder.py         # Tavily RAG Job Scout & live multi-board searcher
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
│       │   ├── builder_chain.py         # Resume decomposition & bullet generation into StructuredResume
│       │   └── job_searcher.py          # Tavily multi-site job search & RAG semantic ranker
│       ├── ui/
│       │   ├── styles.py                # Glassmorphism dark mode CSS tokens & styling
│       │   └── components.py            # Reusable UI cards, skill chips, and metric gauges
│       └── utils/
│           ├── __init__.py
│           └── exporter.py              # Document exporter generating Word (.docx), PDF (.pdf), Text (.txt)
├── tests/
│   ├── test_suite.py                    # Comprehensive verification test suite
│   ├── test_concurrency.py              # Multi-user concurrency & vector isolation test suite
│   └── test_job_searcher.py             # Tavily search, RAG ranking & pagination test suite
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
  - `repository.py`: `save_evaluation()`, `get_evaluation_by_id()`, `get_recent_evaluations()`, `update_suggested_resume()`, `update_cover_letter()`, `save_resume_embeddings()`, `get_embeddings_by_evaluation_id()`, `get_all_stored_embeddings()`.
- **Database Tables**:
  - `evaluations`: Primary evaluation records (scores, keywords, recommendations, outputs).
  - `resume_embeddings`: Document chunks and vectors (1536-dimensional float arrays in `vector(1536)` or `JSONB`).

### I. Tavily Web Job Searcher & RAG Ranking Engine (`rag/job_searcher.py`)
- **Location**: [`src/resume_ats_checker/rag/job_searcher.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/rag/job_searcher.py)
- **Functions**:
  - `build_job_search_queries(job_title, years_exp, country, location) -> List[str]`: Generates targeted boolean query strings for LinkedIn, Indeed, Glassdoor, Greenhouse, Lever, and Wellfound.
  - `search_jobs_with_tavily(job_title, years_exp, country, location, api_key, max_results=100) -> List[Dict[str, Any]]`: Queries Tavily AI Search for up to 100 live jobs across job portals, with curated active fallback.
  - `rank_jobs_with_rag(resume_text, job_listings) -> List[Dict[str, Any]]`: Computes 1536-d semantic embeddings for candidate resume and job descriptions, calculating cosine similarity and sorting by match percentage.
  - `paginate_jobs(jobs, page=1, page_size=20) -> Tuple[List[Dict[str, Any]], int]`: Slices job list into 20-job pages.
  - `extract_company_from_title_or_url(title, url) -> str`: Heuristically parses company name from posting headers and domain names.
- **Dependencies**: `tavily-python`, `langchain-openai`, `numpy`.

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
- **Interactive Vector DB Inspector**: An in-app inspector under Tab 1 ("🔍 Diagnostics & RAG Evidence") letting users explore all stored vectors, chunk previews, 1536-d float previews, and pre-formatted SQL queries.
- **Multi-User Isolation & Performance Hardening**:
  - B-tree index `idx_resume_embeddings_eval_id` for fast partitioned queries.
  - Atomic single-roundtrip batch insert for 1536-d embedding chunks.
  - Full UUID4 global uniqueness across all evaluations.
  - Automated session state reset when switching resume files within the same browser session.

### Feature 8: Multi-Channel Job Scout & RAG Job Match Finder (`pages/3_💼_Job_Match_Finder.py`)
- **Location**: [`pages/3_💼_Job_Match_Finder.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/pages/3_%F0%9F%92%BC_Job_Match_Finder.py)
- **Workflow & Key Capabilities**:
  1. **Automatic Resume Parameter Extraction**:
     - When a candidate resume is uploaded or loaded from the active ATS Checker session, `extract_job_search_criteria` uses `ChatOpenAI(model="gpt-4o-mini").with_structured_output(ResumeSearchProfile)` (with heuristic fallback) to automatically extract and populate **Target Job Title**, **Experience (Years)**, **Country**, and **City / Region**.
     - An on-demand `🔄 Re-extract from Resume` button allows candidates to re-detect criteria at any time.
  2. **Multi-Channel Direct Job Scout**:
     - Uses Tavily Web Search across diverse channels:
       - **💼 LinkedIn Direct Jobs**: Deep links to `linkedin.com/jobs/view/*`.
       - **📢 LinkedIn Recruiter Posts**: Hiring announcements by managers and recruiters (`linkedin.com/posts` with `"we are hiring"`, `"DM me resume"`).
       - **🇮🇳 Naukri Requisitions**: Live openings on India's premier job portal (`naukri.com/job-listings`).
       - **🤖 Reddit [Hiring] Threads**: Active community hiring posts on `r/forhire`, `r/remotework`, `r/jobbit`.
       - **🎯 Direct ATS Requisitions**: Direct requisition postings on `boards.greenhouse.io`, `jobs.lever.co`, `jobs.ashbyhq.com`.
  3. **Calibrated RAG Semantic Ranking**:
     - Vector embeddings computed via `text-embedding-3-small` for candidate resume and discovered job listings.
     - Dynamic relative min-max normalization scales scores to 65%–98.5% with skill overlap bonuses, avoiding score compression at 50%.
  4. **Dynamic 0% Filter Default & Empty Recovery**:
     - Minimum match score filter slider defaults to 0% so all 100 discovered jobs render immediately upon search without blank pages.
     - If filtered to an empty set, displays a clear warning banner and a 1-click `🔄 Reset Match Filter to 0%` button.
  5. **Direct Action Triggers**:
     - `🔗 View & Apply on Site`: Direct external link to the exact job requisition or recruiter post (never generic career homepages).
     - `🎯 Analyze in ATS Checker`: 1-click handoff transferring the job specs into the ATS Checker for a deep audit scorecard.

---

## 5. Automated Verification & Test Suite

The comprehensive automated test suite is located in [`tests/test_suite.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/tests/test_suite.py) and [`tests/test_job_searcher.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/tests/test_job_searcher.py).

### Running Tests:
```bash
# Main comprehensive test suite
uv run python tests/test_suite.py

# Multi-user concurrency & vector isolation test suite
uv run python tests/test_concurrency.py

# Multi-channel job searcher, auto-extraction & RAG ranking test suite
uv run python tests/test_job_searcher.py
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
| `test_concurrent_isolation` | `repository.py` & `connection.py` | Simulates parallel evaluations, B-tree index & 0% cross-talk | `PASSED` |
| `test_search_query_builder` | `rag/job_searcher.py` | Validates multi-channel queries (LinkedIn, Naukri, Reddit, ATS) | `PASSED` |
| `test_criteria_auto_extraction`| `rag/job_searcher.py` | Validates Pydantic criteria extraction from resumes | `PASSED` |
| `test_channel_badging_and_direct_links` | `rag/job_searcher.py` | Validates deep job URLs and channel badge assignments | `PASSED` |
| `test_job_search_and_fallback`| `rag/job_searcher.py` | Validates 100 jobs generation with padding and full metadata | `PASSED` |
| `test_rag_semantic_ranking` | `rag/job_searcher.py` | Validates calibrated RAG scoring (top >= 80%, descending sort) | `PASSED` |
| `test_pagination_logic` | `rag/job_searcher.py` | Validates 20 jobs/page slicing across 5 pages for 100 jobs | `PASSED` |


---

## 6. Maintenance Protocol: Keeping This Document Updated

Whenever new features, database tables, UI pages, or export capabilities are added:
1. **Update Architecture & Diagrams**: Update Section 1 and Section 2 if modules or data flow change.
2. **Update Module & API Specifications**: Document new functions, inputs, outputs, schemas, and dependencies in Section 3.
3. **Update Feature Walkthrough**: Add user interactions, screenshots, and workflows in Section 4.
4. **Update Test Matrix**: Add newly created test cases to Section 5.
5. **Synchronize with README.md**: Keep `README.md` and `WALKTHROUGH.md` synchronized and committed to git.
