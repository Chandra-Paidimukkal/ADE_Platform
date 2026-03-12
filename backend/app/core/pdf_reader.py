"""
PDFReader – wraps pdfplumber to produce ParsedDocument objects.
Handles corrupted/password-protected PDFs gracefully.
Adds OCR fallback for scanned/image-based pages.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterator

from backend.app.core.exceptions import PDFParseError
from backend.app.core.models import ParsedBlock, ParsedDocument, ParsedPage, ParsedTable

logger = logging.getLogger(__name__)


class PDFReader:
    """Read a single PDF and return a structured ParsedDocument."""

    MAX_PAGE_CHARS = 50_000
    OCR_TEXT_THRESHOLD = 20  # if native text is too short, try OCR

    def read_pdf(self, file_path: str | Path) -> ParsedDocument:
        path = Path(file_path)
        doc = ParsedDocument(
            file_name=path.name,
            file_path=str(path),
        )

        try:
            import pdfplumber  # optional dependency
        except ImportError:
            doc.parse_error = "pdfplumber not installed"
            logger.error(doc.parse_error)
            return doc

        try:
            with pdfplumber.open(str(path)) as pdf:
                doc.page_count = len(pdf.pages)
                pages: list[ParsedPage] = []
                full_text_parts: list[str] = []

                for pdf_page in pdf.pages:
                    parsed_page = self._parse_page(pdf_page)
                    pages.append(parsed_page)
                    full_text_parts.append(parsed_page.text)

                doc.pages = pages
                doc.full_text = "\n\n".join(part for part in full_text_parts if part).strip()

        except Exception as exc:  # noqa: BLE001
            doc.parse_error = f"PDF read error: {exc}"
            logger.warning("Failed to read %s: %s", path.name, exc)

        return doc

    # ── Private helpers ──────────────────────────────────────────────

    def _parse_page(self, pdf_page) -> ParsedPage:  # type: ignore[type-arg]
        page_num = pdf_page.page_number
        raw_text = (pdf_page.extract_text() or "")[: self.MAX_PAGE_CHARS]

        # OCR fallback for scanned / image-heavy pages
        if len(raw_text.strip()) < self.OCR_TEXT_THRESHOLD:
            ocr_text = self._extract_ocr_text(pdf_page)
            if ocr_text and len(ocr_text.strip()) > len(raw_text.strip()):
                raw_text = ocr_text[: self.MAX_PAGE_CHARS]

        # Blocks
        blocks: list[ParsedBlock] = []
        try:
            for block in pdf_page.extract_words() or []:
                blocks.append(
                    ParsedBlock(
                        text=block.get("text", ""),
                        bbox=(
                            block.get("x0", 0),
                            block.get("top", 0),
                            block.get("x1", 0),
                            block.get("bottom", 0),
                        ),
                        block_type="text",
                    )
                )
        except Exception as exc:  # noqa: BLE001
            logger.debug("Block extraction failed on page %s: %s", page_num, exc)

        # Tables
        tables: list[ParsedTable] = []
        try:
            for raw_table in pdf_page.extract_tables() or []:
                if not raw_table:
                    continue

                clean: list[list[str]] = [
                    [str(cell).strip() if cell else "" for cell in row]
                    for row in raw_table
                ]

                headers = clean[0] if clean else []
                rows = clean[1:] if len(clean) > 1 else []

                tables.append(ParsedTable(rows=rows, headers=headers))
        except Exception as exc:  # noqa: BLE001
            logger.debug("Table extraction failed on page %s: %s", page_num, exc)

        return ParsedPage(
            page_number=page_num,
            text=raw_text,
            blocks=blocks,
            tables=tables,
        )

    def _extract_ocr_text(self, pdf_page) -> str:
        """
        OCR fallback for image/scanned pages.

        Requires:
        - pytesseract
        - PIL / Pillow
        - system Tesseract installed
        """
        try:
            import pytesseract
        except ImportError:
            logger.debug("pytesseract not installed; OCR skipped")
            return ""

        try:
            page_image = pdf_page.to_image(resolution=200).original
            text = pytesseract.image_to_string(page_image) or ""
            return text.strip()
        except Exception as exc:  # noqa: BLE001
            logger.debug("OCR failed on page %s: %s", getattr(pdf_page, "page_number", "?"), exc)
            return ""

    # ── Batch helpers ────────────────────────────────────────────────

    @staticmethod
    def iter_pdf_files(folder: str | Path, recursive: bool = False) -> Iterator[Path]:
        """Yield all PDF files in a folder."""
        folder = Path(folder)
        if not folder.exists():
            raise PDFParseError(f"Folder not found: {folder}")

        if recursive:
            for p in sorted(folder.rglob("*.pdf")):
                if p.is_file():
                    yield p
        else:
            for p in sorted(folder.iterdir()):
                if p.is_file() and p.suffix.lower() == ".pdf":
                    yield p

    def read_folder(self, folder: str | Path, recursive: bool = False) -> list[ParsedDocument]:
        results = []
        for pdf_path in self.iter_pdf_files(folder, recursive=recursive):
            logger.info("Parsing %s", pdf_path.name)
            results.append(self.read_pdf(pdf_path))
        return results