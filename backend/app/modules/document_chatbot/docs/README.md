# Document Chatbot (RAG)

Grounded Q&A over a single startup's documents. Retrieval and answering are startup-scoped: the
index key is the `startup_id`, so one startup never sees another's content. Document text is treated
as **data, not instructions** (prompt-injection defense).

## Architecture

| Concern | Where |
|---|---|
| Provider boundary (chat, embeddings, rerank) | `app/llm/nvidia.py` — NVIDIA NIM, GPT-OSS-120B + nv-embedqa-e5-v5 |
| Source → chunks (record cards / page-aware) | `ingestion.py` |
| Hybrid index (dense + BM25, RRF) + persistence | `retrieval.py` (`HybridIndex`) |
| Build / load / signature-invalidate index | `index_store.py` |
| Orchestration (retrieve → rerank → generate → cite) | `services/chat_service.py` |

Retrieval default = **Hybrid (RRF of dense + BM25)**; rerank is optional (`RAG_USE_RERANK`). See
`methodology.md` for the eval that chose these (`backend/eval/rag/rag_eval.py` reproduces it).

## Config (`.env`)

```
LLM_PROVIDER=nvidia
NVIDIA_API_KEY=...            # required for embeddings + generation; without it → BM25 + extractive fallback
NVIDIA_CHAT_MODEL=openai/gpt-oss-120b
NVIDIA_EMBED_MODEL=nvidia/nv-embedqa-e5-v5
RAG_TOP_K=5
RAG_CANDIDATE_K=10
RAG_USE_RERANK=false
```

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

No `NVIDIA_API_KEY` (or API failure): index is BM25-only and answers fall back to extractive
(most-relevant chunk). The endpoint never hard-fails.

## Known limitations

- Vector RAG answers **lookups** well but not **aggregations** (counts/sums over many rows) — top-k
  only sees a few cards. Route aggregate questions to a structured/pandas tool if needed.
- Out-of-corpus questions are refused by the model but `grounded` may still read `true`; a stricter
  "no-evidence" gate is future work.
