"""
Elasticsearch backend for Team Brain.
Uses Elastic Cloud (ELASTIC_CLOUD_ID + ELASTIC_API_KEY) or ELASTIC_URL + ELASTIC_API_KEY.
Knowledge base uses JINA v3 embeddings for semantic search.
"""

import os
from datetime import datetime
from typing import Any, Optional

from embeddings import get_embedding, get_query_embedding

# Index names
IDX_TEAMS = "team_brain_teams"
IDX_KNOWLEDGE = "team_brain_knowledge"
IDX_CALENDAR = "team_brain_calendar"
IDX_SHOPPING = "team_brain_shopping"

JINA_DIMS = 1024

_client = None


def _es_client():
    global _client
    if _client is not None:
        return _client
    api_key = os.environ.get("ELASTIC_API_KEY")
    if not api_key:
        return None
    url = os.environ.get("ELASTIC_URL", "").strip()
    cloud_id = os.environ.get("ELASTIC_CLOUD_ID", "").strip()
    try:
        from elasticsearch import Elasticsearch

        # Prefer ELASTIC_URL (full https URL) - same as curl, most reliable
        if url and url.startswith("http"):
            _client = Elasticsearch(hosts=[url], api_key=api_key)
        elif cloud_id:
            _client = Elasticsearch(cloud_id=cloud_id, api_key=api_key)
        else:
            return None
        _client.info()
        return _client
    except Exception:
        return None


def _ensure_indices(es):
    """Create indices with mappings. Knowledge index has dense_vector for JINA embeddings."""
    if not es:
        return

    # Knowledge index with vector field for semantic search
    if not es.indices.exists(index=IDX_KNOWLEDGE):
        es.indices.create(
            index=IDX_KNOWLEDGE,
            body={
                "mappings": {
                    "properties": {
                        "team_id": {"type": "keyword"},
                        "key": {"type": "text"},
                        "value": {"type": "text"},
                        "category": {"type": "keyword"},
                        "created_at": {"type": "date"},
                        "embedding": {
                            "type": "dense_vector",
                            "dims": JINA_DIMS,
                            "index": True,
                            "similarity": "cosine",
                        },
                    }
                }
            },
        )

    for idx, props in [
        (IDX_TEAMS, {"team_id": "keyword", "name": "text"}),
        (IDX_CALENDAR, {"team_id": "keyword", "member_id": "keyword", "member_name": "text", "start": "date", "end": "date", "summary": "text", "type": "keyword"}),
        (IDX_SHOPPING, {"team_id": "keyword", "name": "text", "quantity": "keyword", "added_by": "keyword", "created_at": "date"}),
    ]:
        if not es.indices.exists(index=idx):
            es.indices.create(
                index=idx,
                body={"mappings": {"properties": {k: {"type": v} for k, v in props.items()}}},
            )


def is_available() -> bool:
    return _es_client() is not None


# --- Team ---

def _log(prefix: str, index: str, count: int, extra: str = "") -> None:
    print(f"[ES] {prefix} {index}: {count} docs" + (f" ({extra})" if extra else ""), flush=True)


def get_or_create_team(team_id: str, name: str = "My Team") -> dict:
    es = _es_client()
    if not es:
        raise RuntimeError("Elasticsearch not configured")
    _ensure_indices(es)
    r = es.search(index=IDX_TEAMS, query={"term": {"team_id": team_id}}, size=1)
    hits = r.get("hits", {}).get("hits", [])
    _log("FETCH", IDX_TEAMS, len(hits), f"team_id={team_id}")
    if hits:
        return hits[0]["_source"]
    doc = {"team_id": team_id, "name": name}
    es.index(index=IDX_TEAMS, document=doc)
    return doc


def get_team(team_id: str) -> Optional[dict]:
    es = _es_client()
    if not es:
        return None
    r = es.search(index=IDX_TEAMS, query={"term": {"team_id": team_id}}, size=1)
    hits = r.get("hits", {}).get("hits", [])
    _log("FETCH", IDX_TEAMS, len(hits), f"team_id={team_id}")
    return hits[0]["_source"] if hits else None


# --- Calendar ---

