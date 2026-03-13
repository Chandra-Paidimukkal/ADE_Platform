"""
Agentic Pipeline - AI Agents for Document Processing
Each agent handles a specific stage of the extraction pipeline.
All LLM calls route through the LLM injection layer.
"""

import json
from typing import Any, Optional
from core.llm_router import LLMRouter, LLMRequest, LLMMessage, LLMRole
from core.parser import DocumentParser
from utils.logger import get_logger

logger = get_logger(__name__)


class BaseAgent:
    """Base class for all extraction agents."""

    def __init__(self, llm_router: LLMRouter, config: dict = None):
        self.llm = llm_router
        self.config = config or {}
        self.provider = self.config.get("provider")

    async def _llm_complete(self, system: str, user: str, as_json: bool = False) -> Any:
        """Route LLM call through the injection layer."""
        request = LLMRequest(
            messages=[LLMMessage(role=LLMRole.USER, content=user)],
            system_prompt=system,
            response_format="json" if as_json else None,
        )
        response = await self.llm.complete(request, provider_name=self.provider)
        if as_json:
            return response.as_json()
        return response.content


class SchemaSuggestionAgent(BaseAgent):
    """
    Analyzes a document and proposes an extraction schema.
    Users can accept, modify, or reject the suggestions.
    """

    SYSTEM_PROMPT = """You are an expert document analysis AI specializing in structured data extraction.
Your task is to analyze document content and propose an optimal extraction schema.

Rules:
- Identify all structured data fields visible in the document
- Group related fields into logical objects
- Detect tables and represent them as arrays
- Use descriptive field names in camelCase
- Assign appropriate data types: string, number, boolean, date, object, array, table
- Provide confidence scores (0.0 to 1.0) for each suggested field
- Output ONLY valid JSON, no explanations

Output format:
{
  "schema": { /* schema definition */ },
  "field_hints": { /* field_name: "description of where to find this" */ },
  "confidence": 0.0-1.0,
  "document_type": "invoice|receipt|form|report|catalog|other",
  "suggestions": ["list of field names found"]
}"""

    async def suggest_schema(self, document_text: str, parsed_structure: dict) -> dict:
        """Analyze document and suggest extraction schema."""
        logger.info("Schema Suggestion Agent: Analyzing document...")

        # Build context from parsed structure
        structure_summary = self._summarize_structure(parsed_structure)

        user_prompt = f"""Analyze this document and propose an extraction schema.

DOCUMENT CONTENT:
{document_text[:4000]}

DOCUMENT STRUCTURE SUMMARY:
{structure_summary}

Propose a complete extraction schema with all visible fields."""

        try:
            result = await self._llm_complete(self.SYSTEM_PROMPT, user_prompt, as_json=True)
            logger.info(f"Schema suggestion completed. Document type: {result.get('document_type')}")
            return result
        except Exception as e:
            logger.error(f"Schema suggestion failed: {e}")
            return self._fallback_schema()

    def _summarize_structure(self, parsed: dict) -> str:
        parts = []
        for page in parsed.get("pages", []):
            for block in page.get("blocks", []):
                btype = block.get("type")
                if btype == "title":
                    parts.append(f"TITLE: {block.get('text', '')}")
                elif btype == "header":
                    parts.append(f"HEADER: {block.get('text', '')}")
                elif btype == "table":
                    rows = block.get("rows", [])
                    if rows:
                        parts.append(f"TABLE ({len(rows)} rows, {len(rows[0]) if rows else 0} cols): {rows[0]}")
        return "\n".join(parts[:30])

    def _fallback_schema(self) -> dict:
        return {
            "schema": {
                "documentTitle": "string",
                "date": "date",
                "reference": "string",
                "content": "string",
                "items": [{"description": "string", "value": "string"}],
            },
            "field_hints": {},
            "confidence": 0.3,
            "document_type": "other",
            "suggestions": ["documentTitle", "date", "reference"],
        }


class ExtractionAgent(BaseAgent):
    """
    Extracts structured data from documents according to a schema.
    The schema guides exactly what data to extract.
    """

    SYSTEM_PROMPT = """You are an expert data extraction AI. Extract structured data from documents according to provided schemas.

Rules:
- Extract ONLY fields defined in the schema
- Match output structure EXACTLY to the schema
- Use null for missing/unclear fields
- For arrays/tables, extract ALL rows found
- For dates: use ISO format (YYYY-MM-DD)
- For numbers: return numeric values only (no currency symbols)
- Provide a confidence score (0.0-1.0) for each extracted field
- Output ONLY valid JSON

Output format:
{
  "extracted_data": { /* extracted values matching schema exactly */ },
  "confidence_scores": { /* field_name: 0.0-1.0 */ },
  "extraction_notes": "any important notes about the extraction"
}"""

    async def extract(
        self,
        document_text: str,
        parsed_structure: dict,
        schema: dict,
        segment_index: int = 0,
    ) -> dict:
        """Extract structured data from document using the schema."""
        logger.info(f"Extraction Agent: Processing segment {segment_index}...")

        schema_str = json.dumps(schema, indent=2)
        user_prompt = f"""Extract all data from this document according to the schema.

EXTRACTION SCHEMA:
{schema_str}

DOCUMENT CONTENT:
{document_text[:5000]}

Extract every field in the schema. Return null for fields not found."""

        try:
            result = await self._llm_complete(self.SYSTEM_PROMPT, user_prompt, as_json=True)
            logger.info("Extraction completed successfully")
            return result
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return {"extracted_data": {}, "confidence_scores": {}, "extraction_notes": f"Error: {e}"}


