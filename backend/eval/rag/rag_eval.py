"""Reproducible retrieval eval for the VC-dataset RAG demo.

Compares BM25 (lexical), Dense (nv-embedqa-e5-v5), Hybrid (RRF), and Hybrid+LLM-rerank on two
query families: name-based (favors lexical) and attribute-paraphrase (favors dense). Metrics:
Recall@1/3/5 and MRR@10. Embeddings and generated questions are cached next to this file.

Run:
    NVIDIA_API_KEY=... python backend/eval/rag/rag_eval.py [path/to/investments_VC.csv]
"""
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
import requests
from rank_bm25 import BM25Okapi

KEY = os.environ["NVIDIA_API_KEY"]
BASE = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
HERE = Path(__file__).parent
DEFAULT_CSV = HERE.parents[2] / "investments_VC.csv"
CSV_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
EMB_MODEL = "nvidia/nv-embedqa-e5-v5"
CHAT_MODEL = "openai/gpt-oss-120b"
N_ROWS = 100
N_EVAL = 40


def clean(v):
    return (v or "").strip().strip("|").replace("|", ", ")


def money(v):
    v = (v or "").strip()
    return v.replace(",", "") if v and v not in {"-", "—"} else "0"


def load_cards():
    cards = []
    with CSV_PATH.open(encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [(fn or "").strip() for fn in reader.fieldnames]
        for i, row in enumerate(reader):
            if i >= N_ROWS:
                break
            row = {(k or "").strip(): v for k, v in row.items()}
            name = clean(row.get("name"))
            if not name:
                continue
            market, city = clean(row.get("market")) or "unknown", clean(row.get("city")) or "unknown city"
            country, status = clean(row.get("country_code")) or "unknown country", clean(row.get("status")) or "unknown"
            year, cats = clean(row.get("founded_year")) or "unknown year", clean(row.get("category_list"))
            total, rounds = money(row.get("funding_total_usd")), clean(row.get("funding_rounds")) or "0"
            text = (
                f"{name} is a startup in the {market} market based in {city}, {country}. "
                f"Operating status: {status}. Founded in {year}. Categories: {cats}. "
                f"Total funding raised: ${total} across {rounds} funding round(s)."
            )
            cards.append({"id": len(cards), "name": name, "market": market, "city": city,
                          "country": country, "year": year, "total": total, "text": text})
    return cards


def _post(url, payload, tries=4):
    for t in range(tries):
        r = requests.post(url, headers=H, json=payload, timeout=120)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 500, 502, 503):
            time.sleep(2 * (t + 1))
            continue
        raise RuntimeError(f"{r.status_code}: {r.text[:300]}")
    raise RuntimeError("retries exhausted")


def embed(texts, input_type, batch=16):
    out = []
    for i in range(0, len(texts), batch):
        j = _post(f"{BASE}/embeddings", {"model": EMB_MODEL, "input": texts[i:i + batch],
                                         "input_type": input_type, "truncate": "END"})
        out.extend(d["embedding"] for d in sorted(j["data"], key=lambda d: d["index"]))
    return np.array(out, dtype=np.float32)


def chat(prompt, system, max_tokens=800):
    j = _post(f"{BASE}/chat/completions", {"model": CHAT_MODEL, "temperature": 0, "max_tokens": max_tokens,
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]})
    return j["choices"][0]["message"].get("content") or ""


def build_questions(cards):
    cache = HERE / "questions.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    rng = np.random.default_rng(42)
    qs = []
    for idx in rng.choice(len(cards), size=min(N_EVAL, len(cards)), replace=False):
        c = cards[int(idx)]
        qs.append({"gold": c["id"], "kind": "name",
                   "q": f"How much total funding did {c['name']} raise and what is its status?"})
        sysmsg = ("You write ONE short retrieval question about a company, in English. Do NOT mention the "
                  "company name. Use distinctive attributes (market, city, country, founding year, funding "
                  "amount) so the question points to this one company. Output only the question.")
        prm = (f"Company facts: market={c['market']}, city={c['city']}, country={c['country']}, "
               f"founded={c['year']}, total_funding=${c['total']}. Write the question.")
        try:
            q = chat(prm, sysmsg, max_tokens=400).strip().strip('"').splitlines()[-1].strip()
        except Exception:
            q = f"Which {c['market']} startup in {c['city']} was founded in {c['year']}?"
        qs.append({"gold": c["id"], "kind": "attr", "q": q})
    cache.write_text(json.dumps(qs, ensure_ascii=False, indent=2), encoding="utf-8")
    return qs


