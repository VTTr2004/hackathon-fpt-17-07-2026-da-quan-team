# Document Chatbot (RAG)

Grounded Q&A over a single startup's documents. Retrieval and answering are startup-scoped: the
index key is the `startup_id`, so one startup never sees another's content. Document text is treated
as **data, not instructions** (prompt-injection defense).

## Architecture

| Concern | Where |
|---|---|
| Provider selection (Gemini default, NVIDIA optional) | `app/llm/rag_client.py` |
| Gemini boundary (chat, embeddings, rerank) | `app/llm/gemini.py` — `gemini-flash-latest` + `gemini-embedding-001` |
| NVIDIA boundary (chat, embeddings, rerank) | `app/llm/nvidia.py` — GPT-OSS-120B + nv-embedqa-e5-v5 |
| Source → chunks (CSV / JSON / XLSX / text, page-aware) | `ingestion.py` (`file_to_chunks` dispatch) |
| Hybrid index (dense + BM25, RRF) + persistence | `retrieval.py` (`HybridIndex`) |
| Build / load / signature-invalidate index | `index_store.py` |
| Orchestration (retrieve → rerank → generate → cite) | `services/chat_service.py` |

Both providers expose the same trio (`generate_text`, `embed_texts(input_type=...)`, `rerank`), so
the pipeline is provider-agnostic. `LLM_PROVIDER` picks one. Index files are namespaced by
provider + embed model, so switching providers rebuilds cleanly (dims differ: Gemini 1024, NVIDIA 1024).

Retrieval default = **Hybrid (RRF of dense + BM25)**; rerank is optional (`RAG_USE_RERANK`). See
`methodology.md` for the eval that chose these (`backend/eval/rag/rag_eval.py` reproduces it).

## Config (`.env`)

```
LLM_PROVIDER=gemini          # "gemini" (default) or "nvidia"
# Gemini (default)
GEMINI_API_KEY=...           # without a working key → BM25 + extractive fallback
GEMINI_MODEL=gemini-flash-latest
GEMINI_EMBED_MODEL=gemini-embedding-001
# NVIDIA (alternative)
NVIDIA_API_KEY=...
NVIDIA_CHAT_MODEL=openai/gpt-oss-120b
NVIDIA_EMBED_MODEL=nvidia/nv-embedqa-e5-v5
RAG_TOP_K=5
RAG_CANDIDATE_K=10
RAG_USE_RERANK=false
```

> Gemini free-tier embeddings rate-limit (429) easily; the boundary retries with backoff and, if
> still failing, the index/query degrades to BM25. For heavy demos prefer a billed key or NVIDIA.

## VC-dataset demo (100 rows)

```bash
# 1. create a startup via API, note its id
# 2. build the per-company index for that startup
cd backend
python -m scripts.seed_vc_index --startup-id <startup_uuid> --csv ../investments_VC.csv --limit 100
# 3. POST /api/v1/startups/<id>/chat  {"question": "..."} — loads the prebuilt index
```

Each row becomes one natural-language record card; citations resolve to `dòng <n>` of the CSV.

## Index lifecycle

- **Seeded index** (CSV demo, startup has no `Document` rows): chat passes no documents → the
  persisted index is authoritative and reused as-is.
- **Uploaded documents**: chat rebuilds the index whenever the documents' content signature changes
  (`documents_signature`), so edits/new uploads are reflected.

## Graceful degradation

If the active provider's key is missing (or the API fails): the index is BM25-only and answers fall
back to extractive (most-relevant chunk). The endpoint never hard-fails.

## Ingestion by file type (`file_to_chunks`)

| Type | Handler | Chunking |
|---|---|---|
| CSV (VC dataset) | `csv_rows_to_chunks` | 1 row → 1 record card |
| JSON (profile, location) | `json_to_chunks` | flatten to `key: value` lines → 1 descriptive card |
| XLSX (workbooks) | `xlsx_to_chunks` | structure-aware, see below |
| TXT / MD | inline read → `text_to_chunks` | overlapping windows |
| PDF / DOCX / PPTX | `document_parser` → `text_to_chunks` | overlapping windows, page/slide markers |

**Tabular data (XLSX) — three tiers.** Business workbooks are mostly financial/transaction tables,
so a naive "dump whole sheet → slice by 1000 chars" breaks rows, loses headers, and lets hundreds of
transaction rows drown retrieval (and burn embedding quota). Instead `xlsx_to_chunks`:
1. **Summary cards** — each `Tóm tắt` sheet's metric/monthly rows become one labeled card each
   (precomputed aggregates: total revenue, monthly breakdown, closing balance).
2. **Dimension cards** — small sheets (Menu, suppliers, staff, utilities) → one labeled card per row.
3. **Transaction rows** — capped at `max_data_rows` (default 40) per sheet; oversized sheets get an
   overview card instead of thousands of row cards. Header detection tracks per-table headers (first
   multi-column row after a blank/title), so multi-table sheets label rows correctly.

Validated on `sample-data/goc-ho-coffee` (Excel + JSON): profile lookups, per-month revenue, closing
balance, menu prices, and supplier lookups all answered correctly with citations. Seed a folder with
`scripts/seed_folder_index.py` (skips PDF unless `--include-pdf`).

## Known limitations

- Vector RAG answers **lookups** and **precomputed aggregates** (from `Tóm tắt` cards) well, but not
  **arbitrary aggregations** not already computed (e.g. "revenue of Americano via delivery in May").
  Those need a structured/pandas/SQL tool over the raw sheets — planned as a future retrieval route.
- Out-of-corpus questions are refused by the model but `grounded` may still read `true`; a stricter
  "no-evidence" gate is future work.
