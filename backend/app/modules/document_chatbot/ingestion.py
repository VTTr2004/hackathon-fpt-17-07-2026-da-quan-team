"""Turn raw sources into retrieval chunks with citation metadata.

Two entry points:
- ``csv_rows_to_chunks``: one VC-dataset row -> one natural-language "record card" chunk.
- ``text_to_chunks``: long document text -> overlapping chunks that keep page/slide/sheet markers
  emitted by ``services.document_parser`` so citations can point back to the native location.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

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
