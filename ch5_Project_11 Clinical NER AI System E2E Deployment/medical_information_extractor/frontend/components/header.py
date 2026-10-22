"""
components/header.py
--------------------
Centered hero / landing header for the dark neon dashboard.
"""

import streamlit as st


def render_header() -> None:
    """Render the glowing hero header at the top of the page."""
    st.markdown(
        """
        <div class="hero">
            <div class="badge">✦ AI-Powered Healthcare NLP System</div>
            <h1><span class="pin">🏥</span> Medical Information Extractor</h1>
            <p>Extract structured clinical insights from medical reports in seconds.</p>
            <div class="rule"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
