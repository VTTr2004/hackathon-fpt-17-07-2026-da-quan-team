"""Turn raw sources into retrieval chunks with citation metadata.

Entry points:
- ``csv_rows_to_chunks``: one VC-dataset row -> one natural-language "record card" chunk.
- ``json_to_chunks``: a JSON document (business profile, location) -> one labeled descriptive card.
- ``xlsx_to_chunks``: a workbook -> structure-aware cards. Summary/dimension rows become one labeled
  card each; oversized transaction sheets get an overview card instead of thousands of row cards
  (their ``Tóm tắt`` sheet already carries the aggregates). See docs/methodology.md.
- ``text_to_chunks``: long document text -> overlapping chunks that keep page/slide/sheet markers.
- ``file_to_chunks``: dispatch a file path to the right handler by extension.
"""
from __future__ import annotations

import csv
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

_MARKER = re.compile(r"\[(PAGE|SLIDE|SHEET)\s+([^\]]+)\]", re.IGNORECASE)


def _clean(value: str | None) -> str:
    return (value or "").strip().strip("|").replace("|", ", ").strip()


def _money(value: str | None) -> str:
    text = (value or "").strip()
    if not text or text in {"-", "—"}:
        return "0"
    return text.replace(",", "")


def csv_rows_to_chunks(path: Path, *, document_id: str, filename: str, limit: int = 100) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        reader.fieldnames = [(name or "").strip() for name in (reader.fieldnames or [])]
        for row_index, raw in enumerate(reader):
            if row_index >= limit:
                break
            row = {(k or "").strip(): v for k, v in raw.items()}
            name = _clean(row.get("name"))
            if not name:
                continue
            market = _clean(row.get("market")) or "unknown"
            city = _clean(row.get("city")) or "unknown city"
            country = _clean(row.get("country_code")) or "unknown country"
            status = _clean(row.get("status")) or "unknown"
            year = _clean(row.get("founded_year")) or "unknown year"
            categories = _clean(row.get("category_list"))
            total = _money(row.get("funding_total_usd"))
            rounds = _clean(row.get("funding_rounds")) or "0"
            text = (
                f"{name} is a startup in the {market} market based in {city}, {country}. "
                f"Operating status: {status}. Founded in {year}. Categories: {categories}. "
                f"Total funding raised: ${total} across {rounds} funding round(s)."
            )
            chunks.append(
                {
                    "chunk_id": f"{document_id}:row:{row_index}",
                    "document_id": document_id,
                    "filename": filename,
                    "text": text,
                    "metadata": {"row": row_index, "company": name, "market": market},
                }
            )
    return chunks


def text_to_chunks(
    text: str,
    *,
    document_id: str,
    filename: str,
    chunk_size: int = 1000,
    overlap: int = 150,
) -> list[dict[str, Any]]:
    if not text.strip():
        return []
    step = max(chunk_size - overlap, 1)
    chunks: list[dict[str, Any]] = []
    for offset in range(0, len(text), step):
        window = text[offset : offset + chunk_size]
        if not window.strip():
            continue
        preceding = text[:offset]
        marker = None
        for match in _MARKER.finditer(preceding + window):
            marker = (match.group(1).upper(), match.group(2).strip())
        location: dict[str, Any] = {}
        if marker:
            key = {"PAGE": "page", "SLIDE": "slide", "SHEET": "sheet"}[marker[0]]
            value = marker[1]
            location[key] = int(value) if value.isdigit() else value
        chunks.append(
            {
                "chunk_id": f"{document_id}:chunk:{len(chunks)}",
                "document_id": document_id,
                "filename": filename,
                "text": window.strip(),
                "metadata": location,
            }
        )
    return chunks


# ---------------------------------------------------------------- JSON --------
def _flatten_json(obj: Any, prefix: str = "") -> list[str]:
    lines: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            lines.extend(_flatten_json(value, f"{prefix}{key}."))
    elif isinstance(obj, list):
        if all(not isinstance(item, (dict, list)) for item in obj):
            lines.append(f"{prefix[:-1]}: " + "; ".join(str(item) for item in obj))
        else:
            for index, item in enumerate(obj):
                lines.extend(_flatten_json(item, f"{prefix}{index}."))
    else:
        lines.append(f"{prefix[:-1]}: {obj}")
    return lines


