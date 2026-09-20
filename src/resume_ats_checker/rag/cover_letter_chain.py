"""LangChain cover letter generation engine."""

import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from resume_ats_checker.config import get_settings

logger = logging.getLogger(__name__)

COVER_LETTER_TEMPLATE = """You are a senior executive career coach and expert communications writer.
Your job is to generate an exceptional, tailored cover letter that clearly connects the candidate's actual accomplishments to the employer's exact needs.

=== CANDIDATE RESUME ===
{resume_text}

=== TARGET JOB DESCRIPTION ===
{job_description}

=== CANDIDATE NAME ===
{candidate_name}

=== GUIDELINES FOR THE COVER LETTER ===
1. **Tone**: Confident, authentic, professional, and enthusiastic. Avoid cliches like "I am writing to express my interest in...".
2. **Hook**: Open with a compelling statement that highlights immediate value, relevant domain expertise, and passion for the specific role.
3. **Core Evidence (2-3 body paragraphs)**:
   - Identify the top 2-3 most critical problems described in the Job Description.
   - Prove candidate capability using specific achievements, metrics, and technologies from their resume.
4. **Cultural Alignment & Enthusiasm**: Briefly mention why this company/mission excites the candidate.
5. **Call to Action**: A polite, proactive closing inviting a conversation.
6. Provide ONLY the complete cover letter text formatted in clean Markdown.
"""


def generate_cover_letter(
    resume_text: str,
    job_description: str,
    candidate_name: str = "Candidate",
) -> str:
    """Generate a persuasive, custom cover letter matching resume achievements to job requirements."""
    settings = get_settings()

    prompt = ChatPromptTemplate.from_template(COVER_LETTER_TEMPLATE)
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.5,
        openai_api_key=settings.openai_api_key,
    )

    chain = prompt | llm | StrOutputParser()

    result = chain.invoke({
        "resume_text": resume_text,
        "job_description": job_description,
        "candidate_name": candidate_name,
    })

    return result.strip()
