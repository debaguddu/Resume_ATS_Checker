"""Custom CSS styles, glassmorphic themes, and typography for Streamlit."""

CUSTOM_CSS = """
<style>
/* Import Inter Font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* App Header Gradient Glow */
.main-header {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%);
    border-radius: 16px;
    padding: 2.2rem 2.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 10px 30px -10px rgba(79, 70, 229, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.12);
    position: relative;
    overflow: hidden;
}

.main-header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 350px;
    height: 350px;
    background: radial-gradient(circle, rgba(129, 140, 248, 0.25) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}

.main-header h1 {
    color: #ffffff !important;
    font-size: 2.4rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin: 0 0 0.5rem 0;
}

.main-header p {
    color: #c7d2fe !important;
    font-size: 1.05rem;
    margin: 0;
    max-width: 680px;
    line-height: 1.5;
}

/* Glassmorphic Metric Cards */
.metric-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.2rem;
    margin-bottom: 2rem;
}

.score-card {
    background: rgba(30, 41, 59, 0.7);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.score-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 24px -10px rgba(0, 0, 0, 0.5);
}

.score-card .title {
    color: #94a3b8;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
    margin-bottom: 0.6rem;
}

.score-card .value {
    font-size: 2.6rem;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 0.4rem;
}

.score-card .subtitle {
    font-size: 0.8rem;
    color: #64748b;
}

/* Status colors */
.color-excellent { color: #10b981; }
.color-good { color: #38bdf8; }
.color-warning { color: #f59e0b; }
.color-danger { color: #ef4444; }

/* Keyword Badges */
.badge-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin: 0.8rem 0 1.5rem 0;
}

.badge-matched {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
    padding: 0.35rem 0.8rem;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 500;
}

.badge-missing {
    background: rgba(239, 68, 68, 0.15);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.3);
    padding: 0.35rem 0.8rem;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 500;
}

/* Action Box Callouts */
.callout-box {
    background: rgba(15, 23, 42, 0.6);
    border-left: 4px solid #6366f1;
    border-radius: 0 12px 12px 0;
    padding: 1.2rem 1.5rem;
    margin: 1rem 0;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.callout-box h4 {
    margin: 0 0 0.5rem 0;
    color: #818cf8;
    font-size: 1.05rem;
    font-weight: 600;
}

.callout-box p {
    color: #cbd5e1;
    margin: 0;
    font-size: 0.95rem;
    line-height: 1.5;
}

/* Code & Editor Previews */
.document-preview-box {
    background: #090d16;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 1.8rem;
    color: #e2e8f0;
    font-family: 'Inter', sans-serif;
    line-height: 1.65;
    max-height: 600px;
    overflow-y: auto;
    box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.5);
}
</style>
"""


def apply_custom_styles():
    """Inject custom styles into Streamlit app."""
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
