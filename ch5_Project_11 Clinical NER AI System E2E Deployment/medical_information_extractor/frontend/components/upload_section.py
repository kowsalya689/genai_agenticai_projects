"""
components/upload_section.py
----------------------------
The large upload card: drag-and-drop / browse PDF, constraints hint,
and the primary "Extract Information" call-to-action button.

Returns the uploaded file object and whether the extract button was clicked,
so the parent (app.py) can orchestrate the API call.
"""

import streamlit as st

from utils.api import MAX_FILE_SIZE_MB


def render_upload_section():
    """
    Render the upload card.

    Returns:
        (uploaded_file, extract_clicked)
        uploaded_file : Streamlit UploadedFile or None
        extract_clicked : bool
    """
    st.markdown(
        '<div class="card-title" style="border:none;">'
        '<span class="dot" style="background:#2563EB"></span>'
        "<span>📤 Upload Medical Report</span></div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="upload-hint">Supported: <b>PDF only</b> &nbsp;·&nbsp; '
        f"Maximum size: <b>{MAX_FILE_SIZE_MB} MB</b></div>",
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Drag and drop a PDF here, or browse",
        type=["pdf"],
        accept_multiple_files=False,
        label_visibility="collapsed",
    )

    # Show a compact confirmation once a file is selected.
    if uploaded_file is not None:
        size_mb = uploaded_file.size / (1024 * 1024)
        st.success(f"✅ **{uploaded_file.name}** selected · {size_mb:.2f} MB")

    # Primary action button — full width, centered.
    col_left, col_mid, col_right = st.columns([1, 2, 1])
    with col_mid:
        extract_clicked = st.button(
            "🔎  Extract Information",
            type="primary",
            use_container_width=True,
            disabled=uploaded_file is None,
        )

    return uploaded_file, extract_clicked
