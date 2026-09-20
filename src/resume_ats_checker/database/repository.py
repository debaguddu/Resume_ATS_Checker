"""Repository layer for persisting evaluations, history, and embeddings."""

import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from resume_ats_checker.database.connection import get_engine

logger = logging.getLogger(__name__)


def save_evaluation(eval_data: Dict[str, Any]) -> bool:
    """Insert or update an evaluation record in PostgreSQL."""
    try:
        engine = get_engine()
        sql = """
        INSERT INTO evaluations (
            id, candidate_name, resume_filename, resume_format, job_title,
            job_description, resume_text, overall_score, skills_score,
            experience_score, formatting_score, summary, missing_keywords,
            strengths, weaknesses, suggestions, suggested_resume, cover_letter
        ) VALUES (
            :id, :candidate_name, :resume_filename, :resume_format, :job_title,
            :job_description, :resume_text, :overall_score, :skills_score,
            :experience_score, :formatting_score, :summary, :missing_keywords,
            :strengths, :weaknesses, :suggestions, :suggested_resume, :cover_letter
        )
        ON CONFLICT (id) DO UPDATE SET
            candidate_name = EXCLUDED.candidate_name,
            overall_score = EXCLUDED.overall_score,
            skills_score = EXCLUDED.skills_score,
            experience_score = EXCLUDED.experience_score,
            formatting_score = EXCLUDED.formatting_score,
            summary = EXCLUDED.summary,
            missing_keywords = EXCLUDED.missing_keywords,
            strengths = EXCLUDED.strengths,
            weaknesses = EXCLUDED.weaknesses,
            suggestions = EXCLUDED.suggestions,
            suggested_resume = EXCLUDED.suggested_resume,
            cover_letter = EXCLUDED.cover_letter;
        """
        params = {
            "id": eval_data["id"],
            "candidate_name": eval_data.get("candidate_name", "Anonymous Candidate"),
            "resume_filename": eval_data.get("resume_filename", "resume"),
            "resume_format": eval_data.get("resume_format", "pdf"),
            "job_title": eval_data.get("job_title", "Target Role"),
            "job_description": eval_data.get("job_description", ""),
            "resume_text": eval_data.get("resume_text", ""),
            "overall_score": int(eval_data.get("overall_score", 0)),
            "skills_score": int(eval_data.get("skills_score", 0)),
            "experience_score": int(eval_data.get("experience_score", 0)),
            "formatting_score": int(eval_data.get("formatting_score", 0)),
            "summary": eval_data.get("summary", ""),
            "missing_keywords": json.dumps(eval_data.get("missing_keywords", [])),
            "strengths": json.dumps(eval_data.get("strengths", [])),
            "weaknesses": json.dumps(eval_data.get("weaknesses", [])),
            "suggestions": json.dumps(eval_data.get("suggestions", [])),
            "suggested_resume": eval_data.get("suggested_resume", ""),
            "cover_letter": eval_data.get("cover_letter", ""),
        }
        with engine.connect() as conn:
            conn.execute(text(sql), params)
            conn.commit()
            return True
    except Exception as exc:
        logger.error("Failed to save evaluation to database: %s", exc)
        return False


def update_suggested_resume(evaluation_id: str, suggested_resume: str) -> bool:
    """Update only the suggested resume field in an existing evaluation."""
    try:
        engine = get_engine()
        sql = "UPDATE evaluations SET suggested_resume = :suggested_resume WHERE id = :id;"
        with engine.connect() as conn:
            conn.execute(text(sql), {"id": evaluation_id, "suggested_resume": suggested_resume})
            conn.commit()
            return True
    except Exception as exc:
        logger.error("Failed to update suggested resume: %s", exc)
        return False


def update_cover_letter(evaluation_id: str, cover_letter: str) -> bool:
    """Update only the cover letter field in an existing evaluation."""
    try:
        engine = get_engine()
        sql = "UPDATE evaluations SET cover_letter = :cover_letter WHERE id = :id;"
        with engine.connect() as conn:
            conn.execute(text(sql), {"id": evaluation_id, "cover_letter": cover_letter})
            conn.commit()
            return True
    except Exception as exc:
        logger.error("Failed to update cover letter: %s", exc)
        return False


def get_recent_evaluations(limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieve recent evaluations from PostgreSQL."""
    try:
        engine = get_engine()
        sql = """
        SELECT id, created_at, candidate_name, resume_filename, job_title, overall_score
        FROM evaluations
        ORDER BY created_at DESC
        LIMIT :limit;
        """
        with engine.connect() as conn:
            result = conn.execute(text(sql), {"limit": limit}).mappings().all()
            return [dict(row) for row in result]
    except Exception as exc:
        logger.warning("Failed to fetch evaluations: %s", exc)
        return []


def get_evaluation_by_id(evaluation_id: str) -> Optional[Dict[str, Any]]:
    """Fetch complete evaluation details by ID."""
    try:
        engine = get_engine()
        sql = "SELECT * FROM evaluations WHERE id = :id;"
        with engine.connect() as conn:
            row = conn.execute(text(sql), {"id": evaluation_id}).mappings().first()
            if not row:
                return None
            data = dict(row)
            # Deserialize JSON fields if returned as strings
            for field in ["missing_keywords", "strengths", "weaknesses", "suggestions"]:
                if isinstance(data.get(field), str):
                    try:
                        data[field] = json.loads(data[field])
                    except Exception:
                        pass
            return data
    except Exception as exc:
        logger.error("Failed to retrieve evaluation %s: %s", evaluation_id, exc)
        return None
