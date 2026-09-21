"""Structured resume decomposition and suggestion engine for the Interactive Resume Builder."""

import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from resume_ats_checker.config import get_settings

logger = logging.getLogger(__name__)


class WorkExperienceEntry(BaseModel):
    """Work experience entry with modular, selectable bullet points."""

    company: str = Field(description="Company or organization name")
    role: str = Field(description="Job title or designation")
    location: str = Field(default="", description="Location, e.g. Bengaluru, India or Remote")
    employment_type: str = Field(default="Full-time", description="Full-time, Contract, Part-time, etc.")
    start_date: str = Field(default="", description="Start date, e.g. 06/2020")
    end_date: str = Field(default="Present", description="End date, e.g. Present or 12/2023")
    bullets: List[str] = Field(
        default_factory=list,
        description="Metric-driven accomplishment bullets tailored to target role",
    )


class EducationEntry(BaseModel):
    """Education credential entry."""

    institution: str = Field(description="School, college, or university name")
    degree: str = Field(description="Degree or level, e.g. B. Tech in Computer Science or XII")
    location: str = Field(default="", description="City/Country")
    start_date: str = Field(default="", description="Start date, e.g. 08/2014")
    end_date: str = Field(default="", description="End date, e.g. 06/2018")


class ProjectEntry(BaseModel):
    """Notable project entry."""

    title: str = Field(description="Project name or initiative")
    technologies: str = Field(default="", description="Tech stack used, e.g. Python, Azure, Databricks")
    description: str = Field(default="", description="Brief 1-line project objective")
    bullets: List[str] = Field(
        default_factory=list,
        description="Accomplishment and metric bullets for the project",
    )


class StructuredResume(BaseModel):
    """Complete structured resume schema representing all editable builder sections."""

    full_name: str = Field(default="", description="Candidate full name")
    target_title: str = Field(default="", description="Target job title, e.g. Data Engineering Lead")
    email: str = Field(default="", description="Candidate email address")
    phone: str = Field(default="", description="Contact telephone number")
    location: str = Field(default="", description="City, State / Country")
    linkedin: str = Field(default="", description="LinkedIn profile URL or handle")
    github_portfolio: str = Field(default="", description="GitHub or portfolio website URL")
    professional_summary: str = Field(
        default="",
        description="2-4 sentence tailored executive summary highlighting years of experience and key domain achievements",
    )
    work_experience: List[WorkExperienceEntry] = Field(
        default_factory=list,
        description="Chronological work experience entries with metric-driven bullet points",
    )
    education: List[EducationEntry] = Field(
        default_factory=list,
        description="Academic degrees and qualifications",
    )
    skills_languages: List[str] = Field(default_factory=list, description="Programming and query languages")
    skills_frameworks: List[str] = Field(default_factory=list, description="Libraries, frameworks and platforms")
    skills_cloud_tools: List[str] = Field(default_factory=list, description="Cloud, DevOps and database tools")
    certifications: List[str] = Field(default_factory=list, description="Professional certifications and credentials")
    projects: List[ProjectEntry] = Field(default_factory=list, description="Key projects with quantifiable deliverables")
    awards_scholarships: List[str] = Field(default_factory=list, description="Awards, honors, or scholarships")
    volunteering_leadership: List[str] = Field(default_factory=list, description="Leadership, mentorship, or volunteering")
    publications: List[str] = Field(default_factory=list, description="Published papers, blogs, or patents")


DECOMPOSE_PROMPT = """You are a Principal Technical Recruiter and Executive Resume Architect.
Your task is to parse the candidate's resume (and align it with the target Job Description if provided) into a comprehensive, highly structured resume data model.

=== CANDIDATE RESUME ===
{resume_text}

=== TARGET JOB DESCRIPTION (OPTIONAL ALIGNMENT TARGET) ===
{job_description}

=== INSTRUCTIONS ===
1. Extract and normalize all personal contact details (Name, Title, Email, Phone, Location, Links).
2. Craft an impactful **Professional Summary** weaving target JD requirements with the candidate's actual background.
3. Decompose each job into **Work Experience** entries with clean Company, Role, Location, Dates, and craft 3-7 high-impact, metric-driven bullet points using the Google X-Y-Z formula ("Accomplished [X] measured by [Y], by doing [Z]").
4. Extract all **Education** entries (degrees, schools, dates, locations).
5. Categorize technical **Skills** (Languages, Frameworks, Cloud/Databases/Tools).
6. Capture **Certifications**, **Projects**, **Awards**, **Leadership**, and **Publications**.
7. If the resume has limited details, reasonably extrapolate professional phrasing while preserving candidate honesty.
"""