class ValidationAgent(BaseAgent):
    """
    Validates extracted data against schema rules and business logic.
    """

    SYSTEM_PROMPT = """You are a data validation expert. Validate extracted data against schemas.

Check:
1. Required fields are present and non-null
2. Data types match schema definitions
3. Date formats are valid
4. Numbers are actually numeric
5. Business logic consistency (e.g., total = sum of line items)

Output ONLY valid JSON:
{
  "passed": true/false,
  "errors": [{"field": "fieldName", "error": "description", "severity": "error|warning"}],
  "corrected_data": { /* auto-corrected values if possible */ },
  "overall_confidence": 0.0-1.0
}"""

    async def validate(self, extracted_data: dict, schema: dict) -> dict:
        """Validate extracted data."""
        logger.info("Validation Agent: Validating extracted data...")

        # First do programmatic validation
        prog_errors = self._programmatic_validate(extracted_data, schema)

        user_prompt = f"""Validate this extracted data against the schema.

SCHEMA:
{json.dumps(schema, indent=2)}

EXTRACTED DATA:
{json.dumps(extracted_data, indent=2)}

ALREADY DETECTED ISSUES:
{json.dumps(prog_errors, indent=2)}

Provide comprehensive validation results."""

        try:
            result = await self._llm_complete(self.SYSTEM_PROMPT, user_prompt, as_json=True)
            # Merge programmatic errors
            if prog_errors:
                existing = result.get("errors", [])
                result["errors"] = prog_errors + existing
                result["passed"] = len(result["errors"]) == 0
            return result
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {
                "passed": len(prog_errors) == 0,
                "errors": prog_errors,
                "corrected_data": extracted_data,
                "overall_confidence": 0.5,
            }

    def _programmatic_validate(self, data: dict, schema: dict) -> list[dict]:
        """Fast programmatic validation before LLM call."""
        errors = []
        self._validate_object(data, schema, errors, path="")
        return errors

    def _validate_object(self, data: dict, schema: dict, errors: list, path: str):
        for field, field_type in schema.items():
            full_path = f"{path}.{field}" if path else field
            value = data.get(field)

            if value is None:
                continue  # LLM validation will handle required fields

            if isinstance(field_type, str):
                if field_type == "number" and not isinstance(value, (int, float)):
                    try:
                        float(str(value).replace(",", "").replace("$", ""))
                    except ValueError:
                        errors.append({"field": full_path, "error": f"Expected number, got '{value}'", "severity": "error"})
                elif field_type == "boolean" and not isinstance(value, bool):
                    errors.append({"field": full_path, "error": f"Expected boolean, got '{value}'", "severity": "warning"})
            elif isinstance(field_type, dict):
                if isinstance(value, dict):
                    self._validate_object(value, field_type, errors, full_path)
            elif isinstance(field_type, list) and field_type:
                if isinstance(value, list):
                    item_schema = field_type[0]
                    for i, item in enumerate(value):
                        if isinstance(item, dict) and isinstance(item_schema, dict):
                            self._validate_object(item, item_schema, errors, f"{full_path}[{i}]")


class LayoutAgent(BaseAgent):
    """
    Analyzes document layout to understand structure.
    Identifies sections, tables, headers, and reading order.
    """

    SYSTEM_PROMPT = """You are a document layout analysis expert.
Analyze the document structure and identify layout regions.

Output ONLY valid JSON:
{
  "layout_regions": [
    {"type": "header|footer|section|table|sidebar", "label": "name", "content_preview": "..."}
  ],
  "reading_order": ["region labels in reading order"],
  "document_structure": "description of overall document structure"
}"""

    async def analyze_layout(self, parsed_structure: dict, document_text: str) -> dict:
        """Analyze document layout."""
        logger.info("Layout Agent: Analyzing document layout...")

        structure_text = json.dumps(parsed_structure, indent=2)[:3000]
        user_prompt = f"""Analyze the layout of this document.

PARSED STRUCTURE:
{structure_text}

TEXT PREVIEW:
{document_text[:2000]}"""

        try:
            return await self._llm_complete(self.SYSTEM_PROMPT, user_prompt, as_json=True)
        except Exception as e:
            logger.error(f"Layout analysis failed: {e}")
            return {"layout_regions": [], "reading_order": [], "document_structure": "Unknown"}


