"""
utils/text_pdf.py
-----------------
Convert pasted medical text into an in-memory PDF.

The backend's ONLY entry point (`POST /extract`) accepts a PDF file upload.
To let users paste raw report text WITHOUT changing the backend, we render
that text into a lightweight, text-layer PDF and send it to the same endpoint.
The backend then reads it exactly as it would any uploaded PDF.

Uses fpdf2 (pure-Python, no system dependencies).
"""

from __future__ import annotations

from fpdf import FPDF

_MARGIN_MM = 15
_LINE_HEIGHT_MM = 6


def text_to_pdf_bytes(text: str) -> bytes:
    """
    Render plain medical text into PDF bytes with a real text layer.

    Args:
        text: the pasted report text.

    Returns:
        PDF file contents as bytes, suitable for uploading to /extract.
    """
    # fpdf2 core fonts are Latin-1; sanitize so unexpected unicode never crashes
    # the render. Does not affect the ASCII-heavy fields the backend parses.
    safe_text = (text or "").encode("latin-1", "replace").decode("latin-1")

    pdf = FPDF(format="A4")
    pdf.set_margins(_MARGIN_MM, _MARGIN_MM, _MARGIN_MM)
    pdf.set_auto_page_break(auto=True, margin=_MARGIN_MM)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)

    usable_width = pdf.epw  # effective page width (page minus L/R margins)

    for raw_line in safe_text.split("\n"):
        line = raw_line.rstrip()
        if line == "":
            pdf.ln(_LINE_HEIGHT_MM)
            continue
        pdf.multi_cell(
            w=usable_width,
            h=_LINE_HEIGHT_MM,
            text=line,
            new_x="LMARGIN",
            new_y="NEXT",
        )

    # fpdf2 returns a bytearray from output(); normalize to bytes.
    return bytes(pdf.output())