def decompose_and_tailor_resume(
    resume_text: str,
    job_description: Optional[str] = None,
) -> StructuredResume:
    """Extract and tailor resume sections into structured Pydantic models."""
    settings = get_settings()

    prompt = ChatPromptTemplate.from_template(DECOMPOSE_PROMPT)
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.3,
        openai_api_key=settings.openai_api_key,
    )

    structured_llm = llm.with_structured_output(StructuredResume)
    chain = prompt | structured_llm

    result = chain.invoke({
        "resume_text": resume_text,
        "job_description": job_description or "General senior technical position aligned with candidate background.",
    })

    return result


def generate_default_sample_resume() -> StructuredResume:
    """Return pre-filled sample data matching the enterprise Capgemini / Data Engineering example."""
    return StructuredResume(
        full_name="Debaranjan",
        target_title="Data Engineering Lead",
        email="debaranjanb91@gmail.com",
        phone="+91 98765 43210",
        location="Bengaluru, India",
        linkedin="linkedin.com/in/debaranjan",
        github_portfolio="github.com/debaguddu",
        professional_summary=(
            "Data Engineering Lead with 12+ years of experience in cloud data platforms and large-scale data solutions. "
            "Skilled in data warehousing, SQL, Snowflake-aligned architectures, and PySpark. Delivered 40% pipeline efficiency "
            "improvement at Capgemini. Proven leader in building scalable, governed data platforms."
        ),
        work_experience=[
            WorkExperienceEntry(
                company="Capgemini",
                role="Consultant",
                location="Bengaluru, India",
                employment_type="Full-time",
                start_date="06/2020",
                end_date="Present",
                bullets=[
                    "Lead a team of 15 data engineers to deliver secure and scalable data solutions for a global platform, ensuring 100% adherence to strict SLAs and data governance controls.",
                    "Architect and implement metadata-driven data pipelines using Azure Data Factory and Databricks, improving processing efficiency by 40% and enabling reusable ELT frameworks.",
                    "Drive data governance initiatives using Unity Catalog, implementing fine-grained access control, data cataloging, and ownership models aligned with enterprise standards.",
                    "Led migration of 100+ legacy workflows to serverless data processing architectures, optimizing compute costs and reducing latency.",
                    "Collaborate with business and analytics teams to translate complex requirements into scalable data warehouse solutions aligned with star schema design principles.",
                    "Establish CI/CD pipelines using Azure DevOps, improving deployment reliability and reducing release cycle time.",
                    "Implement monitoring, alerting, and data quality checks using Azure Log Analytics and Power BI, reducing incident response time by 30%.",
                ],
            )
        ],
        education=[
            EducationEntry(
                institution="Gandhi Engineering College",
                degree="B. Tech in Computer Science and Engineering",
                location="Bhubaneswar",
                start_date="08/2014",
                end_date="06/2018",
            ),
            EducationEntry(
                institution="Vivekananda Shiksha Kendra, Bhubaneswar",
                degree="X",
                location="Bhubaneswar",
                start_date="04/2011",
                end_date="03/2012",
            ),
            EducationEntry(
                institution="Kendriya Vidyalaya, Puri",
                degree="XII",
                location="Puri",
                start_date="04/2007",
                end_date="06/2009",
            ),
        ],
        skills_languages=["Python", "SQL", "PySpark", "Scala"],
        skills_frameworks=["Databricks", "Azure Data Factory", "Snowflake", "Delta Lake", "dbt"],
        skills_cloud_tools=["Azure Synapse", "Unity Catalog", "Azure DevOps", "Docker", "Power BI", "PostgreSQL"],
        certifications=[
            "Databricks Certified Data Engineer Associate",
            "Microsoft Certified: Azure Data Engineer Associate (DP-203)",
        ],
        projects=[
            ProjectEntry(
                title="Enterprise Lakehouse Transformation",
                technologies="Azure Databricks, Delta Lake, Unity Catalog",
                description="Modernized enterprise data platform from on-prem Hadoop to Databricks Lakehouse.",
                bullets=[
                    "Reduced batch pipeline execution time from 6 hours to 45 minutes using Delta Lake caching and photon engine.",
                    "Implemented zero-trust data access policy with Unity Catalog across 4 global business units.",
                ],
            )
        ],
        awards_scholarships=["Excellence in Client Delivery Award — Capgemini (2023)"],
        volunteering_leadership=["Mentored 20+ junior data engineers in PySpark and Lakehouse architecture best practices"],
        publications=[],
    )
