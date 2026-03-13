"""
Document Parser Engine
Converts uploaded documents into structured JSON with layout detection.
Supports PDF, PNG, JPEG formats.
"""

import io
import re
import base64
from pathlib import Path
from typing import Any

from utils.logger import get_logger

logger = get_logger(__name__)


class DocumentBlock:
    def __init__(self, block_type: str, content: Any, metadata: dict = None):
        self.type = block_type
        self.content = content
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        base = {"type": self.type, "metadata": self.metadata}
        if self.type == "table":
            base["rows"] = self.content
        elif self.type == "image":
            base["description"] = self.content
        else:
            base["text"] = self.content
        return base


class ParsedDocument:
    def __init__(self, filename: str, file_type: str):
        self.filename = filename
        self.file_type = file_type
        self.pages: list[dict] = []
        self.metadata: dict = {}
        self.raw_text: str = ""
        self.page_count: int = 0

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "file_type": self.file_type,
            "page_count": self.page_count,
            "metadata": self.metadata,
            "pages": self.pages,
            "raw_text": self.raw_text[:10000],  # Truncate for storage
        }


class DocumentParser:
    """
    Main document parsing engine.
    Converts documents to structured JSON with layout detection.
    """

    async def parse(self, file_path: str, file_type: str) -> ParsedDocument:
        """Parse a document and return structured content."""
        path = Path(file_path)
        filename = path.name
        doc = ParsedDocument(filename=filename, file_type=file_type)

        if file_type == "application/pdf":
            await self._parse_pdf(path, doc)
        elif file_type in ("image/png", "image/jpeg", "image/jpg"):
            await self._parse_image(path, doc)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        return doc

    async def _parse_pdf(self, path: Path, doc: ParsedDocument) -> None:
        """Parse PDF using PyMuPDF (fitz)."""
        try:
            import fitz  # PyMuPDF

            pdf = fitz.open(str(path))
            doc.page_count = len(pdf)
            doc.metadata = {
                "title": pdf.metadata.get("title", ""),
                "author": pdf.metadata.get("author", ""),
                "creator": pdf.metadata.get("creator", ""),
                "subject": pdf.metadata.get("subject", ""),
            }

            all_text_parts = []

            for page_num in range(len(pdf)):
                page = pdf[page_num]
                page_data = {"page_number": page_num + 1, "blocks": [], "layout": {}}

                # Extract text blocks with layout info
                blocks = page.get_text("dict")["blocks"]
                page_blocks = []

                for block in blocks:
                    if block.get("type") == 0:  # Text block
                        block_obj = self._process_text_block(block)
                        if block_obj:
                            page_blocks.append(block_obj)
                    elif block.get("type") == 1:  # Image block
                        page_blocks.append({
                            "type": "image",
                            "description": "[Embedded Image]",
                            "bbox": block.get("bbox", []),
                            "metadata": {"width": block.get("width"), "height": block.get("height")},
                        })

                # Detect tables using layout analysis
                tables = self._detect_tables_from_blocks(page_blocks)
                
                # Merge table blocks
                final_blocks = self._merge_with_tables(page_blocks, tables)
                page_data["blocks"] = final_blocks

                # Page layout info
                rect = page.rect
                page_data["layout"] = {
                    "width": rect.width,
                    "height": rect.height,
                    "rotation": page.rotation,
                }

                doc.pages.append(page_data)
                all_text_parts.append(page.get_text("text"))

            pdf.close()
            doc.raw_text = "\n\n--- PAGE BREAK ---\n\n".join(all_text_parts)

        except ImportError:
            logger.warning("PyMuPDF not installed, using fallback PDF parser")
            await self._parse_pdf_fallback(path, doc)

    def _process_text_block(self, block: dict) -> dict | None:
        """Process a text block and classify its type."""
        lines = block.get("lines", [])
        if not lines:
            return None

        texts = []
        max_font_size = 0
        is_bold = False

        for line in lines:
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if text:
                    texts.append(text)
                    size = span.get("size", 10)
                    if size > max_font_size:
                        max_font_size = size
                    flags = span.get("flags", 0)
                    if flags & 16:  # Bold flag
                        is_bold = True

        if not texts:
            return None

        full_text = " ".join(texts)

        # Classify block type
        block_type = "text"
        if max_font_size > 16 or (max_font_size > 12 and is_bold and len(full_text) < 100):
            block_type = "title"
        elif max_font_size > 12 or (is_bold and len(full_text) < 150):
            block_type = "header"
        elif full_text.lower().startswith(("total", "subtotal", "grand total", "amount due")):
            block_type = "summary"

        return {
            "type": block_type,
            "text": full_text,
            "bbox": block.get("bbox", []),
            "metadata": {
                "font_size": max_font_size,
                "is_bold": is_bold,
                "line_count": len(lines),
            },
        }

    def _detect_tables_from_blocks(self, blocks: list[dict]) -> list[dict]:
        """
        Simple heuristic table detection based on alignment patterns.
        In production, enhance with ML-based table detection.
        """
        tables = []
        # Look for blocks that are spatially aligned in a grid pattern
        text_blocks = [b for b in blocks if b.get("type") in ("text", "header")]
        
        # Group blocks by approximate y-coordinate (rows)
        rows: dict[int, list[dict]] = {}
        for block in text_blocks:
            bbox = block.get("bbox", [0, 0, 0, 0])
            y_center = int((bbox[1] + bbox[3]) / 2 / 20) * 20  # Snap to 20px grid
            rows.setdefault(y_center, []).append(block)

        # Rows with 3+ items are likely table rows
        table_rows = {y: blocks for y, blocks in rows.items() if len(blocks) >= 3}
        
        if len(table_rows) >= 2:
            sorted_rows = sorted(table_rows.keys())
            table_data = []
            for y in sorted_rows:
                row_blocks = sorted(table_rows[y], key=lambda b: b.get("bbox", [0])[0])
                table_data.append([b.get("text", "") for b in row_blocks])
            
            if table_data:
                tables.append({
                    "type": "table",
                    "rows": table_data,
                    "metadata": {
                        "row_count": len(table_data),
                        "col_count": max(len(r) for r in table_data),
                        "has_header": True,
                    },
                })

        return tables

    def _merge_with_tables(self, blocks: list[dict], tables: list[dict]) -> list[dict]:
        """Merge detected tables into block list."""
        # Simple merge: add tables to block list
        result = [b for b in blocks if b.get("type") not in ("text",) or len(b.get("text", "")) > 5]
        result.extend(tables)
        return result

    async def _parse_pdf_fallback(self, path: Path, doc: ParsedDocument) -> None:
        """Fallback PDF parser using pdfplumber or basic text extraction."""
        try:
            import pdfplumber
            with pdfplumber.open(str(path)) as pdf:
                doc.page_count = len(pdf.pages)
                all_text = []
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    all_text.append(text)
                    blocks = self._text_to_blocks(text)
                    
                    # Extract tables
                    page_tables = page.extract_tables() or []
                    for table in page_tables:
                        if table:
                            blocks.append({
                                "type": "table",
                                "rows": table,
                                "metadata": {"row_count": len(table)},
                            })

                    doc.pages.append({
                        "page_number": i + 1,
                        "blocks": blocks,
                        "layout": {"width": page.width, "height": page.height},
                    })
                doc.raw_text = "\n\n".join(all_text)
        except ImportError:
            # Absolute fallback
            logger.warning("No PDF library available. Using raw text extraction.")
            doc.page_count = 1
            doc.pages = [{"page_number": 1, "blocks": [{"type": "text", "text": "[PDF content - install PyMuPDF for full parsing]"}], "layout": {}}]

    def _text_to_blocks(self, text: str) -> list[dict]:
        """Convert raw text to blocks using heuristics."""
        blocks = []
        lines = text.split("\n")
        current_para = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current_para:
                    para_text = " ".join(current_para)
                    block_type = "header" if len(para_text) < 80 and para_text.isupper() else "text"
                    blocks.append({"type": block_type, "text": para_text, "metadata": {}})
                    current_para = []
            else:
                current_para.append(stripped)

        if current_para:
            blocks.append({"type": "text", "text": " ".join(current_para), "metadata": {}})

        return blocks

    async def _parse_image(self, path: Path, doc: ParsedDocument) -> None:
        """Parse image document using OCR."""
        doc.page_count = 1
        
        try:
            import pytesseract
            from PIL import Image

            img = Image.open(str(path))
            text = pytesseract.image_to_string(img)
            
            # Get detailed OCR data
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            blocks = self._ocr_data_to_blocks(data, text)
            
            doc.raw_text = text
            doc.pages = [{
                "page_number": 1,
                "blocks": blocks,
                "layout": {"width": img.width, "height": img.height},
            }]
        except (ImportError, Exception) as e:
            logger.warning(f"OCR failed ({e}), using image placeholder")
            # Store image as base64 for AI processing
            with open(str(path), "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()
            doc.pages = [{
                "page_number": 1,
                "blocks": [{"type": "image", "description": "[Image - requires AI vision for extraction]", "base64": img_b64}],
                "layout": {},
            }]

    def _ocr_data_to_blocks(self, data: dict, raw_text: str) -> list[dict]:
        """Convert Tesseract OCR data to structured blocks."""
        blocks = self._text_to_blocks(raw_text)
        return blocks

    def get_document_text(self, parsed: dict) -> str:
        """Extract plain text from parsed document for LLM processing."""
        parts = []
        for page in parsed.get("pages", []):
            for block in page.get("blocks", []):
                if block.get("type") == "table":
                    rows = block.get("rows", [])
                    for row in rows:
                        parts.append(" | ".join(str(cell or "") for cell in row))
                elif block.get("type") != "image":
                    text = block.get("text", "").strip()
                    if text:
                        parts.append(text)
        return "\n".join(parts)
