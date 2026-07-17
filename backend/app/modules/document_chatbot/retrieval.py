import re
from typing import Any


def retrieve(question: str, documents: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    """Startup-scoped lexical baseline; replace with vector retrieval behind this interface."""
    terms = {term.lower() for term in re.findall(r"\w+", question, flags=re.UNICODE) if len(term) > 2}
    candidates: list[tuple[int, dict[str, Any]]] = []
    for document in documents:
        text = document.get("text", "")
        chunks = [text[index : index + 1200] for index in range(0, len(text), 1000)]
        for chunk in chunks:
            lower = chunk.lower()
            score = sum(lower.count(term) for term in terms)
            if score:
                candidates.append((score, {**document, "excerpt": chunk.strip()}))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return [candidate for _, candidate in candidates[:limit]]
