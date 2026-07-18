"""Build and persist the hybrid RAG index for the VC-dataset demo.

Turns the first N rows of investments_VC.csv into per-company record cards, embeds them via
NVIDIA, and writes the startup-scoped index under UPLOAD_DIR/rag_index/<startup_id>.{json,npy}.
The chat endpoint for that startup then loads this prebuilt index automatically.

Usage:
    python -m scripts.seed_vc_index --startup-id <uuid> --csv ../investments_VC.csv --limit 100
"""
import argparse
import asyncio
from pathlib import Path

from app.modules.document_chatbot.index_store import build_index, index_dir
from app.modules.document_chatbot.ingestion import csv_rows_to_chunks


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the VC-dataset RAG index")
    parser.add_argument("--startup-id", required=True, help="Startup id used as the index key")
    parser.add_argument("--csv", default="../investments_VC.csv", help="Path to investments_VC.csv")
    parser.add_argument("--limit", type=int, default=100, help="Number of rows to ingest")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    chunks = csv_rows_to_chunks(
        csv_path, document_id="vc-dataset", filename=csv_path.name, limit=args.limit
    )
    print(f"Ingested {len(chunks)} record cards from {csv_path}")
    index = await build_index(args.startup_id, chunks)
    dense = "with embeddings" if index._unit is not None else "BM25-only (NVIDIA not configured)"  # noqa: SLF001
    print(f"Index persisted to {index_dir() / (args.startup_id + '.json')} ({dense})")


if __name__ == "__main__":
    asyncio.run(main())
