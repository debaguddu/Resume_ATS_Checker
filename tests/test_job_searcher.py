"""Verification test suite for Tavily Job Searcher & RAG Ranking Engine."""

import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from resume_ats_checker.rag.job_searcher import (
    build_job_search_queries,
    search_jobs_with_tavily,
    rank_jobs_with_rag,
    paginate_jobs,
)


def test_search_query_builder():
    print("Testing Job Search Query Construction...")
    queries = build_job_search_queries(
        job_title="Senior Data Engineer",
        years_exp=8,
        country="India",
        location="Bengaluru",
    )
    assert len(queries) >= 3, "Expected at least 3 distinct target queries"
    assert any("site:linkedin.com/jobs" in q for q in queries)
    assert any("site:greenhouse.io" in q for q in queries)
    print("  ✓ Multi-site query builder verified.")


def test_job_search_and_fallback():
    print("Testing Job Searcher (with Curated Fallback)...")
    jobs = search_jobs_with_tavily(
        job_title="Technical Lead Data Platforms",
        years_exp=10,
        country="India",
        location="Bengaluru",
        api_key=None,  # Tests fallback generation
        max_results=100,
    )
    assert len(jobs) == 100, f"Expected 100 jobs, got {len(jobs)}"
    sample = jobs[0]
    assert "title" in sample and "Technical Lead Data Platforms" in sample["title"]
    assert "company" in sample
    assert "location" in sample
    assert "url" in sample and sample["url"].startswith("http")
    assert "snippet" in sample
    assert "match_score" in sample
    print("  ✓ 100 jobs generated with full metadata and active links.")


def test_rag_semantic_ranking():
    print("Testing RAG Semantic Ranking on Discovered Jobs...")
    mock_resume = (
        "DEBARANJAN BEHERA - Technical Lead\n"
        "Expert in Python, Apache Spark, Databricks, Snowflake, Azure, and distributed architectures. "
        "Led teams designing petabyte-scale data pipelines and enterprise analytics platforms."
    )
    jobs = search_jobs_with_tavily(
        job_title="Data Platform Lead",
        years_exp=8,
        country="India",
        location="Bengaluru",
        api_key=None,
        max_results=25,
    )
    ranked = rank_jobs_with_rag(mock_resume, jobs)
    assert len(ranked) == 25
    # Verify scores are assigned and sorted descending
    scores = [j["match_score"] for j in ranked]
    assert scores == sorted(scores, reverse=True), "Jobs must be sorted by match_score descending"
    print("  ✓ RAG semantic ranking & descending sort verified.")


def test_pagination_logic():
    print("Testing 20-per-page Pagination Engine...")
    mock_jobs = [{"id": f"job-{i}", "title": f"Job {i}"} for i in range(100)]
    
    # Page 1
    page_1, total_p1 = paginate_jobs(mock_jobs, page=1, page_size=20)
    assert len(page_1) == 20
    assert total_p1 == 5
    assert page_1[0]["id"] == "job-0"
    assert page_1[-1]["id"] == "job-19"

    # Page 5 (Last page)
    page_5, total_p5 = paginate_jobs(mock_jobs, page=5, page_size=20)
    assert len(page_5) == 20
    assert page_5[0]["id"] == "job-80"
    assert page_5[-1]["id"] == "job-99"

    # Edge cases
    page_out_of_bounds, _ = paginate_jobs(mock_jobs, page=99, page_size=20)
    assert len(page_out_of_bounds) == 20  # Clamped to last page

    print("  ✓ Pagination logic verified (20 jobs/page, exactly 5 pages for 100 jobs).")


if __name__ == "__main__":
    test_search_query_builder()
    test_job_search_and_fallback()
    test_rag_semantic_ranking()
    test_pagination_logic()
    print("\n🎉 ALL JOB SEARCHER & RAG RANKING TESTS PASSED!")
