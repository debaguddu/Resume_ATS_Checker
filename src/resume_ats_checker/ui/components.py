"""Reusable UI presentation components for Streamlit."""

from typing import List
import streamlit as st


def render_header(title: str, subtitle: str):
    """Render animated gradient hero header."""
    st.markdown(
        f"""
        <div class="main-header">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_score_color_class(score: int) -> str:
    """Return CSS color class based on score threshold."""
    if score >= 80:
        return "color-excellent"
    elif score >= 65:
        return "color-good"
    elif score >= 50:
        return "color-warning"
    return "color-danger"


def render_metric_cards(overall: int, skills: int, experience: int, formatting: int):
    """Render 4 responsive glassmorphic metric cards."""
    col1, col2, col3, col4 = st.columns(4)

    cards = [
        (col1, "Overall ATS Score", overall, "Weighted match against job requirements"),
        (col2, "Skills Match", skills, "Direct hard skill & tool coverage"),
        (col3, "Experience Relevance", experience, "Seniority, scope & domain depth"),
        (col4, "ATS Formatting", formatting, "Heading structure & readability"),
    ]

    for col, title, score, subtitle in cards:
        color_cls = get_score_color_class(score)
        with col:
            st.markdown(
                f"""
                <div class="score-card">
                    <div class="title">{title}</div>
                    <div class="value {color_cls}">{score}%</div>
                    <div class="subtitle">{subtitle}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_keyword_badges(matched: List[str], missing: List[str]):
    """Render color-coded chips for matched and missing keywords."""
    st.subheader("🎯 Keyword & Skill Diagnostics")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**✅ Matched Skills & Keywords**")
        if matched:
            chips = "".join(f'<span class="badge-matched">{kw}</span>' for kw in matched)
            st.markdown(f'<div class="badge-container">{chips}</div>', unsafe_allow_html=True)
        else:
            st.caption("No direct keyword matches detected.")

    with c2:
        st.markdown("**⚠️ Critical Missing Keywords (From JD)**")
        if missing:
            chips = "".join(f'<span class="badge-missing">{kw}</span>' for kw in missing)
            st.markdown(f'<div class="badge-container">{chips}</div>', unsafe_allow_html=True)
        else:
            st.caption("No critical missing keywords! Great coverage.")


def render_suggestions_list(suggestions: List[str]):
    """Render high-impact resume improvement suggestions."""
    st.subheader("💡 Key Recommendations to Boost ATS Score")
    if not suggestions:
        st.info("No specific suggestions generated.")
        return

    for idx, item in enumerate(suggestions, 1):
        st.markdown(
            f"""
            <div class="callout-box">
                <h4>Recommendation #{idx}</h4>
                <p>{item}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
