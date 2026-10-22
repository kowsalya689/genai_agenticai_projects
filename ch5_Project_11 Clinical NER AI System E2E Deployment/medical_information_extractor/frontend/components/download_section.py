"""
components/download_section.py
------------------------------
Action bar shown after a successful extraction:

    · Download JSON  — the full backend response, unchanged.
    · Download CSV   — a flattened, sectioned CSV built from the tables.
    · Clear Results  — clears the current result and returns to the input state.

`Clear Results` sets a flag in st.session_state; app.py reads it and reruns,
so this component stays presentation-only.
"""

import io
import json

import pandas as pd
import streamlit as st


def _build_csv(response: dict) -> str:
    """Flatten the backend response into a single, sectioned CSV."""
    tables = response.get("tables", {}) or {}
    buffer = io.StringIO()

    def _write_section(title: str, frame: pd.DataFrame) -> None:
        buffer.write(f"{title}\n")
        if frame.empty:
            buffer.write("(none)\n")
        else:
            frame.to_csv(buffer, index=False)
        buffer.write("\n")

    _write_section("PATIENT INFORMATION", pd.DataFrame(tables.get("patient_table", []) or []))
    _write_section("DISEASES", pd.DataFrame(tables.get("disease_table", []) or []))
    _write_section("MEDICATIONS", pd.DataFrame(tables.get("medication_table", []) or []))
    _write_section("LABORATORY RESULTS", pd.DataFrame(tables.get("lab_table", []) or []))

    return buffer.getvalue()


def render_download_section(response: dict, source_filename: str = "report") -> None:
    """
    Render the download / reset action bar.

    Args:
        response:        the full backend response dict.
        source_filename: original PDF name (or 'pasted_text'), used for filenames.
    """
    base_name = source_filename.rsplit(".", 1)[0] if source_filename else "report"

    json_bytes = json.dumps(response, indent=2, ensure_ascii=False).encode("utf-8")
    csv_text = _build_csv(response)

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            "⬇️ Download JSON",
            data=json_bytes,
            file_name=f"{base_name}_extracted.json",
            mime="application/json",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "⬇️ Download CSV",
            data=csv_text,
            file_name=f"{base_name}_extracted.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col3:
        if st.button("🧹 Clear Results", use_container_width=True):
            st.session_state["_reset"] = True
            st.rerun()
