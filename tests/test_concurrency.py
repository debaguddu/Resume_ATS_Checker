"""Concurrency and multi-user isolation verification test suite.

Simulates simultaneous evaluations running in parallel to verify:
1. Zero cross-talk / perfect partitioning of vector embeddings in PostgreSQL.
2. High-performance batch insertion and B-tree index lookup via idx_resume_embeddings_eval_id.
3. Thread-safe connection pool handling under concurrent load.
"""

import sys
import uuid
import concurrent.futures
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from sqlalchemy import text
from resume_ats_checker.database.connection import get_engine, init_db
from resume_ats_checker.database.repository import (
    save_evaluation,
    save_resume_embeddings,
    get_embeddings_by_evaluation_id,
    get_evaluation_by_id,
)


def run_simulated_evaluation(candidate_name: str, num_resume_chunks: int, num_jd_chunks: int) -> str:
    """Simulate a complete evaluation workflow for a candidate."""
    eval_id = str(uuid.uuid4())
    
    # 1. Save evaluation audit record
    eval_data = {
        "id": eval_id,
        "candidate_name": candidate_name,
        "resume_filename": f"{candidate_name.lower().replace(' ', '_')}_resume.pdf",
        "resume_format": "pdf",
        "job_title": f"Senior {candidate_name} Engineer",
        "job_description": f"Target job description for {candidate_name}",
        "resume_text": f"Simulated resume text for {candidate_name}",
        "overall_score": 85,
        "skills_score": 90,
        "experience_score": 80,
        "formatting_score": 95,
        "summary": f"Summary for {candidate_name}",
        "missing_keywords": ["Docker", "Kubernetes"],
        "strengths": ["Leadership", "Architecture"],
        "weaknesses": ["Cloud depth"],
        "suggestions": ["Add metrics"],
    }
    assert save_evaluation(eval_data), f"Failed to save evaluation for {candidate_name}"

    # 2. Build mock embedded chunks (1536 dimensions)
    chunks = []
    for i in range(num_resume_chunks):
        chunks.append({
            "chunk_type": "resume",
            "chunk_index": i,
            "content": f"[{candidate_name}] Resume Experience Chunk #{i}: Led engineering teams and scalable platforms.",
            "embedding": [0.01 * (i + 1)] * 1536,
        })
    for j in range(num_jd_chunks):
        chunks.append({
            "chunk_type": "job_description",
            "chunk_index": j,
            "content": f"[{candidate_name}] Job Requirement Chunk #{j}: Looking for distributed systems expertise.",
            "embedding": [0.02 * (j + 1)] * 1536,
        })

    # 3. Batch save embeddings
    saved = save_resume_embeddings(eval_id, chunks)
    assert saved, f"Failed to save batch embeddings for {candidate_name}"
    return eval_id


def test_concurrent_isolation():
    print("Testing Multi-User Concurrency & Database Vector Isolation...")
    init_ok, init_msg = init_db()
    assert init_ok, f"Init DB failed: {init_msg}"

    engine = get_engine()
    # Verify index exists
    with engine.connect() as conn:
        indexes = [
            r[0]
            for r in conn.execute(
                text("SELECT indexname FROM pg_indexes WHERE tablename = 'resume_embeddings';")
            ).fetchall()
        ]
        assert "idx_resume_embeddings_eval_id" in indexes, "idx_resume_embeddings_eval_id index not found!"
        print("  ✓ Index idx_resume_embeddings_eval_id verified on resume_embeddings.")

    # Execute two parallel evaluations simultaneously using ThreadPoolExecutor
    print("  Executing parallel evaluations for Candidate Alice and Candidate Bob...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_alice = executor.submit(run_simulated_evaluation, "Alice Candidate", 12, 8)
        future_bob = executor.submit(run_simulated_evaluation, "Bob Candidate", 15, 10)

        alice_id = future_alice.result()
        bob_id = future_bob.result()

    print(f"  ✓ Both parallel evaluations completed: Alice ID={alice_id}, Bob ID={bob_id}")

    # Verify Isolation
    alice_embeddings = get_embeddings_by_evaluation_id(alice_id)
    bob_embeddings = get_embeddings_by_evaluation_id(bob_id)

    # 1. Correct count
    assert len(alice_embeddings) == 20, f"Expected 20 chunks for Alice, got {len(alice_embeddings)}"
    assert len(bob_embeddings) == 25, f"Expected 25 chunks for Bob, got {len(bob_embeddings)}"

    # 2. Strict Partitioning (zero cross-talk)
    for chunk in alice_embeddings:
        assert "Alice" in chunk["content"], f"Data contamination detected! Non-Alice content in Alice embeddings: {chunk['content']}"
        assert "Bob" not in chunk["content"], "Data contamination! Bob data found in Alice embeddings!"
        assert chunk["evaluation_id"] == alice_id

    for chunk in bob_embeddings:
        assert "Bob" in chunk["content"], f"Data contamination detected! Non-Bob content in Bob embeddings: {chunk['content']}"
        assert "Alice" not in chunk["content"], "Data contamination! Alice data found in Bob embeddings!"
        assert chunk["evaluation_id"] == bob_id

    print("  ✓ Perfect data isolation confirmed: 0% cross-talk between concurrent candidates.")

    # 3. Clean up test records
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM resume_embeddings WHERE evaluation_id IN (:a, :b)"), {"a": alice_id, "b": bob_id})
        conn.execute(text("DELETE FROM evaluations WHERE id IN (:a, :b)"), {"a": alice_id, "b": bob_id})
        conn.commit()
    print("  ✓ Test artifacts cleaned up successfully.")


if __name__ == "__main__":
    test_concurrent_isolation()
    print("\n🎉 ALL CONCURRENCY & ISOLATION TESTS PASSED SUCCESSFULLY!")
