"""LangChain resume rewriting and regeneration engine."""

import logging
from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from resume_ats_checker.config import get_settings

logger = logging.getLogger(__name__)

REWRITE_PROMPT_TEMPLATE = """You are a Master Resume Writer and Career Strategist with a track record of getting candidates into Tier-1 tech, finance, and Fortune 500 companies.

Your task is to completely rewrite and reconstruct the candidate's resume so it achieves a 95%+ match against the target Job Description while remaining 100% honest to the candidate's genuine background.

=== CANDIDATE ORIGINAL RESUME ===
{resume_text}

=== TARGET JOB DESCRIPTION ===
{job_description}

=== IDENTIFIED GAPS & MISSING KEYWORDS TO INTEGRATE ===
{missing_keywords}

=== CREATIVE REGENERATION ANGLE ===
{focus_instruction}

=== STRUCTURAL & ATS RULES ===
1. Professional Clean Markdown format.
2. Standard ATS Section Headers:
   # [CANDIDATE FULL NAME]
   [Location] | [Email] | [LinkedIn URL] | [GitHub/Portfolio URL]

   ## PROFESSIONAL SUMMARY
   3-4 powerful sentences weaving the target role title, years of experience, core technical stack, and standout career impact.

   ## TECHNICAL SKILLS
   Categorize clearly (e.g., Languages, Frameworks & Libraries, Cloud & DevOps, Databases, Tools & Architecture).
   Ensure target keywords from the Job Description are prominently integrated.

   ## PROFESSIONAL EXPERIENCE
   For each role:
   **[Company Name]** — *[Job Title]* ([Dates of Employment])
   - Craft 3 to 5 high-impact bullet points following the Google X-Y-Z formula: "Accomplished [X] measured by [Y], by doing [Z]".
   - Emphasize quantifiable business outcomes (latencies reduced, revenue enabled, team velocity increased, efficiency boosted).

   ## EDUCATION
   [Degree], [Major] — [University Name], [Graduation Year]

   ## CERTIFICATIONS & KEY PROJECTS
   List relevant credentials and top projects that prove required skills.

Provide ONLY the complete, ready-to-use rewritten resume text. Do not add introductory chit-chat.
"""


def generate_suggested_resume(
    resume_text: str,
    job_description: str,
    missing_keywords: List[str],
    variation_focus: Optional[str] = None,
) -> str:
    """Generate or regenerate a complete, tailored resume optimized for the target job description."""
    settings = get_settings()

    if not variation_focus:
        focus_instruction = "Standard High-Impact ATS Alignment: Emphasize direct keyword matching, clean action verbs, and clear quantifiable deliverables."
    else:
        focus_instruction = f"Targeted Emphasis: {variation_focus}. Reframe accomplishments to maximize alignment with this strategic angle."

    prompt = ChatPromptTemplate.from_template(REWRITE_PROMPT_TEMPLATE)
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.7 if variation_focus else 0.4,
        openai_api_key=settings.openai_api_key,
    )

    chain = prompt | llm | StrOutputParser()

    formatted_keywords = ", ".join(missing_keywords) if missing_keywords else "None explicitly missing."
    result = chain.invoke({
        "resume_text": resume_text,
        "job_description": job_description,
        "missing_keywords": formatted_keywords,
        "focus_instruction": focus_instruction,
    })

    return result.strip()
