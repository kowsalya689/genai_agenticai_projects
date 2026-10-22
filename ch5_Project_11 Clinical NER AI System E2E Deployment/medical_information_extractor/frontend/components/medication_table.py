"""
components/medication_table.py
------------------------------
Card 3: Medication Table.

Renders Medicine / Dosage / Frequency as a styled HTML table.

Prefers `tables.medication_table` (keys: Medicine, Dosage, Frequency).
Falls back to `entities.medications` (keys: medicine, dosage, frequency)
if the tables block is missing — both are produced by the backend.
"""

import streamlit as st

from utils.styles import COLORS, card_open, card_close


def _normalize_rows(medication_table: list, medications: list) -> list:
    """Return a list of (medicine, dosage, frequency) tuples from either source."""
    rows = []

    if medication_table:
        for row in medication_table:
            rows.append(
                (
                    row.get("Medicine", ""),
                    row.get("Dosage", ""),
                    row.get("Frequency", ""),
                )
            )
    elif medications:
        for row in medications:
            rows.append(
                (
                    row.get("medicine", ""),
                    row.get("dosage", ""),
                    row.get("frequency", ""),
                )
            )
    return rows


def _cell(value: str) -> str:
    """Render a table cell, showing a muted dash for empty values."""
    value = str(value or "").strip()
    return value if value else '<span class="muted">—</span>'


def render_medication_table(medication_table: list, medications: list) -> None:
    """
    Render the medication table card.

    Args:
        medication_table: tables["medication_table"] (may be empty).
        medications:      entities["medications"] fallback (may be empty).
    """
    rows = _normalize_rows(medication_table or [], medications or [])

    if rows:
        body_rows = "".join(
            "<tr>"
            f"<td><b>{_cell(med)}</b></td>"
            f"<td>{_cell(dose)}</td>"
            f"<td>{_cell(freq)}</td>"
            "</tr>"
            for med, dose, freq in rows
        )
        body = (
            '<table class="data-table">'
            "<thead><tr>"
            "<th>Medicine</th><th>Dosage</th><th>Frequency</th>"
            "</tr></thead>"
            f"<tbody>{body_rows}</tbody>"
            "</table>"
        )
    else:
        body = (
            '<div style="color:#64748B;font-style:italic;">'
            "No medications were detected in this report."
            "</div>"
        )

    st.markdown(
        card_open("Medication Table", "💊", COLORS["secondary"])
        + body
        + card_close(),
        unsafe_allow_html=True,
    )
