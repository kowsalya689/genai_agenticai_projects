"""
components/patient_card.py
--------------------------
Card 1: Patient Information.

Reads `entities.patient_information` from the backend response and displays
Patient, Age, Gender, Doctor, Hospital and Date in a responsive info grid.
"""

import streamlit as st

from utils.styles import COLORS, card_open, card_close


# Maps the display label -> the backend field key.
_FIELDS = [
    ("Patient", "patient"),
    ("Age", "age"),
    ("Gender", "gender"),
    ("Doctor", "doctor"),
    ("Hospital", "hospital"),
    ("Date", "date"),
]


def render_patient_card(patient_info: dict) -> None:
    """
    Render the patient information card.

    Args:
        patient_info: entities["patient_information"] dict.
    """
    patient_info = patient_info or {}

    items_html = ""
    for label, key in _FIELDS:
        value = str(patient_info.get(key, "") or "").strip()
        if value:
            value_html = f'<div class="value">{value}</div>'
        else:
            value_html = '<div class="value empty">Not found</div>'
        items_html += (
            '<div class="info-item">'
            f'<div class="label">{label}</div>'
            f"{value_html}"
            "</div>"
        )

    st.markdown(
        card_open("Patient Information", "🧑‍⚕️", COLORS["primary"])
        + f'<div class="info-grid">{items_html}</div>'
        + card_close(),
        unsafe_allow_html=True,
    )
