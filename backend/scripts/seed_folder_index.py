"""Build and persist the hybrid RAG index for a folder of mixed documents.

Ingests every supported file in a directory (JSON, XLSX, CSV, TXT/MD, and PDF/DOCX/PPTX unless
excluded) into one startup-scoped index. Used to seed sample datasets like sample-data/goc-ho-coffee.

Usage:
    python -m scripts.seed_folder_index --startup-id <id> --dir ../sample-data/goc-ho-coffee
    python -m scripts.seed_folder_index --startup-id <id> --dir ./docs --include-pdf
"""
import argparse
import asyncio
from pathlib import Path

from app.modules.document_chatbot.index_store import build_index, index_dir
from app.modules.document_chatbot.ingestion import file_to_chunks

TEXT_LIKE = {".json", ".xlsx", ".csv", ".txt", ".md"}
DOC_LIKE = {".pdf", ".docx", ".pptx"}


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed a hybrid RAG index from a folder")
    parser.add_argument("--startup-id", required=True, help="Startup id used as the index key")
    parser.add_argument("--dir", required=True, help="Directory of documents to ingest")
    parser.add_argument("--include-pdf", action="store_true", help="Also ingest PDF/DOCX/PPTX")
    args = parser.parse_args()

    allowed = TEXT_LIKE | (DOC_LIKE if args.include_pdf else set())
    root = Path(args.dir)
    chunks = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in allowed):
        produced = file_to_chunks(path, document_id=path.stem, filename=path.name)
        print(f"  {path.relative_to(root)}: {len(produced)} chunks")
        chunks.extend(produced)

    if not chunks:
        print(f"No supported files found in {root}")
        return
    index = await build_index(args.startup_id, chunks)
    dense = "with embeddings" if index._unit is not None else "BM25-only (provider not configured)"  # noqa: SLF001
    print(f"\n{len(chunks)} chunks -> {index_dir()} ({dense})")


if __name__ == "__main__":
    asyncio.run(main())
