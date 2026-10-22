"""
components/sidebar.py
---------------------
Left sidebar: project details, live backend status, workflow diagram,
about section and developer information.

The backend URL input lets the user point the app at wherever their FastAPI
server is running (default http://localhost:8000) without editing any code.
"""

import streamlit as st

from utils.api import check_backend_status


def render_sidebar(base_url: str) -> str:
    """
    Render the sidebar.

    Args:
        base_url: the currently configured backend URL.

    Returns:
        The (possibly updated) backend URL entered by the user.
    """
    with st.sidebar:
        st.markdown("### 🩺 Project Details")
        st.markdown(
            "**Medical Information Extractor** turns unstructured medical "
            "report PDFs into structured, clinician-friendly data using an "
            "NLP entity-extraction pipeline."
        )

        # ---- Backend / FastAPI status --------------------------------------
        st.markdown(
            '<div class="sidebar-section-title">Backend Connection</div>',
            unsafe_allow_html=True,
        )
        updated_url = st.text_input(
            "FastAPI URL",
            value=base_url,
            help="Base URL where your FastAPI backend is running.",
            label_visibility="collapsed",
        )

        is_online, message = check_backend_status(updated_url)
        if is_online:
            st.markdown(
                '<div class="status-badge status-online">'
                '<span class="status-dot online"></span>'
                f"FastAPI Online · {message}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="status-badge status-offline">'
                '<span class="status-dot offline"></span>'
                f"FastAPI Offline · {message}</div>",
                unsafe_allow_html=True,
            )

        # ---- Workflow ------------------------------------------------------
        st.markdown(
            '<div class="sidebar-section-title">Workflow</div>',
            unsafe_allow_html=True,
        )
        steps = [
            "📄 PDF Upload",
            "🔍 Text Extraction",
            "🧠 Entity Extraction (NLP)",
            "🧹 Data Cleaning",
            "💊 Medication Mapping",
            "🗂️ JSON / Table Building",
            "📝 Summary Generation",
        ]
        st.markdown(
            "".join(
                f'<div class="workflow-step">{s}</div>'
                + (
                    '<div style="color:#94A3B8;font-size:12px;'
                    'margin-left:6px;">↓</div>'
                    if i < len(steps) - 1
                    else ""
                )
                for i, s in enumerate(steps)
            ),
            unsafe_allow_html=True,
        )

        # ---- About ---------------------------------------------------------
        st.markdown(
            '<div class="sidebar-section-title">About Project</div>',
            unsafe_allow_html=True,
        )
        with st.expander("What does it do?"):
            st.write(
                "This tool reads medical consultation reports and extracts "
                "patient details, diagnoses, prescribed medications with "
                "dosage and frequency, and laboratory results — then produces "
                "a concise clinical summary. Built on a FastAPI + SciSpaCy "
                "NLP backend."
            )

        # ---- Developer -----------------------------------------------------
        st.markdown(
            '<div class="sidebar-section-title">Developer Information</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            "**Built with:** Streamlit · FastAPI · SciSpaCy · PyMuPDF\n\n"
            "**Type:** Healthcare NLP · Full-stack demo\n\n"
            "_Update this section with your own name, roll number and links._"
        )

    return updated_url
