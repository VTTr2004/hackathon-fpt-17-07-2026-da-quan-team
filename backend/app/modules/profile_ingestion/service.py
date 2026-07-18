import asyncio
from pathlib import Path
from typing import Any

from app.modules.document_chatbot.ingestion import file_to_chunks, text_to_chunks

from .schemas import EvidenceBlock

SUPPORTED_SUFFIXES = {".pdf", ".docx", ".pptx", ".txt", ".md", ".json", ".png", ".jpg", ".jpeg"}
MAX_BLOCKS_PER_DOCUMENT = 200
MAX_BLOCKS_PER_EXTRACTION = 1000


def _document_blocks(document: dict[str, Any]) -> list[EvidenceBlock]:
    document_id = str(document["id"])
    filename = str(document["filename"])
    path_value = document.get("storage_path")
    chunks: list[dict[str, Any]]
    if path_value and Path(path_value).exists() and Path(filename).suffix.lower() not in {".png", ".jpg", ".jpeg"}:
        try:
            chunks = file_to_chunks(Path(path_value), document_id=document_id, filename=filename)
        except Exception:
            chunks = []
    else:
        chunks = []
    if not chunks:
        chunks = text_to_chunks(
            str(document.get("text") or ""), document_id=document_id, filename=filename
        )
    normalized_chunks = [
        {**chunk, "block_id": chunk.get("block_id") or chunk.get("chunk_id")}
        for chunk in chunks
        if str(chunk.get("text") or "").strip()
    ]
    return [EvidenceBlock.model_validate(chunk) for chunk in normalized_chunks]


async def build_evidence_blocks(documents: list[dict[str, Any]]) -> tuple[list[EvidenceBlock], list[str]]:
    blocks: list[EvidenceBlock] = []
    warnings: list[str] = []
    for document in documents:
        suffix = Path(str(document["filename"])).suffix.lower()
        if suffix not in SUPPORTED_SUFFIXES:
            warnings.append(f"{document['filename']}: chưa thuộc phạm vi profile extraction MVP.")
            continue
        try:
            document_blocks = await asyncio.to_thread(_document_blocks, document)
            if not document_blocks:
                warnings.append(
                    f"{document['filename']}: không có text có thể trích xuất; PDF scan hoặc tài liệu toàn ảnh cần OCR."
                )
                continue
            if len(document_blocks) > MAX_BLOCKS_PER_DOCUMENT:
                warnings.append(
                    f"{document['filename']}: chỉ dùng {MAX_BLOCKS_PER_DOCUMENT} evidence block đầu tiên."
                )
            blocks.extend(document_blocks[:MAX_BLOCKS_PER_DOCUMENT])
            if len(blocks) >= MAX_BLOCKS_PER_EXTRACTION:
                warnings.append(f"Extraction được giới hạn ở {MAX_BLOCKS_PER_EXTRACTION} evidence block.")
                return blocks[:MAX_BLOCKS_PER_EXTRACTION], warnings
        except Exception as exc:
            warnings.append(f"{document['filename']}: không thể tạo evidence block ({exc}).")
    return blocks, warnings
