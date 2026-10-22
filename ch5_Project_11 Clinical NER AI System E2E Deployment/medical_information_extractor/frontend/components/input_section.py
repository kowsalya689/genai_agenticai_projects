"""
components/input_section.py
---------------------------
Left input pane: two ways to provide a report, plus the Extract button.

    Tab 1 — Upload Medical PDF (drag & drop / browse)
    Tab 2 — Paste Medical Paragraph (large multi-line text area)

Returns everything app.py needs to orchestrate the API call. If a PDF is
uploaded it takes precedence; otherwise pasted text is used.
"""

import streamlit as st

from utils.api import MAX_FILE_SIZE_MB


def render_input_section():
    """
    Render the input pane.

    Returns:
        dict with keys:
            mode : "pdf" | "text" | None
            file : UploadedFile or None
            text : str
            extract_clicked : bool
    """
    st.markdown('<div class="pane-title">Provide a report</div>', unsafe_allow_html=True)

    tab_pdf, tab_text = st.tabs(["📄 Upload PDF", "📝 Paste Text"])

    uploaded_file = None
    with tab_pdf:
        st.markdown(
            f'<div class="hint">Drag &amp; drop supported · PDF only · '
            f"Max {MAX_FILE_SIZE_MB} MB</div>",
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader(
            "Upload medical PDF",
            type=["pdf"],
            accept_multiple_files=False,
            label_visibility="collapsed",
        )
        if uploaded_file is not None:
            size_mb = uploaded_file.size / (1024 * 1024)
            st.caption(f"✅ {uploaded_file.name} · {size_mb:.2f} MB")

    pasted_text = ""
    with tab_text:
        st.markdown(
            '<div class="hint">Paste a medical report / consultation note below.</div>',
            unsafe_allow_html=True,
        )
        pasted_text = st.text_area(
            "Paste medical paragraph",
            height=240,
            placeholder=(
                "e.g. Patient Name: David Wilson\nAge: 58 years\nGender: Male\n"
                "Diagnosis: Community-acquired Pneumonia ...\n"
                "Medications: Azithromycin 500 mg once daily ..."
            ),
            label_visibility="collapsed",
        )

    # Decide which input to use (PDF wins if both are present).
    if uploaded_file is not None:
        mode = "pdf"
    elif pasted_text.strip():
        mode = "text"
    else:
        mode = None

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    extract_clicked = st.button(
        "🔎  Extract Information",
        type="primary",
        use_container_width=True,
        disabled=mode is None,
    )
    if mode is None:
        st.caption("Upload a PDF or paste text to enable extraction.")

    return {
        "mode": mode,
        "file": uploaded_file,
        "text": pasted_text,
        "extract_clicked": extract_clicked,
    }