def json_to_chunks(path: Path, *, document_id: str, filename: str) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    lines = _flatten_json(data)
    if not lines:
        return []
    text = f"[{filename}]\n" + "\n".join(lines)
    return [
        {
            "chunk_id": f"{document_id}:json",
            "document_id": document_id,
            "filename": filename,
            "text": text,
            "metadata": {"kind": "json"},
        }
    ]


# ---------------------------------------------------------------- XLSX --------
def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat() if value.time().isoformat() == "00:00:00" else value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    return str(value).strip()


def xlsx_to_chunks(
    path: Path, *, document_id: str, filename: str, max_data_rows: int = 40
) -> list[dict[str, Any]]:
    """Structure-aware workbook ingestion.

    Detects the header of each table within a sheet (a header is the first multi-column row after a
    blank/title row), then emits one labeled card per data row. Sheets with more than ``max_data_rows``
    data rows get only an overview card (their ``Tóm tắt`` sheet holds the aggregates), which keeps
    embedding volume and retrieval noise bounded.
    """
    workbook = load_workbook(path, read_only=True, data_only=True)
    chunks: list[dict[str, Any]] = []
    for sheet in workbook.worksheets:
        header: list[str] | None = None
        expect_header = True
        data_count = 0
        columns: list[str] = []
        row_cards: list[dict[str, Any]] = []
        for raw in sheet.values:
            cells = [_cell(value) for value in raw]
            non_empty = [cell for cell in cells if cell]
            if not non_empty:
                expect_header = True
                continue
            if len(non_empty) == 1:  # title / disclaimer / section label
                expect_header = True
                continue
            if expect_header:
                header = cells
                columns = [cell for cell in cells if cell]
                expect_header = False
                continue
            data_count += 1
            if data_count > max_data_rows:
                continue
            pairs = [
                f"{header[index]}: {cells[index]}"
                for index in range(len(cells))
                if index < len(header) and header[index] and cells[index]
            ]
            if not pairs:
                continue
            row_cards.append(
                {
                    "chunk_id": f"{document_id}:{sheet.title}:{data_count}",
                    "document_id": document_id,
                    "filename": filename,
                    "text": f"[{filename} › {sheet.title}] " + " | ".join(pairs),
                    "metadata": {"sheet": sheet.title, "row": data_count},
                }
            )
        overview = f"[{filename} › {sheet.title}] Bảng dữ liệu {data_count} dòng."
        if columns:
            overview += " Cột: " + ", ".join(columns) + "."
        if data_count > max_data_rows:
            overview += (
                f" (Chỉ lập chỉ mục {max_data_rows} dòng đầu; dùng sheet 'Tóm tắt' cho số liệu tổng hợp.)"
            )
        chunks.append(
            {
                "chunk_id": f"{document_id}:{sheet.title}:overview",
                "document_id": document_id,
                "filename": filename,
                "text": overview,
                "metadata": {"sheet": sheet.title, "kind": "overview"},
            }
        )
        chunks.extend(row_cards)
    return chunks


# ------------------------------------------------------------ dispatch --------
def file_to_chunks(path: Path, *, document_id: str, filename: str) -> list[dict[str, Any]]:
    """Route a file to the right ingester by extension (PDF/text fall back to document_parser)."""
    suffix = path.suffix.lower()
    if suffix == ".json":
        return json_to_chunks(path, document_id=document_id, filename=filename)
    if suffix == ".xlsx":
        return xlsx_to_chunks(path, document_id=document_id, filename=filename)
    if suffix == ".csv":
        return csv_rows_to_chunks(path, document_id=document_id, filename=filename)
    if suffix in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8", errors="replace")
    else:
        # PDF/DOCX/PPTX: import the parser lazily so JSON/XLSX/text ingestion needs no doc-parser libs.
        from app.services.document_parser import extract_text

        text = extract_text(path)
    return text_to_chunks(text, document_id=document_id, filename=filename)
