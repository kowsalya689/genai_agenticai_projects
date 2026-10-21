"""Turn an uploaded file (.txt, .md, .pdf, .docx) into plain text."""
import io
from pathlib import Path

from backend.core.errors import AppError

SUPPORTED = {".txt", ".md", ".text", ".pdf", ".docx"}


def extract_text(filename: str, data: bytes) -> str:
    ext = Path(filename or "").suffix.lower()
    if ext not in SUPPORTED:
        raise AppError(415, "unsupported_file", f"Unsupported file type '{ext or 'unknown'}'. Use .txt, .md, .pdf or .docx.")
    try:
        if ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(data))
            text = "\n".join((p.extract_text() or "") for p in reader.pages)
        elif ext == ".docx":
            from docx import Document
            doc = Document(io.BytesIO(data))
            text = "\n".join(p.text for p in doc.paragraphs)
        else:
            try:
                text = data.decode("utf-8-sig")
            except UnicodeDecodeError:
                text = data.decode("latin-1")
    except AppError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise AppError(422, "unreadable_file", f"Could not read this file: {exc}") from exc
    text = text.strip()
    if not text:
        raise AppError(422, "empty_file", "No text could be extracted. Scanned PDFs need OCR first.")
    return text