def tokenize(s):
    return re.findall(r"[a-z0-9]+", s.lower())


def dense_ranks(card_emb, q_emb):
    cn = card_emb / (np.linalg.norm(card_emb, axis=1, keepdims=True) + 1e-9)
    return list(np.argsort(-(cn @ (q_emb / (np.linalg.norm(q_emb) + 1e-9)))))


def rrf(rank_lists, k=60):
    score = {}
    for rl in rank_lists:
        for pos, cid in enumerate(rl):
            score[cid] = score.get(cid, 0.0) + 1.0 / (k + pos + 1)
    return [cid for cid, _ in sorted(score.items(), key=lambda x: -x[1])]


def llm_rerank(q, cand_ids, cards, topn=10):
    cand = cand_ids[:topn]
    listing = "\n".join(f"[{i}] {cards[cid]['text']}" for i, cid in enumerate(cand))
    sysmsg = ("You are a search reranker. Given a question and numbered passages, return the passage indices "
              "from most to least relevant as a JSON list of integers, e.g. [3,0,1]. Output only the JSON list.")
    try:
        raw = chat(f"Question: {q}\n\nPassages:\n{listing}", sysmsg, max_tokens=200)
        order = json.loads(re.search(r"\[.*\]", raw, re.S).group(0))
        seen, ranked = set(), []
        for i in order:
            if isinstance(i, int) and 0 <= i < len(cand) and i not in seen:
                seen.add(i)
                ranked.append(cand[i])
        ranked += [cand[j] for j in range(len(cand)) if j not in seen]
        return ranked + cand_ids[topn:]
    except Exception:
        return cand_ids


def metrics(ranked, gold):
    pos = ranked.index(gold) if gold in ranked else 10 ** 6
    return {"r1": float(pos < 1), "r3": float(pos < 3), "r5": float(pos < 5),
            "mrr": 1.0 / (pos + 1) if pos < 10 else 0.0}


def agg(rows):
    return {k: round(sum(r[k] for r in rows) / len(rows), 3) for k in ["r1", "r3", "r5", "mrr"]}


def main():
    cards = load_cards()
    print(f"Loaded {len(cards)} cards")
    ecache = HERE / "card_emb.npy"
    card_emb = np.load(ecache) if ecache.exists() else embed([c["text"] for c in cards], "passage")
    if not ecache.exists():
        np.save(ecache, card_emb)
    bm25 = BM25Okapi([tokenize(c["text"]) for c in cards])

    qs = build_questions(cards)
    qec = HERE / "q_emb.npy"
    q_emb = np.load(qec) if qec.exists() else embed([x["q"] for x in qs], "query")
    if not qec.exists():
        np.save(qec, q_emb)
    print(f"{len(qs)} eval questions")

    methods = ["bm25", "dense", "hybrid", "hybrid+rerank"]
    results = {m: {"name": [], "attr": [], "all": []} for m in methods}
    for i, item in enumerate(qs):
        gold, kind, q = item["gold"], item["kind"], item["q"]
        dr, br = dense_ranks(card_emb, q_emb[i]), list(np.argsort(-bm25.get_scores(tokenize(q))))
        hy = rrf([[int(x) for x in dr], [int(x) for x in br]])
        per = {"bm25": br, "dense": dr, "hybrid": hy, "hybrid+rerank": llm_rerank(q, hy, cards, 10)}
        for m in methods:
            mt = metrics([int(x) for x in list(per[m])[:50]], gold)
            results[m][kind].append(mt)
            results[m]["all"].append(mt)
        print(".", end="", flush=True)
    print()
    print(f"\n{'method':16} {'split':6} {'R@1':>6} {'R@3':>6} {'R@5':>6} {'MRR':>6}\n" + "-" * 52)
    for m in methods:
        for split in ["name", "attr", "all"]:
            a = agg(results[m][split])
            print(f"{m:16} {split:6} {a['r1']:6.3f} {a['r3']:6.3f} {a['r5']:6.3f} {a['mrr']:6.3f}")
        print()


if __name__ == "__main__":
    main()
