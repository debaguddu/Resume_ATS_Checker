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
    extract_job_search_criteria,
    determine_job_source_and_channel,
)


def test_search_query_builder():
    print("Testing Job Search Query Construction (LinkedIn, Naukri, Reddit, ATS)...")
    queries = build_job_search_queries(
        job_title="Senior Data Engineer",
        years_exp=8,
        country="India",
        location="Bengaluru",
    )
    assert len(queries) >= 4, f"Expected at least 4 distinct target queries, got {len(queries)}"
    all_queries_text = " ".join(queries)
    assert "site:linkedin.com/jobs/view" in all_queries_text, "Missing direct LinkedIn job queries"
    assert "site:linkedin.com/posts" in all_queries_text, "Missing LinkedIn recruiter/people hiring posts"
    assert "site:naukri.com/job-listings" in all_queries_text, "Missing direct Naukri requisition queries"
    assert "site:reddit.com" in all_queries_text, "Missing Reddit hiring thread queries"
    assert "site:boards.greenhouse.io" in all_queries_text or "site:jobs.lever.co" in all_queries_text, "Missing ATS queries"
    print("  ✓ Multi-channel query builder verified (LinkedIn jobs & posts, Naukri, Reddit, ATS).")


def test_criteria_auto_extraction():
    print("Testing Resume Criteria Extraction (Title, Exp, Country, City)...")
    mock_resume = (
        "DEBARANJAN BEHERA\n"
        "Bengaluru, Karnataka, India | debaranjan@example.com\n"
        "Technical Lead Data Platforms with 12+ years of experience in Apache Spark, Databricks, Snowflake, Azure.\n"
        "Experience:\n"
        "Capgemini - Lead Data Architect (2018 - Present)\n"
    )
    criteria = extract_job_search_criteria(mock_resume)
    assert isinstance(criteria, dict), "Criteria must be a dictionary"
    assert "target_job_title" in criteria and len(criteria["target_job_title"]) > 3
    assert "years_of_experience" in criteria and criteria["years_of_experience"] >= 5
    assert "country" in criteria and criteria["country"] == "India"
    assert "city_or_region" in criteria and criteria["city_or_region"] == "Bengaluru"
    print(f"  ✓ Extracted criteria: {criteria['target_job_title']} | {criteria['years_of_experience']} yrs | {criteria['city_or_region']}, {criteria['country']}.")


def test_channel_badging_and_direct_links():
    print("Testing Direct Job Links & Channel Badging...")
    dom, badge = determine_job_source_and_channel("https://www.linkedin.com/posts/recruiter-hiring-123", "Hiring Lead", "")
    assert "Post" in badge, f"Expected Post badge, got {badge}"

    dom, badge = determine_job_source_and_channel("https://www.naukri.com/job-listings-lead-100", "Lead", "")
    assert "Naukri" in badge

    dom, badge = determine_job_source_and_channel("https://www.reddit.com/r/forhire/comments/xyz", "Hiring", "")
    assert "Reddit" in badge

    dom, badge = determine_job_source_and_channel("https://boards.greenhouse.io/snowflake/jobs/123", "Engineer", "")
    assert "ATS" in badge

    print("  ✓ Source and channel badges accurately assigned.")


def test_job_search_and_fallback():
    print("Testing Fallback Job Searcher (api_key='')...")
    jobs = search_jobs_with_tavily(
        job_title="Technical Lead Data Platforms",
        years_exp=10,
        country="India",
        location="Bengaluru",
        api_key="",  # Explicitly tests fallback generation
        max_results=100,
    )
    assert len(jobs) == 100, f"Expected 100 jobs, got {len(jobs)}"
    sample = jobs[0]
    assert "title" in sample and "Technical Lead Data Platforms" in sample["title"]
    assert "company" in sample
    assert "location" in sample
    assert "url" in sample and sample["url"].startswith("http")
    assert "channel_badge" in sample
    assert "snippet" in sample
    assert "match_score" in sample
    print("  ✓ 100 fallback jobs generated with full metadata, channel badges, and direct links.")


def test_rag_semantic_ranking():
    print("Testing Calibrated RAG Semantic Ranking on Discovered Jobs...")
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
        api_key="",
        max_results=25,
    )
    ranked = rank_jobs_with_rag(mock_resume, jobs)
    assert len(ranked) == 25
    # Verify scores are assigned and sorted descending
    scores = [j["match_score"] for j in ranked]
    assert scores == sorted(scores, reverse=True), "Jobs must be sorted by match_score descending"
    # Ensure calibrated top score is high and not clamped to 50%
    assert scores[0] >= 80.0, f"Top match score should be >= 80%, got {scores[0]}%"
    print(f"  ✓ Calibrated RAG semantic ranking verified (Top: {scores[0]}%, Min: {scores[-1]}%).")


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
    test_criteria_auto_extraction()
    test_channel_badging_and_direct_links()
    test_job_search_and_fallback()
    test_rag_semantic_ranking()
    test_pagination_logic()
    print("\n🎉 ALL MULTI-CHANNEL JOB SEARCHER & RAG RANKING TESTS PASSED!")

