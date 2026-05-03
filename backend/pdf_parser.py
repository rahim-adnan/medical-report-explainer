# backend/pdf_parser.py
"""
PDF Parser — extracts raw text from uploaded medical report PDFs.
Handles multi-page documents, scanned-image fallback detection,
and cleans raw text for downstream LLM processing.
"""

import re
import fitz  # PyMuPDF


class PDFParser:
    """
    Parses a medical report PDF and returns cleaned text.

    Usage:
        parser = PDFParser(pdf_bytes)
        result = parser.parse()
        # result = { "text": "...", "pages": 3, "is_scanned": False, "word_count": 412 }
    """

    MAX_CHARS = 12_000  # Keep within LLM context limits

    def __init__(self, pdf_bytes: bytes):
        self.pdf_bytes = pdf_bytes

    # ── Public API ─────────────────────────────────────────────────────────────
    def parse(self) -> dict:
        """
        Main entry point. Returns a dict with:
            text       — cleaned extracted text (truncated if very long)
            pages      — number of pages in the PDF
            is_scanned — True if little/no text found (likely a scanned image)
            word_count — approximate word count of extracted text
        """
        doc = fitz.open(stream=self.pdf_bytes, filetype="pdf")
        pages = doc.page_count
        raw_text = self._extract_text(doc)
        doc.close()

        is_scanned = len(raw_text.strip()) < 100
        cleaned = self._clean(raw_text)
        truncated = cleaned[: self.MAX_CHARS]

        return {
            "text": truncated,
            "pages": pages,
            "is_scanned": is_scanned,
            "word_count": len(truncated.split()),
        }

    # ── Internal helpers ───────────────────────────────────────────────────────
    def _extract_text(self, doc: fitz.Document) -> str:
        """Extracts text from all pages, preserving logical reading order."""
        parts = []
        for page in doc:
            # Use "text" mode which preserves reading order
            text = page.get_text("text")
            if text.strip():
                parts.append(text)
        return "\n".join(parts)

    def _clean(self, text: str) -> str:
        """
        Removes junk characters, collapses whitespace,
        and strips repeated blank lines.
        """
        # Remove non-printable characters except newlines
        text = re.sub(r"[^\x20-\x7E\n]", " ", text)
        # Collapse multiple spaces to one
        text = re.sub(r"[ \t]+", " ", text)
        # Collapse 3+ newlines to 2
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Strip leading/trailing whitespace per line
        lines = [line.strip() for line in text.splitlines()]
        return "\n".join(lines).strip()
