# 🎯 Enterprise AI Resume ATS Suite

An enterprise-grade, modular, **RAG-powered Resume ATS (Applicant Tracking System) Checker** built with **Streamlit**, **LangChain**, **OpenAI**, and **PostgreSQL**.

---

## 📌 Repository Rules & Design Policy

> [!IMPORTANT]
> **Mandatory Rule**: Any changes, additions, or modifications to the system design, architecture, database schema, RAG pipeline, or UI workflows **MUST immediately be updated in this `README.md` file**.  
> This ensures that documentation, module descriptions, and flow diagrams remain an accurate reflection of the codebase.

---

## 📖 Table of Contents
1. [System Architecture & Design Philosophy](#-system-architecture--design-philosophy)
2. [End-to-End Flow Diagrams](#-end-to-end-flow-diagrams)
   - [System Architecture & Data Flow](#1-system-architecture--data-flow)
   - [User Interaction Sequence Diagram](#2-user-interaction-sequence-diagram)
   - [Database Entity-Relationship (ER) Diagram](#3-database-entity-relationship-er-diagram)
3. [Comprehensive Module Descriptions](#-comprehensive-module-descriptions)
   - [Document Parsing Layer](#1-document-parsing-layer-parsersdocument_parserpy)
   - [RAG & Vector Retrieval Engine](#2-rag--vector-retrieval-engine-ragvectorstorepy)
   - [LangChain ATS Evaluation Chain](#3-langchain-ats-evaluation-chain-ragchainspy)
   - [Resume Rewrite & Regeneration Engine](#4-resume-rewrite--regeneration-engine-ragrewrite_chainpy)
   - [Cover Letter Generator](#5-cover-letter-generator-ragcover_letter_chainpy)
   - [PostgreSQL Database & Storage Layer](#6-postgresql-database--storage-layer)
   - [Application Configuration](#7-application-configuration-configpy)
   - [UI Design System & Components](#8-ui-design-system--components)
   - [Streamlit Application Pages](#9-streamlit-application-pages)
4. [Getting Started & Installation](#-getting-started--installation)
5. [Environment Variables Reference](#-environment-variables-reference)
6. [Testing & Verification](#-testing--verification)
7. [Future Expansion Roadmap](#-future-expansion-roadmap)

---

## 🏛️ System Architecture & Design Philosophy

The application is architected around the following key principles:
1. **Separation of Concerns (Modularity)**: Distinct separation between file ingestion, RAG vector processing, LLM evaluation chains, relational persistence, and presentation UI.
2. **Semantic RAG Grounding**: Rather than relying purely on top-level LLM parsing, the engine breaks both the resume and the job description into semantic chunks, computes vector embeddings via OpenAI (`text-embedding-3-small`), and matches individual requirements against candidate evidence.
3. **Strict Structured Output**: All ATS diagnostics are validated via **Pydantic schemas** to ensure predictable scoring, categorized skills, and actionable feedback.
4. **Relational & Vector Hybrid Storage**: Powered by **PostgreSQL 18** with automatic detection for the `pgvector` extension and a transparent JSONB fallback for maximum portability across local installations and cloud deployments.
5. **Future-Ready Expansion**: Structured as a multi-page Streamlit application where subsequent features (e.g., visual template designers, photo uploaders, and PDF/DOCX exporters) plug into the existing architecture without modifying core ATS logic.

---

## 🔄 End-to-End Flow Diagrams

### 1. System Architecture & Data Flow

```mermaid
flowchart TB
    subgraph UI["Streamlit User Interface"]
        Upload["File Uploader (PDF, DOCX, PPTX)"]
        JDPaste["Job Description Text Area"]
        Dash["Metrics Dashboard (4 Glassmorphic Cards)"]
        Tab1["Tab 1: Diagnostics & RAG Evidence"]
        Tab2["Tab 2: Recommendations Box"]
        Tab3["Tab 3: Suggested Resume (Create & Regenerate)"]
        Tab4["Tab 4: Tailored Cover Letter"]
    end

    subgraph Parsers["Document Parsing Layer"]
        Parser["parsers/document_parser.py"]
        PDF["pypdf: Extract Pages & Text"]
        DOCX["python-docx: Extract Paragraphs & Tables"]
        PPTX["python-pptx: Extract Slides & Shapes"]
    end

    subgraph RAG["Semantic RAG Pipeline"]
        Chunker["RecursiveCharacterTextSplitter"]
        Embed["OpenAI text-embedding-3-small"]
        Cosine["Cosine Similarity Engine"]
        Matches["Requirement-to-Evidence Matches"]
    end

    subgraph LLM["LangChain & OpenAI Engine"]
        EvalChain["rag/chains.py: evaluate_resume_ats()"]
        PydanticOut["ATSEvaluationResult (Structured JSON)"]
        RewriteChain["rag/rewrite_chain.py: generate_suggested_resume()"]
        CoverChain["rag/cover_letter_chain.py: generate_cover_letter()"]
    end

    subgraph DB["PostgreSQL 18 Database"]
        Conn["database/connection.py: SQLAlchemy Pool"]
        TableEval[("evaluations Table")]
        TableEmb[("resume_embeddings Table")]
    end

    %% Ingestion Flow
    Upload --> Parser
    Parser --> PDF
    Parser --> DOCX
    Parser --> PPTX
    PDF --> Chunker
    DOCX --> Chunker
    PPTX --> Chunker
    JDPaste --> Chunker

    %% RAG Flow
    Chunker --> Embed
    Embed --> Cosine
    Cosine --> Matches
    Matches --> EvalChain

    %% LLM Evaluation Flow
    EvalChain --> PydanticOut
    PydanticOut --> Dash
    PydanticOut --> Tab1
    PydanticOut --> Tab2
    PydanticOut --> DB

    %% Generative Actions
    Tab3 --> RewriteChain
    RewriteChain --> Tab3
    RewriteChain --> DB

    Tab4 --> CoverChain
    CoverChain --> Tab4
    CoverChain --> DB

    %% Database Operations
    Conn --> TableEval
    Conn --> TableEmb
```

---

### 2. User Interaction Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User as Candidate / User
    participant App as Streamlit (pages/1_🎯_ATS_Checker.py)
    participant Parser as parsers/document_parser.py
    participant RAG as rag/vectorstore.py
    participant OpenAI as OpenAI API
    participant LangChain as rag/chains.py
    participant DB as PostgreSQL (database/repository.py)

    User->>App: 1. Uploads Resume (PDF/DOCX/PPTX) & Pastes JD
    App->>Parser: 2. parse_document(file_name, bytes)
    Parser-->>App: Returns normalized clean text & metadata
    User->>App: 3. Clicks "Run RAG & ATS Analysis"
    
    App->>RAG: 4. perform_rag_analysis(resume_text, jd_text)
    RAG->>OpenAI: 5. Generate embeddings for chunks (text-embedding-3-small)
    OpenAI-->>RAG: Vectors returned
    RAG->>RAG: 6. Computes cosine similarity & ranks top-k evidence
    RAG-->>App: Returns rag_matches & average similarity score
    
    App->>LangChain: 7. evaluate_resume_ats(resume_text, jd_text, rag_matches)
    LangChain->>OpenAI: 8. ChatOpenAI (gpt-4o-mini) with structured output
    OpenAI-->>LangChain: Structured ATSEvaluationResult
    LangChain-->>App: Validated ATS scores, keywords, suggestions
    
    App->>DB: 9. save_evaluation(eval_data)
    DB-->>App: Record persisted
    App-->>User: 10. Renders 4 Metric Scorecards, Keyword Chips & Tabs

    opt User Requests Full Resume Rewrite
        User->>App: 11. Clicks "Create Suggested Resume" or "Regenerate"
        App->>LangChain: 12. generate_suggested_resume(..., variation_focus)
        LangChain->>OpenAI: 13. Prompts Master Resume Writer model
        OpenAI-->>LangChain: Tailored complete Markdown resume
        LangChain-->>App: Formatted resume
        App->>DB: 14. update_suggested_resume(eval_id, rewritten)
        App-->>User: 15. Displays preview with Markdown Download button
    end

    opt User Requests Cover Letter
        User->>App: 16. Clicks "Create Cover Letter"
        App->>LangChain: 17. generate_cover_letter(resume, jd, candidate_name)
        LangChain->>OpenAI: 18. Executive communications prompt
        OpenAI-->>LangChain: Tailored cover letter
        LangChain-->>App: Formatted cover letter
        App->>DB: 19. update_cover_letter(eval_id, letter)
        App-->>User: 20. Displays preview with Markdown Download button
    end
```

---

### 3. Database Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    EVALUATIONS {
        varchar(64) id PK "Unique UUID/hash per evaluation"
        timestamp created_at "Audit generation timestamp"
        varchar(255) candidate_name "Extracted candidate name"
        varchar(255) resume_filename "Original uploaded file name"
        varchar(32) resume_format "pdf, docx, pptx, txt"
        varchar(255) job_title "Target role title"
        text job_description "Complete input job description"
        text resume_text "Normalized extracted resume text"
        integer overall_score "Weighted total score (0-100)"
        integer skills_score "Hard skills match score (0-100)"
        integer experience_score "Seniority & depth score (0-100)"
        integer formatting_score "ATS readability score (0-100)"
        text summary "Executive recruiter assessment"
        jsonb missing_keywords "Array of missing critical keywords"
        jsonb strengths "Array of identified candidate strengths"
        jsonb weaknesses "Array of identified deficiencies"
        jsonb suggestions "Actionable bullet recommendations"
        text suggested_resume "Complete rewritten resume (Markdown)"
        text cover_letter "Generated tailored cover letter"
    }

    RESUME_EMBEDDINGS {
        serial id PK "Autoincrement row ID"
        varchar(64) evaluation_id FK "References EVALUATIONS.id"
        varchar(32) chunk_type "'resume' or 'job_description'"
        integer chunk_index "Index position of chunk in document"
        text content "Raw chunk text content"
        vector_or_jsonb embedding "1536-dim vector or JSON array"
        timestamp created_at "Creation timestamp"
    }

    EVALUATIONS ||--o{ RESUME_EMBEDDINGS : "has chunks"
```

---

## 🧩 Comprehensive Module Descriptions

### 1. Document Parsing Layer: `parsers/document_parser.py`
- **File**: [`src/resume_ats_checker/parsers/document_parser.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/parsers/document_parser.py)
- **Purpose**: Provides a unified, format-agnostic text extraction service for resumes.
- **Key Functions**:
  - `clean_text(text: str) -> str`: Normalizes Windows/Unix carriage returns, removes non-printable bytes, collapses redundant whitespace, and preserves clean paragraph boundaries.
  - `parse_pdf(file_bytes: bytes) -> (str, dict)`: Utilizes `pypdf.PdfReader` to extract text page-by-page, returning formatted text alongside metadata (`page_count`, `char_count`).
  - `parse_docx(file_bytes: bytes) -> (str, dict)`: Utilizes `python-docx` to extract both narrative paragraphs and structured tabular rows (critical for tables listing skills, certifications, and education).
  - `parse_pptx(file_bytes: bytes) -> (str, dict)`: Utilizes `python-pptx` to traverse presentation slides, extracting text from geometric shapes, tables, text frames, and speaker notes.
  - `parse_document(file_name: str, file_bytes: bytes) -> (str, dict)`: Master dispatcher routing by extension (`.pdf`, `.docx`, `.pptx`, `.txt`, `.md`) with graceful legacy fallbacks for `.doc` and `.ppt`.

---

### 2. RAG & Vector Retrieval Engine: `rag/vectorstore.py`
- **File**: [`src/resume_ats_checker/rag/vectorstore.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/rag/vectorstore.py)
- **Purpose**: Powers semantic chunking, vector embedding generation, and cosine similarity matching between resume evidence and job requirements.
- **Key Functions**:
  - `get_embeddings_model() -> OpenAIEmbeddings`: Instantiates LangChain's `OpenAIEmbeddings` configured via `.env` (`text-embedding-3-small`).
  - `chunk_text(text: str, chunk_size=500, chunk_overlap=50) -> List[Document]`: Uses `RecursiveCharacterTextSplitter` with punctuation-aware separators (`\n\n`, `\n`, `•`, `-`, `. `) to maintain coherent bullet points.
  - `cosine_similarity(vec_a, vec_b) -> float`: Computes vector cosine similarity with zero-norm safety checks.
  - `perform_rag_analysis(resume_text, job_description) -> (matches, avg_score)`:
    1. Chunks both documents into separate vector corpora.
    2. Computes batch embeddings for all chunks.
    3. Finds the highest-similarity candidate evidence for every JD requirement chunk.
    4. Tags matches as `Strong Match` (>= 72%), `Partial Match` (>= 55%), or `Missing/Gap` (< 55%).
    5. Returns ranked matches and mean semantic coverage score.

---

### 3. LangChain ATS Evaluation Chain: `rag/chains.py`
- **File**: [`src/resume_ats_checker/rag/chains.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/rag/chains.py)
- **Purpose**: Executes an elite ATS audit prompt using LangChain and OpenAI structured outputs.
- **Pydantic Schema**: `ATSEvaluationResult`
  - `candidate_name`: Extracted name.
  - `job_title`: Target job title from JD.
  - `overall_score`: Rigorous match percentage (0–100%).
  - `skills_score`: Direct technical/hard skills coverage (0–100%).
  - `experience_score`: Career trajectory, seniority, and scale (0–100%).
  - `formatting_score`: ATS parseability and structure (0–100%).
  - `summary`: 2–3 sentence executive assessment.
  - `missing_keywords`: High-priority technologies missing from resume.
  - `matched_keywords`: Shared skills and tools found in both.
  - `strengths`: 3–5 candidate highlights aligning with the role.
  - `weaknesses`: 2–4 noticeable gaps.
  - `suggestions`: Metric-driven recommendations formatted using the Google X-Y-Z formula.
- **Execution**: `evaluate_resume_ats(resume_text, job_description, rag_matches)` builds the RAG context string, constructs the `ChatPromptTemplate`, binds `with_structured_output(ATSEvaluationResult)` on `ChatOpenAI(model=settings.openai_model, temperature=0.2)`, and invokes the pipeline.

---

### 4. Resume Rewrite & Regeneration Engine: `rag/rewrite_chain.py`
- **File**: [`src/resume_ats_checker/rag/rewrite_chain.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/rag/rewrite_chain.py)
- **Purpose**: Complete reconstruction of candidate resumes to target 95%+ ATS match rates while preserving factual integrity.
- **Key Functions**:
  - `generate_suggested_resume(resume_text, job_description, missing_keywords, variation_focus)`:
    - Synthesizes original resume accomplishments with target role requirements.
    - Naturally weaves in missing keywords.
    - Structures content with standard ATS headers: `# NAME`, `## SUMMARY`, `## TECHNICAL SKILLS`, `## PROFESSIONAL EXPERIENCE` (X-Y-Z bullets), `## EDUCATION`, `## CERTIFICATIONS`.
    - **Regeneration Engine**: When `variation_focus` is passed, shifts strategic emphasis (e.g., *Direct Keyword Maximization*, *Senior Architecture Leadership*, or *Delivery Focus*) at temperature 0.7 to generate a distinct, customized resume.

---

### 5. Cover Letter Generator: `rag/cover_letter_chain.py`
- **File**: [`src/resume_ats_checker/rag/cover_letter_chain.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/rag/cover_letter_chain.py)
- **Purpose**: Generates persuasive, customized cover letters.
- **Key Functions**:
  - `generate_cover_letter(resume_text, job_description, candidate_name) -> str`:
    - Opens with a hook emphasizing relevant domain achievements.
    - Connects candidate experience to the employer's specific operational challenges.
    - Concludes with a proactive, professional call to action.

---

### 6. PostgreSQL Database & Storage Layer
- **Files**:
  - [`src/resume_ats_checker/database/connection.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/database/connection.py)
  - [`src/resume_ats_checker/database/repository.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/database/repository.py)
- **Purpose**: Manages database connectivity, schema lifecycle, and evaluation history storage.
- **Key Functions**:
  - `get_engine() -> Engine`: Lazily creates an SQLAlchemy engine with connection pooling (`pool_pre_ping=True`, `pool_size=5`).
  - `check_connection() -> (bool, str)`: Runs `SELECT version();` to verify connectivity without crashing if disconnected.
  - `init_db() -> (bool, str)`: Automatically creates the `evaluations` table and checks if `CREATE EXTENSION IF NOT EXISTS vector;` is supported. If `pgvector` is absent, seamlessly falls back to storing vector embeddings in standard PostgreSQL `JSONB`.
  - `save_evaluation(eval_data: dict) -> bool`: Upserts an evaluation audit record.
  - `update_suggested_resume(eval_id, text) -> bool` & `update_cover_letter(eval_id, text) -> bool`: Targeted updates for generated assets.
  - `get_recent_evaluations(limit=10) -> List[dict]`: Populates dashboard audit drawer.

---

### 7. Application Configuration: `config.py`
- **File**: [`src/resume_ats_checker/config.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/config.py)
- **Purpose**: Type-safe settings management using `pydantic-settings`.
- **Fields**:
  - `openai_api_key`, `openai_model` (default `gpt-4o-mini`), `embedding_model` (default `text-embedding-3-small`).
  - `postgres_host`, `postgres_port` (default `5432`), `postgres_db`, `postgres_user`, `postgres_password`, `database_url`.
  - Computed property `effective_db_url`: Ensures the modern `postgresql+psycopg://` driver scheme is used.

---

### 8. UI Design System & Components
- **Files**:
  - [`src/resume_ats_checker/ui/styles.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/ui/styles.py)
  - [`src/resume_ats_checker/ui/components.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/ui/components.py)
- **Design Tokens**:
  - **Typography**: Google Font *Inter* with *JetBrains Mono* for code.
  - **Glassmorphism**: Backdrop blur (`backdrop-filter: blur(12px)`), subtle semi-transparent borders (`rgba(255,255,255,0.08)`), and deep shadows.
  - **Status Tokens**: Emerald Green (`#10b981` / `>= 80%`), Sky Blue (`#38bdf8` / `>= 65%`), Amber (`#f59e0b` / `>= 50%`), Crimson Red (`#ef4444` / `< 50%`).
- **Widgets**:
  - `render_header(title, subtitle)`: Glowing header with radial gradient backdrop.
  - `render_metric_cards(overall, skills, experience, formatting)`: 4 responsive scorecard metrics.
  - `render_keyword_badges(matched, missing)`: Pill badges with color-coded status.
  - `render_suggestions_list(suggestions)`: Actionable callout cards.

---

### 9. Streamlit Application Pages
- **Main Dashboard**: [`app.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/app.py)
  - Executive overview, quick-start guide, live sidebar connection indicators (PostgreSQL and OpenAI), and recent evaluation logs.
- **ATS Checker Workspace**: [`pages/1_🎯_ATS_Checker.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/pages/1_%F0%9F%8E%AF_ATS_Checker.py)
  - Two-column input: File uploader (PDF/DOCX/PPTX) + Job Description textarea.
  - Execution button triggering RAG embedding, similarity ranking, LLM structured scoring, and database persistence.
  - Tabbed results display:
    1. *Diagnostics & RAG Evidence* (Keyword badges, strengths, weaknesses, similarity breakdown).
    2. *Suggestions Box* (Google X-Y-Z recommendation callouts).
    3. *Suggested Complete Resume* (Rewrite generator, focus strategy selector, regenerate trigger, Markdown download).
    4. *Tailored Cover Letter* (Cover letter generator and Markdown download).
- **Template & Export Studio (Future Expansion)**: [`pages/2_📝_Resume_Builder.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/pages/2_%F0%9F%93%9D_Resume_Builder.py)
  - Scaffolded page with template cards (*Modern Tech*, *Executive Suite*, *Minimalist Ivory*), profile data fields, candidate photo placeholder, and export triggers for PDF and DOCX.

---

## 🚀 Getting Started & Installation

### 1. Prerequisites
- **Python 3.11+** (managed automatically via `uv`)
- **PostgreSQL 14+** (running locally on port 5432 or via Docker)
- **OpenAI API Key**

### 2. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure your credentials are set in `.env`:
```env
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
DATABASE_URL=postgresql+psycopg://postgres:your_password@localhost:5432/postgres
```

### 3. Sync Dependencies with `uv`
```bash
uv sync
```

### 4. Run the Application
```bash
uv run streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

---

## 🧪 Testing & Verification

Run the automated test suite verifying multi-format parsers, PostgreSQL tables, and CRUD operations:
```bash
uv run python tests/test_suite.py
```

Expected output:
```text
Testing PDF Parser...
  ✓ PDF parser executed successfully.
Testing DOCX Parser...
  ✓ DOCX parser extracted text properly.
Testing PPTX Parser...
  ✓ PPTX parser extracted presentation text properly.
Testing PostgreSQL Connection and Tables...
  Connection check: connected=True, msg=Connected: PostgreSQL 18.6...
  Database init: success=True, msg=Database initialized successfully...
  ✓ PostgreSQL tables, CRUD operations, and JSON serialization verified!

🎉 ALL TESTS PASSED SUCCESSFULLY!
```

---

## 🔮 Future Expansion Roadmap

1. **Resume Builder Direct Export**: Connect `pages/2_📝_Resume_Builder.py` with `weasyprint` or `reportlab` to render downloadable PDF templates directly from the rewritten Markdown resume.
2. **Batch Resume Screening**: Support uploading a ZIP or folder of multiple candidate resumes against a single Job Description to rank applicants by ATS match score.
3. **Cover Letter Tone Customizer**: Add tone selection toggles (*Concise & Impactful*, *Warm & Culturally Aligned*, *Executive & Visionary*).
