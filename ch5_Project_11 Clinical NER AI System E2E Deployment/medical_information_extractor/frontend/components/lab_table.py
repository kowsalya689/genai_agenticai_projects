"""
components/lab_table.py
-----------------------
Card 4: Laboratory Results.

Renders Lab Test / Result as a styled HTML table.
Reads `tables.lab_table` (keys: "Lab Test", "Result").
"""

import streamlit as st

from utils.styles import COLORS, card_open, card_close


def _cell(value: str) -> str:
    value = str(value or "").strip()
    return value if value else '<span class="muted">—</span>'


def render_lab_table(lab_table: list) -> None:
    """
    Render the laboratory results card.

    Args:
        lab_table: tables["lab_table"] — list of {"Lab Test", "Result"}.
    """
    lab_table = lab_table or []

    # Keep rows that have at least a test name or a result.
    rows = [
        row
        for row in lab_table
        if str(row.get("Lab Test", "")).strip()
        or str(row.get("Result", "")).strip()
    ]

    if rows:
        body_rows = "".join(
            "<tr>"
            f"<td><b>{_cell(row.get('Lab Test', ''))}</b></td>"
            f"<td>{_cell(row.get('Result', ''))}</td>"
            "</tr>"
            for row in rows
        )
        body = (
            '<table class="data-table">'
            "<thead><tr><th>Lab Test</th><th>Result</th></tr></thead>"
            f"<tbody>{body_rows}</tbody>"
            "</table>"
        )
    else:
        body = (
            '<div style="color:#64748B;font-style:italic;">'
            "No laboratory results were detected in this report."
            "</div>"
        )

    st.markdown(
        card_open("Laboratory Results", "🧪", COLORS["accent"])
        + body
        + card_close(),
        unsafe_allow_html=True,
    )
