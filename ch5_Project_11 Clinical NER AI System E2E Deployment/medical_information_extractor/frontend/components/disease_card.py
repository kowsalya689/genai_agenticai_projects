"""
components/disease_card.py
--------------------------
Card 2: Disease Information.

Renders the list of diagnosed diseases as a styled bullet list.
Reads `entities.clinical_information.disease` (a list of strings).
"""

import streamlit as st

from utils.styles import COLORS, card_open, card_close


def render_disease_card(diseases: list) -> None:
    """
    Render the disease information card.

    Args:
        diseases: list of disease name strings.
    """
    diseases = diseases or []

    if diseases:
        items = "".join(
            f'<li><span class="pill-icon">🩸</span>{str(d).strip()}</li>'
            for d in diseases
            if str(d).strip()
        )
        body = f'<ul class="disease-list">{items}</ul>'
    else:
        body = (
            '<div style="color:#64748B;font-style:italic;">'
            "No diseases were detected in this report."
            "</div>"
        )

    st.markdown(
        card_open("Disease Information", "🦠", COLORS["danger"])
        + body
        + card_close(),
        unsafe_allow_html=True,
    )
