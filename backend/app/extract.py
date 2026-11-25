"""Turn an uploaded resume (PDF, DOCX, TXT/MD) into plain text."""

from __future__ import annotations

import io
import re

from docx import Document
from pypdf import PdfReader


class ExtractError(ValueError):
    pass


def _clean(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)


def _docx(data: bytes) -> str:
    doc = Document(io.BytesIO(data))
    lines = [p.text for p in doc.paragraphs]
    for table in doc.tables:  # many resume templates lay out sections in tables
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                lines.append(" | ".join(dict.fromkeys(cells)))
    return "\n".join(lines)


def extract_text(filename: str, data: bytes) -> str:
    name = filename.lower()
    try:
        if name.endswith(".pdf"):
            text = _pdf(data)
        elif name.endswith(".docx"):
            text = _docx(data)
        elif name.endswith((".txt", ".md")):
            text = data.decode("utf-8", errors="replace")
        else:
            raise ExtractError("Unsupported file type. Use PDF, DOCX, TXT or MD.")
    except ExtractError:
        raise
    except Exception as exc:
        raise ExtractError(f"Could not read {filename}: {exc}") from exc

    text = _clean(text)
    if len(text) < 50:
        raise ExtractError(
            "Almost no text could be extracted. If this is a scanned PDF, paste the text instead."
        )
    return text