def add_calendar_slot(team_id: str, member_id: str, member_name: str, start: str, end: str, summary: str = "", slot_type: str = "availability") -> None:
    es = _es_client()
    if not es:
        return
    _ensure_indices(es)
    es.index(
        index=IDX_CALENDAR,
        document={
            "team_id": team_id,
            "member_id": member_id,
            "member_name": member_name,
            "start": start,
            "end": end,
            "summary": summary,
            "type": slot_type,
        },
    )


def get_calendar_slots(team_id: str, member_id_filter: Optional[str] = None, slot_type: Optional[str] = None) -> list:
    """Get calendar slots. slot_type: 'availability' or 'meeting' or None for all."""
    es = _es_client()
    if not es:
        return []
    must = [{"term": {"team_id": team_id}}]
    if member_id_filter:
        must.append({"term": {"member_id": member_id_filter}})
    if slot_type:
        must.append({"term": {"type": slot_type}})
    r = es.search(index=IDX_CALENDAR, query={"bool": {"must": must}}, size=100, sort=[{"start": "asc"}])
    hits = r.get("hits", {}).get("hits", [])
    _log("FETCH", IDX_CALENDAR, len(hits), f"team_id={team_id}")
    return [h["_source"] for h in hits]


# --- Knowledge (with JINA semantic search) ---

def add_knowledge(team_id: str, key: str, value: str, category: str = "fact") -> None:
    es = _es_client()
    if not es:
        return
    _ensure_indices(es)
    text = f"{key}: {value}"
    embedding = get_embedding(text)
    doc = {
        "team_id": team_id,
        "key": key,
        "value": value,
        "category": category,
        "created_at": datetime.utcnow().isoformat(),
    }
    if embedding:
        doc["embedding"] = embedding
    es.index(index=IDX_KNOWLEDGE, document=doc)


def query_knowledge(team_id: str, query: str = "", category: str = "", semantic: bool = True, limit: int = 10) -> list:
    es = _es_client()
    if not es:
        return []
    must = [{"term": {"team_id": team_id}}]
    if category:
        must.append({"term": {"category": category}})
    filt = {"bool": {"must": must}} if must else {"match_all": {}}

    if query and semantic:
        emb = get_query_embedding(query)
        if emb:
            r = es.search(
                index=IDX_KNOWLEDGE,
                size=limit,
                query={
                    "knn": {
                        "field": "embedding",
                        "query_vector": emb,
                        "k": limit,
                        "num_candidates": limit * 2,
                        "filter": filt,
                    }
                },
            )
            hits = r.get("hits", {}).get("hits", [])
            _log("FETCH", IDX_KNOWLEDGE, len(hits), f"team_id={team_id} query={'...' if query else 'all'}")
            return [h["_source"] for h in hits]
    if query:
        must.append({"multi_match": {"query": query, "fields": ["key", "value"], "type": "best_fields"}})
    r = es.search(index=IDX_KNOWLEDGE, query={"bool": {"must": must}} if must else {"match_all": {}}, size=limit)
    hits = r.get("hits", {}).get("hits", [])
    _log("FETCH", IDX_KNOWLEDGE, len(hits), f"team_id={team_id}")
    return [h["_source"] for h in hits]


# --- Shopping ---

def add_shopping_item(team_id: str, name: str, quantity: str = "1", added_by: str = "unknown") -> None:
    es = _es_client()
    if not es:
        return
    _ensure_indices(es)
    es.index(
        index=IDX_SHOPPING,
        document={
            "team_id": team_id,
            "name": name,
            "quantity": quantity,
            "added_by": added_by,
            "created_at": datetime.utcnow().isoformat(),
        },
    )


def get_shopping_list(team_id: str, filter_item: str = "") -> list:
    es = _es_client()
    if not es:
        return []
    must = [{"term": {"team_id": team_id}}]
    if filter_item:
        must.append({"match": {"name": filter_item}})
    r = es.search(index=IDX_SHOPPING, query={"bool": {"must": must}}, size=100, sort=[{"created_at": "asc"}])
    hits = r.get("hits", {}).get("hits", [])
    _log("FETCH", IDX_SHOPPING, len(hits), f"team_id={team_id}")
    return [h["_source"] for h in hits]


def remove_shopping_item(team_id: str, name: str) -> bool:
    es = _es_client()
    if not es:
        return False
    r = es.delete_by_query(
        index=IDX_SHOPPING,
        body={"query": {"bool": {"must": [{"term": {"team_id": team_id}}, {"term": {"name": name}}]}}},
    )
    return r.get("deleted", 0) > 0
