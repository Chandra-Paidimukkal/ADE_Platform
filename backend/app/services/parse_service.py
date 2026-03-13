"""ParseService – document ingestion layer."""
from __future__ import annotations

import logging
from pathlib import Path

from backend.app.core.models import ParsedDocument
from backend.app.core.pdf_reader import PDFReader

logger = logging.getLogger(__name__)


class ParseService:
    def __init__(self) -> None:
        self._reader = PDFReader()

    def parse_document(self, file_path: str | Path) -> ParsedDocument:
        """Parse a single PDF. Returns a ParsedDocument (may have parse_error set)."""
        doc = self._reader.read_pdf(file_path)
        if doc.parse_error:
            logger.warning("Parse error in %s: %s", doc.file_name, doc.parse_error)
        else:
            logger.info("Parsed %s – %d pages, %d chars",
                        doc.file_name, doc.page_count, len(doc.full_text))
        return doc

    def parse_batch(self, folder_path: str | Path) -> list[ParsedDocument]:
        """Parse all PDFs in a folder. Each result includes status."""
        folder = Path(folder_path)
        docs   = []
        for pdf_path in PDFReader.iter_pdf_files(folder):
            docs.append(self.parse_document(pdf_path))
        logger.info("Parsed %d files from %s", len(docs), folder)
        return docs
