"""LangChain evaluation chain for ATS score calculation and key point suggestions."""

import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from resume_ats_checker.config import get_settings

logger = logging.getLogger(__name__)


class ATSEvaluationResult(BaseModel):
    """Structured ATS evaluation metrics and diagnostic feedback."""

    candidate_name: str = Field(description="Name of candidate extracted from resume")
    job_title: str = Field(description="Target job title extracted from job description")
    overall_score: int = Field(description="Overall ATS match percentage between 0 and 100")
    skills_score: int = Field(description="Technical and hard skills match score between 0 and 100")
    experience_score: int = Field(description="Years of experience and seniority match score between 0 and 100")
    formatting_score: int = Field(description="ATS readability and structure score between 0 and 100")
    summary: str = Field(description="2-3 sentence executive evaluation summary explaining the score")
    missing_keywords: List[str] = Field(description="High-priority keywords, skills, or tools present in JD but absent in resume")
    matched_keywords: List[str] = Field(description="Prominent matching keywords and technologies found in both")
    strengths: List[str] = Field(description="3-5 specific areas where the candidate strongly aligns with the role")
    weaknesses: List[str] = Field(description="2-4 noticeable gaps or misalignment areas")
    suggestions: List[str] = Field(description="Actionable, metric-driven bullet point recommendations to boost score")


ATS_PROMPT_TEMPLATE = """You are an elite Applicant Tracking System (ATS) auditor and Senior Executive Technical Recruiter.
Your job is to thoroughly analyze the candidate's resume against the target Job Description using the provided semantic RAG retrieval evidence.

=== RETRIEVED RAG EVIDENCE (JD REQUIREMENTS vs RESUME MATCHES) ===
{rag_context}

=== COMPLETE JOB DESCRIPTION ===
{job_description}

=== COMPLETE RESUME TEXT ===
{resume_text}

=== INSTRUCTIONS ===
1. Calculate a realistic and rigorous ATS match score (0-100). Do not inflate the score.
2. Evaluate:
   - Skills Score: Direct match of primary technologies, libraries, tools, and platforms.
   - Experience Score: Depth of relevant career experience, seniority, and scale of past projects.
   - Formatting Score: Clarity of sections, bullet structure, standard headings, and absence of confusing formatting.
   - Overall Score: Weighted combination (45% skills, 40% experience, 15% formatting).
3. Identify all critical missing keywords that an enterprise ATS (Workday, Taleo, Greenhouse, Lever) would look for.
4. Provide concrete, high-impact suggestions showing how to rewrite experience bullets with the Google X-Y-Z formula: "Accomplished [X] as measured by [Y], by doing [Z]".
"""


def evaluate_resume_ats(
    resume_text: str,
    job_description: str,
    rag_matches: List[Dict[str, Any]],
) -> ATSEvaluationResult:
    """Execute LangChain ATS evaluation chain."""
    settings = get_settings()

    # Format RAG evidence for prompt context
    rag_context_lines = []
    for m in rag_matches[:8]:
        rag_context_lines.append(
            f"• Requirement: {m['requirement_chunk'][:120]}...\n"
            f"  Status: {m['status']} ({m['similarity_score']}%)\n"
            f"  Resume Evidence: {m['best_resume_evidence'][:140]}..."
        )
    rag_context = "\n\n".join(rag_context_lines) if rag_context_lines else "No specific vector matches."

    prompt = ChatPromptTemplate.from_template(ATS_PROMPT_TEMPLATE)
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.2,
        openai_api_key=settings.openai_api_key,
    )

    structured_llm = llm.with_structured_output(ATSEvaluationResult)
    chain = prompt | structured_llm

    result = chain.invoke({
        "rag_context": rag_context,
        "job_description": job_description,
        "resume_text": resume_text,
    })

    return result
