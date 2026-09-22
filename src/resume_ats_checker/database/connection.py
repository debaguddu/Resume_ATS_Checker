"""Database connection and table initialization for PostgreSQL."""

import logging
from typing import Tuple, Optional
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.orm import declarative_base, sessionmaker

from resume_ats_checker.config import get_settings

logger = logging.getLogger(__name__)

Base = declarative_base()
_engine: Optional[Engine] = None
SessionLocal = sessionmaker(autocommit=False, autoflush=False)


def get_engine() -> Engine:
    """Return singleton SQLAlchemy engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        db_url = settings.effective_db_url
        _engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            connect_args={"connect_timeout": 5},
        )
        SessionLocal.configure(bind=_engine)
    return _engine


def check_connection() -> Tuple[bool, str]:
    """Check whether connection to PostgreSQL database succeeds."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();")).scalar()
            return True, f"Connected: {result[:50]}..."
    except Exception as exc:
        logger.warning("Database connection check failed: %s", exc)
        return False, str(exc)


def init_db() -> Tuple[bool, str]:
    """Create necessary database tables and pgvector extension if supported."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # 1. Try enabling pgvector if installed
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
                has_vector = True
            except Exception:
                conn.rollback()
                has_vector = False

            # 2. Create evaluations table
            create_eval_sql = """
            CREATE TABLE IF NOT EXISTS evaluations (
                id VARCHAR(64) PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                candidate_name VARCHAR(255),
                resume_filename VARCHAR(255) NOT NULL,
                resume_format VARCHAR(32),
                job_title VARCHAR(255),
                job_description TEXT NOT NULL,
                resume_text TEXT NOT NULL,
                overall_score INTEGER,
                skills_score INTEGER,
                experience_score INTEGER,
                formatting_score INTEGER,
                summary TEXT,
                missing_keywords JSONB,
                strengths JSONB,
                weaknesses JSONB,
                suggestions JSONB,
                suggested_resume TEXT,
                cover_letter TEXT
            );
            """
            conn.execute(text(create_eval_sql))

            # 3. Create embeddings table
            if has_vector:
                create_emb_sql = """
                CREATE TABLE IF NOT EXISTS resume_embeddings (
                    id SERIAL PRIMARY KEY,
                    evaluation_id VARCHAR(64) NOT NULL,
                    chunk_type VARCHAR(32) NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    embedding vector(1536),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            else:
                create_emb_sql = """
                CREATE TABLE IF NOT EXISTS resume_embeddings (
                    id SERIAL PRIMARY KEY,
                    evaluation_id VARCHAR(64) NOT NULL,
                    chunk_type VARCHAR(32) NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    embedding JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            conn.execute(text(create_emb_sql))
            # 4. Create index on evaluation_id for rapid multi-user partitioned lookups
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_resume_embeddings_eval_id ON resume_embeddings(evaluation_id);"))
            conn.commit()
            return True, f"Database initialized successfully (pgvector: {has_vector})."
    except Exception as exc:

        logger.error("Failed to initialize database: %s", exc)
        return False, str(exc)
