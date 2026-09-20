# 🎯 Enterprise AI Resume ATS Suite

An enterprise-grade, modular, **RAG-powered Resume ATS (Applicant Tracking System) Checker** built with **Streamlit**, **LangChain**, **OpenAI**, and **PostgreSQL**.

---

## ✨ Features

- **Multi-Format Document Parsing**: Upload resumes seamlessly in **PDF**, **DOCX**, **PPTX**, and **TXT** formats.
- **RAG Semantic Analysis**: Chunks resumes and job descriptions to compute contextual cosine similarity against job requirements.
- **ATS Scorecard & Diagnostics**:
  - **Overall Score** (0–100%)
  - **Skills Match** (0–100%)
  - **Experience Relevance** (0–100%)
  - **ATS Formatting & Structure** (0–100%)
- **Missing Keywords & Skill Chips**: Highlights matched skills in green and missing high-priority keywords in red.
- **Key Recommendations Box**: Concrete, metric-driven suggestions following the Google X-Y-Z formula.
- **Suggested Complete Resume**:
  - Rewrites the entire resume tailored to the target role.
  - **Regenerate Button**: Generates fresh variations with different strategic focuses (e.g. Keyword Maximization, Senior Leadership).
  - Download as Markdown (`.md`).
- **Tailored Cover Letter**: One-click custom cover letter generator directly mapping candidate achievements to employer challenges.
- **PostgreSQL Persistence**: Saves all audit history, match scores, resumes, and generated cover letters.
- **Modular Multi-Page Architecture**: Designed with a clean package structure and a scaffolded **Resume Builder & Template Studio** for future template selection, photo uploading, and PDF/DOCX exporting.

---

## 🏗️ Project Architecture

```
Resume ATS Checker/
├── .env                              # Local secrets & credentials (git-ignored)
├── .env.example                      # Configuration template
├── pyproject.toml                    # UV project configuration & dependencies
├── app.py                            # Streamlit entrypoint & dashboard
├── pages/
│   ├── 1_🎯_ATS_Checker.py           # Core ATS Checker & RAG Analyzer
│   └── 2_📝_Resume_Builder.py        # Template studio & export workspace
├── src/
│   └── resume_ats_checker/
│       ├── config.py                 # Pydantic Settings & environment loader
│       ├── database/
│       │   ├── connection.py         # PostgreSQL connection pool & schema creation
│       │   └── repository.py         # History & evaluation CRUD operations
│       ├── parsers/
│       │   └── document_parser.py    # Multi-format parser (PDF, DOCX, PPTX)
│       ├── rag/
│       │   ├── vectorstore.py        # Chunking, embeddings & RAG similarity retrieval
│       │   ├── chains.py             # LangChain structured ATS evaluation
│       │   ├── rewrite_chain.py      # Complete resume rewrite & regeneration
│       │   └── cover_letter_chain.py # Persuasive cover letter generation
│       └── ui/
│           ├── styles.py             # Glassmorphic CSS tokens & themes
│           └── components.py         # Reusable UI widgets & metric cards
└── tests/
    └── test_suite.py                 # Multi-format parser & system verification
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.11+ (Managed automatically via [uv](https://docs.astral.sh/uv/))
- Local PostgreSQL instance (or Docker container)
- OpenAI API Key

### 2. Environment Configuration
Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```
Edit `.env`:
```env
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password
DATABASE_URL=postgresql+psycopg://postgres:your_postgres_password@localhost:5432/postgres
```

### 3. Install Dependencies
Using `uv`:
```bash
uv sync
```

### 4. Run Automated Tests
```bash
uv run python tests/test_suite.py
```

### 5. Launch the Streamlit App
```bash
uv run streamlit run app.py
```
Open your browser at `http://localhost:8501`.
