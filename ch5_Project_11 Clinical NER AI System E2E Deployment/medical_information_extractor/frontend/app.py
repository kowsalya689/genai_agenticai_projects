"""
app.py
------
Medical Information Extractor — dark neon Streamlit dashboard.

Layout:
    ┌──────────────────────── HERO (full width) ────────────────────────┐
    │  INPUT PANE (left)              │   RESULTS PANE (right)           │
    │   · Upload PDF / Paste Text     │    · slides in after extraction  │
    │   · Extract Information         │    · 5 cards + download bar       │
    └───────────────────────────────────────────────────────────────────┘

No business logic and no mock data — every value shown comes from the existing
FastAPI `/extract` response. Pasted text is rendered to an in-memory PDF and
sent to the same endpoint, so the backend is never modified.

Run:
    streamlit run app.py
Backend (separate terminal):
    cd ../backend && uvicorn app:app --reload
"""

import time

import streamlit as st

from utils.api import (
    DEFAULT_BASE_URL,
    extract_information,
    BackendConnectionError,
    BackendTimeoutError,
    FileTooLargeError,
    APIResponseError,
    BackendError,
)
from utils.text_pdf import text_to_pdf_bytes
from utils.styles import inject_global_styles, neon_loader, empty_state

from components.header import render_header
from components.input_section import render_input_section
from components.patient_card import render_patient_card
from components.disease_card import render_disease_card
from components.medication_table import render_medication_table
from components.lab_table import render_lab_table
from components.summary_card import render_summary_card
from components.download_section import render_download_section


# ---------------------------------------------------------------------------
# Page config — must be the first Streamlit call.
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Medical Information Extractor",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(inject_global_styles(), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
st.session_state.setdefault("result", None)
st.session_state.setdefault("source_filename", "report")
st.session_state.setdefault("pending", False)          # extraction in progress
st.session_state.setdefault("pending_payload", None)   # (bytes, filename)

# Handle a reset requested by the download bar on the previous run.
if st.session_state.get("_reset"):
    st.session_state["result"] = None
    st.session_state["source_filename"] = "report"
    st.session_state["pending"] = False
    st.session_state["pending_payload"] = None
    st.session_state["_reset"] = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _show_error(exc: Exception) -> None:
    """Translate an exception into a friendly, actionable message."""
    if isinstance(exc, FileTooLargeError):
        st.error(f"📦 {exc}")
    elif isinstance(exc, BackendConnectionError):
        st.error(
            f"🔌 {exc}\n\nStart the FastAPI backend (uvicorn app:app --reload) "
            "and check your network connection."
        )
    elif isinstance(exc, BackendTimeoutError):
        st.error(f"⏳ {exc}")
    elif isinstance(exc, APIResponseError):
        st.error(f"⚠️ {exc}")
    elif isinstance(exc, BackendError):
        st.error(f"❌ {exc}")
    else:
        st.error(f"❌ Something went wrong: {exc}")


def _render_results(result: dict) -> None:
    """Render the five result cards + download bar in the right pane."""
    entities = result.get("entities", {}) or {}
    tables = result.get("tables", {}) or {}
    summary = result.get("summary", "") or ""

    patient_info = entities.get("patient_information", {}) or {}
    clinical_info = entities.get("clinical_information", {}) or {}
    medications = entities.get("medications", []) or []

    render_patient_card(patient_info)
    render_disease_card(clinical_info.get("disease", []))
    render_medication_table(tables.get("medication_table", []), medications)
    render_lab_table(tables.get("lab_table", []))
    render_summary_card(summary)

    with st.expander("🔧 View raw API response (JSON)"):
        st.json(result)

    render_download_section(result, st.session_state.get("source_filename", "report"))


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
render_header()

# ---------------------------------------------------------------------------
# Two-pane body
# ---------------------------------------------------------------------------
left, right = st.columns([1, 1.35], gap="large")

# ----- LEFT: input pane -----------------------------------------------------
with left:
    form = render_input_section()

    # Queue an extraction: capture the payload, flip to "pending", rerun so the
    # right pane can paint the loader before we make the blocking API call.
    if form["extract_clicked"] and form["mode"] is not None:
        try:
            if form["mode"] == "pdf":
                file = form["file"]
                payload = (file.getvalue(), file.name)
            else:  # text -> in-memory PDF
                payload = (text_to_pdf_bytes(form["text"]), "pasted_text.pdf")
            st.session_state["pending_payload"] = payload
            st.session_state["source_filename"] = payload[1]
            st.session_state["pending"] = True
            st.session_state["result"] = None
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            _show_error(exc)

# ----- RIGHT: results pane --------------------------------------------------
with right:
    right_slot = st.empty()

    if st.session_state["pending"]:
        # 1) paint the neon loader immediately
        right_slot.markdown(
            neon_loader("Analyzing report and extracting medical information…"),
            unsafe_allow_html=True,
        )
        # 2) run the blocking backend call
        try:
            file_bytes, filename = st.session_state["pending_payload"]
            response = extract_information(
                file_bytes=file_bytes,
                filename=filename,
                base_url=DEFAULT_BASE_URL,
            )
            st.session_state["result"] = response
        except Exception as exc:  # noqa: BLE001
            st.session_state["result"] = None
            right_slot.empty()
            _show_error(exc)
        finally:
            st.session_state["pending"] = False
            st.session_state["pending_payload"] = None
        # 3) rerun to reveal results with the slide-in animation
        if st.session_state["result"] is not None:
            time.sleep(0.15)
            st.rerun()

    elif st.session_state["result"] is not None:
        with right_slot.container():
            st.success("✅ Extraction complete.")
            _render_results(st.session_state["result"])

    else:
        right_slot.markdown(empty_state(), unsafe_allow_html=True)
