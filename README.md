# 🎯 Enterprise AI Resume ATS Suite

An enterprise-grade, modular, **RAG-powered Resume ATS (Applicant Tracking System) Checker** built with **Streamlit**, **LangChain**, **OpenAI**, and **PostgreSQL**.

---

## 📌 Repository Rules & Design Policy

> [!IMPORTANT]
> **Mandatory Synchronization Rule**: Any changes, additions, or modifications to the system design, architecture, database schema, RAG pipeline, or UI workflows **MUST immediately be updated in this `README.md` file**.  
> Detailed implementation notes are also maintained in [**`IMPLEMENTATION_PLAN.md`**](IMPLEMENTATION_PLAN.md).

---

## 📖 Table of Contents
1. [🎯 Project Purpose & Problem Statement](#1--project-purpose--problem-statement)
2. [📋 Project Details & Metadata](#2--project-details--metadata)
3. [🌐 System Overview](#3--system-overview)
4. [📂 Folder Structure](#4--folder-structure)
5. [📚 Libraries & Technologies Used](#5--libraries--technologies-used)
6. [🗄️ Database Architecture (PostgreSQL)](#6-️database-architecture-postgresql)
7. [🚀 How to Run (Step-by-Step Guide)](#7--how-to-run-step-by-step-guide)
8. [🔄 End-to-End Flow Diagrams](#8--end-to-end-flow-diagrams)
   - [System Architecture & Data Flow](#81-system-architecture--data-flow)
   - [User Interaction Sequence Diagram](#82-user-interaction-sequence-diagram)
   - [Database Entity-Relationship (ER) Diagram](#83-database-entity-relationship-er-diagram)
9. [🧩 Comprehensive Module Descriptions](#9--comprehensive-module-descriptions)
   - [Document Parsing Layer (`parsers/document_parser.py`)](#91-document-parsing-layer-parsersdocument_parserpy)
   - [RAG & Vector Retrieval Engine (`rag/vectorstore.py`)](#92-rag--vector-retrieval-engine-ragvectorstorepy)
   - [LangChain ATS Evaluation Chain (`rag/chains.py`)](#93-langchain-ats-evaluation-chain-ragchainspy)
   - [Resume Rewrite & Regeneration Engine (`rag/rewrite_chain.py`)](#94-resume-rewrite--regeneration-engine-ragrewrite_chainpy)
   - [Cover Letter Generator (`rag/cover_letter_chain.py`)](#95-cover-letter-generator-ragcover_letter_chainpy)
   - [PostgreSQL Database & Storage Layer (`database/`)](#96-postgresql-database--storage-layer-database)
   - [Application Configuration (`config.py`)](#97-application-configuration-configpy)
   - [UI Design System & Components (`ui/`)](#98-ui-design-system--components-ui)
   - [Streamlit Application Pages (`app.py`, `pages/`)](#99-streamlit-application-pages)
10. [⚙️ Environment Variables Reference](#10-️environment-variables-reference)
11. [🧪 Testing & Verification](#11--testing--verification)
12. [🔮 Future Expansion Roadmap](#12--future-expansion-roadmap)

---

## 1. 🎯 Project Purpose & Problem Statement

### The Problem
Modern hiring workflows rely heavily on automated **Applicant Tracking Systems (ATS)** like Workday, Taleo, Greenhouse, and Lever. These systems filter out over 75% of qualified applicants before a human recruiter ever sees their resume due to:
- Missing critical technical and domain keywords present in the Job Description.
- Format incompatibilities and unparseable layouts (e.g. multi-column text boxes, non-standard headers).
- Failure to articulate achievements using quantified impact metrics (e.g., the Google X-Y-Z formula: *"Accomplished [X] as measured by [Y], by doing [Z]"*).

### The Solution
The **Enterprise AI Resume ATS Suite** solves this by providing job seekers and recruiters with a transparent, AI-driven audit workspace:
- **Ground Truth Semantic Matching (RAG)**: Chunks both the candidate's resume and the target Job Description, computes vector embeddings, and performs cosine similarity retrieval to detect exact qualification alignments and glaring skill gaps.
- **Holistic ATS Scorecard**: Breaks evaluation into 4 transparent metrics: Overall Score, Skills Match, Experience Relevance, and ATS Formatting.
- **Actionable Diagnostic Feedback**: Highlights matched keywords in emerald green and critical missing keywords in coral red, accompanied by specific bullet improvement recommendations.
- **Tailored Generative Reconstruction**: Instantly rewrites the entire resume to achieve a 95%+ ATS match rate while remaining honest to the candidate's background, with a **Regenerate** engine for alternative strategic angles (Keyword Maximization, Leadership, Delivery).
- **Executive Cover Letter Composition**: Composes personalized cover letters directly connecting the candidate's past wins to the employer's pressing challenges.

---

## 2. 📋 Project Details & Metadata

| Attribute | Specification |
| :--- | :--- |
| **Project Name** | Resume ATS Checker (`resume-ats-checker`) |
| **Version** | `0.1.0` |
| **Author** | Debaranjan (`debaranjanb91@gmail.com`) |
| **Repository** | [https://github.com/debaguddu/Resume_ATS_Checker](https://github.com/debaguddu/Resume_ATS_Checker) |
| **Supported Python** | Python `>= 3.11` (Managed via `uv`, tested on Python `3.12.14`) |
| **Primary Frameworks** | Streamlit, LangChain, OpenAI, SQLAlchemy, Psycopg 3 |
| **Supported File Formats** | PDF (`.pdf`), Word (`.docx`), PowerPoint (`.pptx`), Plain Text (`.txt`, `.md`), Legacy (`.doc`, `.ppt`) |
| **Database** | PostgreSQL 18 with `pgvector` extension and automatic `JSONB` fallback |

---

## 3. 🌐 System Overview

The application follows a clean **modular architecture** with a strict separation of concerns:

```
[User Interface] ──> [Document Parsers] ──> [Semantic RAG Pipeline] ──> [LangChain LLM Chains] ──> [PostgreSQL Persistence]
  (Streamlit)          (PDF/DOCX/PPTX)     (Chunking & Embeddings)      (Scoring & Rewrites)      (Audit History & Logs)
```

1. **Ingestion Layer**: Users upload their resume in PDF, DOCX, or PPTX format and paste a target job description. The parser extracts plain text and preserves paragraph and tabular structure.
2. **Retrieval-Augmented Generation (RAG) Layer**: The resume and JD are split into semantic chunks with punctuation-aware overlaps. Vector embeddings (`text-embedding-3-small`) are generated to measure requirement-to-experience similarity.
3. **Reasoning & Evaluation Layer**: LangChain orchestrates `gpt-4o-mini` with strict **Pydantic structured output** to calculate weighted scores, extract strengths/weaknesses, and compile keyword chips.
4. **Generative Transformation Layer**: Generates customized full resume rewrites and tailored cover letters with multi-angle regeneration options.
5. **Data Persistence Layer**: All audit records, scores, metadata, and generated assets are stored in PostgreSQL on port 5432.

---

## 4. 📂 Folder Structure

```
Resume ATS Checker/
├── .agents/
│   └── rules/
│       └── design_updates.md         # Customization rule enforcing README synchronization
├── .env                              # Local secrets & credentials (git-ignored)
├── .env.example                      # Committed configuration template (no secrets)
├── .gitignore                        # Python, uv, cache, and secrets exclusion rules
├── .python-version                   # Pinned Python version (3.12)
├── pyproject.toml                    # UV project configuration and package dependencies
├── uv.lock                           # Pinned dependency lockfile
├── IMPLEMENTATION_PLAN.md            # Detailed technical specification & component blueprint
├── README.md                         # Complete project documentation, diagrams & guide
├── AGENTS.md                         # Workspace rule for design updates
├── app.py                            # Streamlit entrypoint & executive dashboard
├── pages/
│   ├── 1_🎯_ATS_Checker.py           # Core ATS Checker & RAG Analyzer workspace
│   └── 2_📝_Resume_Builder.py        # Future expansion template & export studio
├── src/
│   └── resume_ats_checker/
│       ├── __init__.py               # Package marker
│       ├── config.py                 # Pydantic Settings & environment loader
│       ├── database/
│       │   ├── __init__.py
│       │   ├── connection.py         # PostgreSQL connection pool & auto table initialization
│       │   └── repository.py         # Evaluation history & embeddings CRUD operations
│       ├── parsers/
│       │   ├── __init__.py
│       │   └── document_parser.py    # Multi-format parser (PDF, DOCX, PPTX, TXT)
│       ├── rag/
│       │   ├── __init__.py
│       │   ├── vectorstore.py        # Semantic chunking, embeddings & cosine similarity
│       │   ├── chains.py             # LangChain structured ATS scoring chain
│       │   ├── rewrite_chain.py      # Complete tailored resume rewrite & regeneration
│       │   └── cover_letter_chain.py # Persuasive tailored cover letter generator
│       └── ui/
│           ├── __init__.py
│           ├── styles.py             # Glassmorphic CSS tokens, typography & color palettes
│           └── components.py         # Reusable UI metric cards, chips & callouts
└── tests/
    └── test_suite.py                 # Automated verification test suite
```

---

## 5. 📚 Libraries & Technologies Used

| Library / Tool | Version | Purpose in Application |
| :--- | :--- | :--- |
| **Streamlit** | `>= 1.40.0` | Powers the reactive multi-page web application, interactive tabs, file uploader, and dashboards. |
| **LangChain Core & Community** | `>= 0.3.0` | Orchestrates prompt templates, chain composition, and LLM output parsing. |
| **LangChain OpenAI** | `>= 0.2.0` | Direct integration with OpenAI's `ChatOpenAI` and `OpenAIEmbeddings` models. |
| **OpenAI SDK** | `>= 1.50.0` | Underlying client communicating with OpenAI GPT-4o-mini and embedding APIs. |
| **SQLAlchemy** | `>= 2.0.0` | Database ORM and connection pooling engine for robust PostgreSQL interaction. |
| **Psycopg 3 (`psycopg[binary]`)** | `>= 3.2.0` | High-performance PostgreSQL database driver with binary wheels for Windows. |
| **pgvector** | `>= 0.3.0` | Vector extension support for storing and indexing embeddings directly in PostgreSQL. |
| **pypdf** | `>= 5.0.0` | Pure-Python PDF extraction library extracting clean text from multi-page resumes. |
| **python-docx** | `>= 1.1.0` | Microsoft Word (`.docx`) document parser extracting paragraphs, headings, and tables. |
| **python-pptx** | `>= 1.0.0` | PowerPoint (`.pptx`) parser extracting text from slides, shapes, tables, and notes. |
| **Pydantic & Pydantic-Settings** | `>= 2.8.0` | Type-safe schema validation for structured LLM evaluation outputs and `.env` configuration. |
| **NumPy** | `>= 1.26.0` | Vector operations and fast cosine similarity computations. |
| **python-dotenv** | `>= 1.0.1` | Loads local environment variables from `.env` seamlessly. |
| **uv** | `>= 0.12.0` | Next-generation Python package manager providing ultra-fast installation and lockfile management. |

---

## 6. 🗄️ Database Architecture (PostgreSQL)

The application uses **PostgreSQL 18** (running locally on port `5432` or via Docker/cloud).

### Automatic Schema Initialization & Vector Fallback
On launch, [`src/resume_ats_checker/database/connection.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/database/connection.py) connects to PostgreSQL and attempts to enable the native `vector` extension:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```
- **If `vector` is available**: Embeddings in `resume_embeddings` are stored as `vector(1536)` columns with indexing.
- **If `vector` is not compiled**: The engine automatically falls back to `JSONB` format for embeddings. The app remains 100% functional without external dependencies or build errors on Windows.

### Database Tables
1. **`evaluations`**:
   Stores candidate audit records, overall and breakdown scores, recruiter summaries, JSON arrays of matched/missing keywords, and generated markdown assets (rewritten resumes and cover letters).
2. **`resume_embeddings`**:
   Stores document chunks, chunk types (`resume` vs `job_description`), and vector embeddings linked by `evaluation_id`.

---

## 7. 🚀 How to Run (Step-by-Step Guide)

### Step 1: Prerequisites
- **Python 3.11 or 3.12** installed (or let `uv` download it automatically).
- **PostgreSQL 14+** running locally on port `5432` (or in a Docker container).
- An **OpenAI API Key** with access to `gpt-4o-mini` and `text-embedding-3-small`.

### Step 2: Clone the Repository
```bash
git clone https://github.com/debaguddu/Resume_ATS_Checker.git
cd "Resume ATS Checker"
```

### Step 3: Configure Environment Variables
Copy the template to create your local `.env`:
```bash
cp .env.example .env
```
Open `.env` in your text editor and update:
```env
OPENAI_API_KEY=sk-your-actual-openai-api-key
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_actual_postgres_password
DATABASE_URL=postgresql+psycopg://postgres:your_actual_postgres_password@localhost:5432/postgres
```

### Step 4: Install Dependencies via `uv`
Install all dependencies cleanly into a local `.venv`:
```bash
uv sync
```

### Step 5: Run Automated Tests
Verify document parsers and PostgreSQL database connectivity:
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
  Connection check: connected=True, msg=Connected: PostgreSQL 18...
  Database init: success=True, msg=Database initialized successfully...
  ✓ PostgreSQL tables, CRUD operations, and JSON serialization verified!

🎉 ALL TESTS PASSED SUCCESSFULLY!
```

### Step 6: Launch the Streamlit Application
```bash
uv run streamlit run app.py
```
Open your web browser and navigate to:  
👉 **`http://localhost:8501`**

---

## 8. 🔄 End-to-End Flow Diagrams

### 8.1 System Architecture & Data Flow

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

### 8.2 User Interaction Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User as Candidate / Recruiter
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
    DB-->>App: Record persisted in PostgreSQL
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

### 8.3 Database Entity-Relationship (ER) Diagram

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

## 9. 🧩 Comprehensive Module Descriptions

### 9.1 Document Parsing Layer: `parsers/document_parser.py`
- **File**: [`src/resume_ats_checker/parsers/document_parser.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/parsers/document_parser.py)
- **Purpose**: Provides a unified, format-agnostic text extraction service for resumes.
- **Key Functions**:
  - `clean_text(text: str) -> str`: Normalizes Windows/Unix carriage returns, removes non-printable bytes, collapses redundant whitespace, and preserves clean paragraph boundaries.
  - `parse_pdf(file_bytes: bytes) -> (str, dict)`: Utilizes `pypdf.PdfReader` to extract text page-by-page, returning formatted text alongside metadata (`page_count`, `char_count`).
  - `parse_docx(file_bytes: bytes) -> (str, dict)`: Utilizes `python-docx` to extract both narrative paragraphs and structured tabular rows (critical for tables listing skills, certifications, and education).
  - `parse_pptx(file_bytes: bytes) -> (str, dict)`: Utilizes `python-pptx` to traverse presentation slides, extracting text from geometric shapes, tables, text frames, and speaker notes.
  - `parse_document(file_name: str, file_bytes: bytes) -> (str, dict)`: Master dispatcher routing by extension (`.pdf`, `.docx`, `.pptx`, `.txt`, `.md`) with graceful legacy fallbacks for `.doc` and `.ppt`.

---

### 9.2 RAG & Vector Retrieval Engine: `rag/vectorstore.py`
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

### 9.3 LangChain ATS Evaluation Chain: `rag/chains.py`
- **File**: [`src/resume_ats_checker/rag/chains.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/rag/chains.py)
- **Purpose**: Executes an elite ATS audit prompt using LangChain and OpenAI structured outputs.
- **Pydantic Schema**: `ATSEvaluationResult`
  - `candidate_name`: Extracted candidate name.
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

### 9.4 Resume Rewrite & Regeneration Engine: `rag/rewrite_chain.py`
- **File**: [`src/resume_ats_checker/rag/rewrite_chain.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/rag/rewrite_chain.py)
- **Purpose**: Complete reconstruction of candidate resumes to target 95%+ ATS match rates while preserving factual integrity.
- **Key Functions**:
  - `generate_suggested_resume(resume_text, job_description, missing_keywords, variation_focus)`:
    - Synthesizes original resume accomplishments with target role requirements.
    - Naturally weaves in missing keywords.
    - Structures content with standard ATS headers: `# NAME`, `## SUMMARY`, `## TECHNICAL SKILLS`, `## PROFESSIONAL EXPERIENCE` (X-Y-Z bullets), `## EDUCATION`, `## CERTIFICATIONS`.
    - **Regeneration Engine**: When `variation_focus` is passed, shifts strategic emphasis (e.g., *Direct Keyword Maximization*, *Senior Architecture Leadership*, or *Delivery Focus*) at temperature 0.7 to generate a distinct, customized resume.

---

### 9.5 Cover Letter Generator: `rag/cover_letter_chain.py`
- **File**: [`src/resume_ats_checker/rag/cover_letter_chain.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/rag/cover_letter_chain.py)
- **Purpose**: Generates persuasive, customized cover letters.
- **Key Functions**:
  - `generate_cover_letter(resume_text, job_description, candidate_name) -> str`:
    - Opens with a hook emphasizing relevant domain achievements.
    - Connects candidate experience to the employer's specific operational challenges.
    - Concludes with a proactive, professional call to action.

---

### 9.6 PostgreSQL Database & Storage Layer: `database/`
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

### 9.7 Application Configuration: `config.py`
- **File**: [`src/resume_ats_checker/config.py`](file:///c:/Debaranjan/Git_Projects/Resume%20ATS%20Checker/src/resume_ats_checker/config.py)
- **Purpose**: Type-safe settings management using `pydantic-settings`.
- **Fields**:
  - `openai_api_key`, `openai_model` (default `gpt-4o-mini`), `embedding_model` (default `text-embedding-3-small`).
  - `postgres_host`, `postgres_port` (default `5432`), `postgres_db`, `postgres_user`, `postgres_password`, `database_url`.
  - Computed property `effective_db_url`: Ensures the modern `postgresql+psycopg://` driver scheme is used.

---

### 9.8 UI Design System & Components: `ui/`
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

### 9.9 Streamlit Application Pages
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

## 10. ⚙️ Environment Variables Reference

| Variable Name | Required | Default Value | Description |
| :--- | :---: | :--- | :--- |
| `OPENAI_API_KEY` | **Yes** | *None* | OpenAI API Key for embeddings and GPT-4o models. |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | Chat model used for scoring, rewriting, and cover letters. |
| `EMBEDDING_MODEL` | No | `text-embedding-3-small` | Embedding model used for semantic RAG chunk vectorization. |
| `POSTGRES_HOST` | No | `localhost` | Hostname of the PostgreSQL database instance. |
| `POSTGRES_PORT` | No | `5432` | Port on which PostgreSQL is listening. |
| `POSTGRES_DB` | No | `postgres` | Target database name. |
| `POSTGRES_USER` | No | `postgres` | Database username. |
| `POSTGRES_PASSWORD` | **Yes** | *None* | Database password. |
| `DATABASE_URL` | No | *Computed* | Complete SQLAlchemy connection string (e.g. `postgresql+psycopg://...`). |

---

## 11. 🧪 Testing & Verification

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

## 12. 🔮 Future Expansion Roadmap

1. **Resume Builder Direct Export**: Connect `pages/2_📝_Resume_Builder.py` with `weasyprint` or `reportlab` to render downloadable PDF templates directly from the rewritten Markdown resume.
2. **Batch Resume Screening**: Support uploading a ZIP or folder of multiple candidate resumes against a single Job Description to rank applicants by ATS match score.
3. **Cover Letter Tone Customizer**: Add tone selection toggles (*Concise & Impactful*, *Warm & Culturally Aligned*, *Executive & Visionary*).
