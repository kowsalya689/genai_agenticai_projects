"""
components/summary_card.py
--------------------------
Card 5: Medical Summary.

Renders the backend's `summary` string inside a highlighted container.
The backend joins summary sentences with blank lines ("\\n\\n"), so we split
on those and render each block as its own paragraph.
"""

import html

import streamlit as st

from utils.styles import COLORS, card_open, card_close


def render_summary_card(summary: str) -> None:
    """
    Render the medical summary card.

    Args:
        summary: the backend `summary` string.
    """
    summary = (summary or "").strip()

    if summary:
        paragraphs = [p.strip() for p in summary.split("\n\n") if p.strip()]
        # Escape to be safe, since summary is text (not trusted HTML).
        inner = "".join(f"<p>{html.escape(p)}</p>" for p in paragraphs)
        body = f'<div class="summary-box">{inner}</div>'
    else:
        body = (
            '<div class="summary-box" style="color:#64748B;font-style:italic;">'
            "No summary could be generated for this report."
            "</div>"
        )

    st.markdown(
        card_open("Medical Summary", "📝", COLORS["secondary"])
        + body
        + card_close(),
        unsafe_allow_html=True,
    )