class SplitAgent(BaseAgent):
    """
    Detects logical boundaries in documents for splitting multiple records.
    """

    SYSTEM_PROMPT = """You are a document segmentation expert.
Analyze documents to find where one logical record ends and another begins.

Examples: Multiple invoices in one PDF, multiple patient records, multiple forms.

Output ONLY valid JSON:
{
  "should_split": true/false,
  "split_method": "page|section|semantic",
  "segments": [
    {"start_page": 1, "end_page": 2, "label": "Record 1", "confidence": 0.9}
  ],
  "reasoning": "explanation"
}"""

    async def detect_splits(self, parsed_structure: dict, document_text: str) -> dict:
        """Detect logical document segments."""
        logger.info("Split Agent: Detecting document segments...")

        page_count = len(parsed_structure.get("pages", []))
        user_prompt = f"""Analyze if this document contains multiple logical records and where to split.

DOCUMENT: {page_count} pages

TEXT PREVIEW:
{document_text[:3000]}

Determine if splitting is needed."""

        try:
            result = await self._llm_complete(self.SYSTEM_PROMPT, user_prompt, as_json=True)
            return result
        except Exception as e:
            logger.error(f"Split detection failed: {e}")
            return {
                "should_split": False,
                "split_method": "page",
                "segments": [{"start_page": 1, "end_page": page_count, "label": "Full Document", "confidence": 1.0}],
                "reasoning": "Could not analyze splits",
            }


class AgentOrchestrator:
    """
    Coordinates all agents in the extraction pipeline.
    Manages the full lifecycle from parsing to validation.
    """

    def __init__(self, llm_router: LLMRouter, config: dict = None):
        self.llm = llm_router
        self.config = config or {}
        agent_config = self.config.get("agent_config", {})

        self.parser = DocumentParser()
        self.layout_agent = LayoutAgent(llm_router, agent_config)
        self.split_agent = SplitAgent(llm_router, agent_config)
        self.schema_agent = SchemaSuggestionAgent(llm_router, agent_config)
        self.extraction_agent = ExtractionAgent(llm_router, agent_config)
        self.validation_agent = ValidationAgent(llm_router, agent_config)

    async def full_pipeline(
        self,
        file_path: str,
        file_type: str,
        schema: dict,
        split_config: dict = None,
    ) -> dict:
        """
        Execute the full extraction pipeline.
        Returns structured results for all segments.
        """
        logger.info(f"Starting full pipeline for: {file_path}")
        results = {"status": "running", "segments": []}

        # 1. Parse document
        parsed = await self.parser.parse(file_path, file_type)
        parsed_dict = parsed.to_dict()
        doc_text = self.parser.get_document_text(parsed_dict)

        # 2. Layout analysis
        layout = await self.layout_agent.analyze_layout(parsed_dict, doc_text)

        # 3. Split detection
        splits = await self.split_agent.detect_splits(parsed_dict, doc_text)
        segments = splits.get("segments", [{"start_page": 1, "end_page": parsed.page_count, "label": "Full Document", "confidence": 1.0}])

        # 4. Extract each segment
        for i, segment in enumerate(segments):
            seg_text = self._extract_segment_text(parsed_dict, segment)
            extraction = await self.extraction_agent.extract(seg_text, parsed_dict, schema, i)
            validation = await self.validation_agent.validate(extraction.get("extracted_data", {}), schema)

            results["segments"].append({
                "segment_index": i,
                "segment_label": segment.get("label", f"Segment {i+1}"),
                "pages": f"{segment.get('start_page')}-{segment.get('end_page')}",
                "extracted_data": extraction.get("extracted_data", {}),
                "confidence_scores": extraction.get("confidence_scores", {}),
                "validation": validation,
            })

        results["status"] = "completed"
        results["parsed_document"] = parsed_dict
        results["layout"] = layout
        results["splits"] = splits
        return results

    def _extract_segment_text(self, parsed: dict, segment: dict) -> str:
        """Extract text for a specific page range segment."""
        start = segment.get("start_page", 1) - 1
        end = segment.get("end_page", len(parsed.get("pages", [])))
        pages = parsed.get("pages", [])[start:end]
        
        parts = []
        for page in pages:
            for block in page.get("blocks", []):
                if block.get("type") == "table":
                    for row in block.get("rows", []):
                        parts.append(" | ".join(str(c or "") for c in row))
                elif block.get("text"):
                    parts.append(block["text"])
        return "\n".join(parts)
