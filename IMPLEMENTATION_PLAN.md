# Implementation Plan: RAG-based Resume ATS Checker with Streamlit, LangChain, OpenAI & PostgreSQL

Build an enterprise-grade, modular, RAG-powered Resume ATS (Applicant Tracking System) Checker application using **Streamlit**, **LangChain**, **OpenAI**, and **PostgreSQL**. The tool analyzes resumes against job descriptions, provides accurate ATS match scores, lists missing key skills/suggestions, generates a tailored full resume rewrite with regeneration capabilities, produces a personalized cover letter, and supports future template & export pages.

---

## 1. Technical Objectives & Requirements Breakdown

1. **RAG-Based ATS Checker Tool**:
   - Semantic chunking of candidate resumes and target job descriptions.
   - Vector embeddings using OpenAI (`text-embedding-3-small`).
   - Cosine similarity matching between candidate achievements and job requirements.
2. **LangChain & OpenAI**:
   - Structured JSON output parsing via Pydantic (`ATSEvaluationResult`).
   - Weighted scoring: Skills Match (45%), Experience Relevance (40%), ATS Formatting (15%).
   - Generative resume rewriting and tailored cover letter composition.
3. **Database (PostgreSQL)**:
   - Relational audit logging in `evaluations` table.
   - Vector embeddings in `resume_embeddings` (supporting both native `pgvector` and `JSONB` fallback).
4. **Multi-Format Ingestion**:
   - Seamless parsing for **PDF** (`pypdf`), **Word** (`python-docx`), and **PowerPoint** (`python-pptx`) documents with metadata tracking.
5. **Interactive UI (Streamlit)**:
   - Glassmorphic design with metric cards and keyword chips.
   - Suggestions box with actionable Google X-Y-Z recommendations.
   - Complete resume rewrite window with a **Regenerate** engine for alternative strategic angles.
   - Tailored cover letter space with copy/download features.
6. **Modularity & Future Expansion**:
   - Clean package layout under `src/resume_ats_checker/`.
   - Dedicated multi-page foundation (`pages/2_📝_Resume_Builder.py`) for visual resume templates, candidate photo placeholders, and PDF/DOCX exporters.

---

## 2. Directory & Modular Architecture

```
Resume ATS Checker/
├── .env                              # API keys, database settings, model config
├── .env.example                      # Committed sanitized template
├── pyproject.toml                    # UV project dependencies (Python >=3.11)
├── IMPLEMENTATION_PLAN.md            # Complete implementation plan & technical specs
├── README.md                         # Project documentation, diagrams & guides
├── AGENTS.md                         # Workspace rules for synchronization
├── app.py                            # Streamlit entrypoint & dashboard
├── pages/
│   ├── 1_🎯_ATS_Checker.py           # Core ATS Checker & RAG Analyzer workspace
│   └── 2_📝_Resume_Builder.py        # Future expansion template & export studio
├── src/
│   └── resume_ats_checker/
│       ├── __init__.py
│       ├── config.py                 # Pydantic Settings & environment loader
│       ├── database/
│       │   ├── __init__.py
│       │   ├── connection.py         # PostgreSQL connection pool & schema creation
│       │   └── repository.py         # Evaluation history & embeddings CRUD operations
│       ├── parsers/
│       │   ├── __init__.py
│       │   └── document_parser.py    # Multi-format parser (PDF, DOCX, PPTX, TXT)
│       ├── rag/
│       │   ├── __init__.py
│       │   ├── vectorstore.py        # Chunking, embeddings & RAG similarity retrieval
│       │   ├── chains.py             # LangChain structured ATS evaluation
│       │   ├── rewrite_chain.py      # Complete tailored resume rewrite & regeneration
│       │   └── cover_letter_chain.py # Persuasive tailored cover letter generator
│       └── ui/
│           ├── __init__.py
│           ├── styles.py             # Glassmorphic CSS tokens, typography, and dark palette
│           └── components.py         # Reusable UI metric cards, chips, and callouts
└── tests/
    └── test_suite.py                 # Automated verification test suite
```

---

## 3. End-to-End Component Flow

```mermaid
flowchart TD
    User([User / Candidate]) -->|Uploads PDF/DOCX/PPTX| Parser[document_parser.py]
    User -->|Pastes Job Description| UI[Streamlit pages/1_🎯_ATS_Checker.py]
    
    Parser -->|Normalized Text| Chunker[RecursiveCharacterTextSplitter]
    UI -->|JD Text| Chunker
    
    Chunker -->|Document Chunks| Embedder[OpenAI text-embedding-3-small]
    Embedder -->|Vectors| Similarity[Cosine Similarity Engine]
    
    Similarity -->|Ranked Matches & Gaps| LangChain[rag/chains.py: evaluate_resume_ats]
    LangChain -->|ChatOpenAI gpt-4o-mini| Pydantic[Structured ATSEvaluationResult]
    
    Pydantic -->|Save Audit| DB[(PostgreSQL evaluations & embeddings)]
    Pydantic -->|Display Scorecard & Badges| UI
    
    UI -->|Trigger Full Rewrite| Rewrite[rag/rewrite_chain.py]
    Rewrite -->|Tailored Resume| UI
    
    UI -->|Trigger Cover Letter| Cover[rag/cover_letter_chain.py]
    Cover -->|Tailored Letter| UI
```

---

## 4. Module Specifications

### A. Document Parser (`src/resume_ats_checker/parsers/document_parser.py`)
- **Functions**: `parse_document()`, `parse_pdf()`, `parse_docx()`, `parse_pptx()`, `clean_text()`.
- **Inputs**: File name, raw file byte stream.
- **Outputs**: Cleaned plain text string, metadata dictionary (format, counts).

### B. RAG Engine (`src/resume_ats_checker/rag/vectorstore.py`)
- **Functions**: `chunk_text()`, `cosine_similarity()`, `perform_rag_analysis()`.
- **Inputs**: Resume text, Job Description text.
- **Outputs**: List of requirement-to-evidence matches, mean similarity score.

### C. ATS Evaluation Chain (`src/resume_ats_checker/rag/chains.py`)
- **Schema**: `ATSEvaluationResult` (Pydantic model).
- **Functions**: `evaluate_resume_ats()`.
- **Inputs**: Resume text, Job Description text, RAG matches.
- **Outputs**: Validated scores (Overall, Skills, Experience, Formatting), summary, keyword lists, suggestions.

### D. Resume Rewrite Engine (`src/resume_ats_checker/rag/rewrite_chain.py`)
- **Functions**: `generate_suggested_resume()`.
- **Inputs**: Original resume text, Job Description, missing keywords, variation focus.
- **Outputs**: Formatted complete Markdown resume.

### E. Cover Letter Generator (`src/resume_ats_checker/rag/cover_letter_chain.py`)
- **Functions**: `generate_cover_letter()`.
- **Inputs**: Resume text, Job Description, candidate name.
- **Outputs**: Persuasive Markdown cover letter.

### F. Database Persistence (`src/resume_ats_checker/database/`)
- **Modules**: `connection.py` (engine & table DDL), `repository.py` (CRUD helpers).
- **Tables**: `evaluations`, `resume_embeddings`.

---

## 5. Verification & Test Plan

1. **Automated Tests**:
   - Verified multi-format document parser using synthesized PDF, DOCX, and PPTX byte streams.
   - Verified PostgreSQL connection and table operations on port 5432.
2. **Syntax Validation**:
   - Verified zero compilation/syntax errors across all Python files.
3. **Execution**:
   - Ran live Streamlit server on `http://localhost:8501` verifying healthy HTTP 200 response.
