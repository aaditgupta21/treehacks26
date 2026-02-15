"""
JINA embeddings v3 for semantic search.
https://jina.ai/embeddings | jina-embeddings-v3
"""

import os
from typing import List

import httpx

JINA_API = "https://api.jina.ai/v1/embeddings"
JINA_DIMS = 1024


def get_embedding(text: str, task: str = "retrieval.passage") -> List[float] | None:
    """Get embedding for a single text. Returns None if JINA_API_KEY not set."""
    key = os.environ.get("JINA_API_KEY")
    if not key:
        return None
    try:
        r = httpx.post(
            JINA_API,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "input": [text],
                "model": "jina-embeddings-v3",
                "dimensions": JINA_DIMS,
                "task": task,
            },
            timeout=10.0,
        )
        if r.status_code >= 400:
            return None
        data = r.json()
        embeds = data.get("data", [])
        return embeds[0]["embedding"] if embeds else None
    except Exception:
        return None


def get_query_embedding(text: str) -> List[float] | None:
    """Get embedding for a search query (use retrieval.query task)."""
    return get_embedding(text, task="retrieval.query")
