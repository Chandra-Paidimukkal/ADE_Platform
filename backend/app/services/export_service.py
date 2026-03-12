"""
ExportService – writes extraction results to JSON and/or CSV.
"""
from __future__ import annotations

import csv
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from backend.app.core.config import settings
from backend.app.core.exceptions import ExportError

logger = logging.getLogger(__name__)


class ExportService:
    def __init__(self, output_dir: Path | None = None) -> None:
        self._dir = Path(output_dir or settings.OUTPUT_DIR)
        self._dir.mkdir(parents=True, exist_ok=True)

    # ── Public ───────────────────────────────────────────────────────

    def export_json(
        self,
        results: list[dict],
        output_path: str | Path | None = None,
    ) -> Path:
        path = Path(output_path or self._auto_path("json"))
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(results, fh, indent=2, ensure_ascii=False)
            logger.info("Exported %d records → %s", len(results), path)
            return path
        except Exception as exc:
            raise ExportError(f"JSON export failed: {exc}") from exc

    def export_csv(
        self,
        results: list[dict],
        output_path: str | Path | None = None,
    ) -> Path:
        path = Path(output_path or self._auto_path("csv"))
        try:
            rows = [self._flatten(r) for r in results]
            if not rows:
                raise ExportError("No results to export")

            # Union of all column keys
            all_keys: list[str] = []
            seen: set[str] = set()
            for row in rows:
                for k in row:
                    if k not in seen:
                        all_keys.append(k)
                        seen.add(k)

            with open(path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=all_keys, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(rows)

            logger.info("Exported %d records → %s", len(rows), path)
            return path
        except ExportError:
            raise
        except Exception as exc:
            raise ExportError(f"CSV export failed: {exc}") from exc

    # ── Private ──────────────────────────────────────────────────────

    def _auto_path(self, ext: str) -> Path:
        ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        return self._dir / f"extraction_{ts}.{ext}"

    @staticmethod
    def _flatten(result: dict) -> dict:
        """Flatten nested 'data' dict into the top-level row."""
        row: dict = {
            "file":   result.get("file", ""),
            "status": result.get("status", ""),
        }
        data = result.get("data", {})
        for k, v in data.items():
            row[k] = ", ".join(str(i) for i in v) if isinstance(v, list) else str(v)
        errors = result.get("errors", [])
        row["errors"] = "; ".join(errors) if errors else ""
        return row
