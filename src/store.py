"""
Team Brain store — Elasticsearch only.
Set ELASTIC_URL + ELASTIC_API_KEY (or ELASTIC_CLOUD_ID + ELASTIC_API_KEY).
"""

from dataclasses import dataclass
from typing import Optional

from elastic_store import (
    get_or_create_team as _es_get_or_create_team,
    get_team as _es_get_team,
    add_calendar_slot as _es_add_calendar_slot,
    get_calendar_slots as _es_get_calendar_slots,
    add_knowledge as _es_add_knowledge,
    query_knowledge as _es_query_knowledge,
    add_shopping_item as _es_add_shopping_item,
    get_shopping_list as _es_get_shopping_list,
    remove_shopping_item as _es_remove_shopping_item,
)


@dataclass
class CalendarSlot:
    member_id: str
    member_name: str
    start: str
    end: str
    summary: Optional[str] = None


@dataclass
class KnowledgeEntry:
    key: str
    value: str
    category: str
    created_at: str


@dataclass
class ShoppingItem:
    name: str
    quantity: str = "1"
    added_by: str = "unknown"
    created_at: str = ""


@dataclass
class TeamData:
    team_id: str
    name: str
    calendar_slots: list
    knowledge: list
    shopping_list: list


def _team_from_elastic(team_id: str, name: str) -> TeamData:
    slots = _es_get_calendar_slots(team_id)
    knowledge = _es_query_knowledge(team_id, limit=100)
    shopping = _es_get_shopping_list(team_id)
    return TeamData(
        team_id=team_id,
        name=name,
        calendar_slots=[CalendarSlot(**{k: s.get(k, "") for k in ["member_id", "member_name", "start", "end", "summary"]}) for s in slots],
        knowledge=[KnowledgeEntry(key=e["key"], value=e["value"], category=e["category"], created_at=e.get("created_at", "")) for e in knowledge],
        shopping_list=[ShoppingItem(name=i["name"], quantity=i.get("quantity", "1"), added_by=i.get("added_by", "unknown"), created_at=i.get("created_at", "")) for i in shopping],
    )


def get_or_create_team(team_id: str, name: str = "My Team") -> TeamData:
    _es_get_or_create_team(team_id, name)
    return _team_from_elastic(team_id, name)


def get_team(team_id: str) -> Optional[TeamData]:
    t = _es_get_team(team_id)
    if not t:
        return None
    return _team_from_elastic(team_id, t.get("name", "My Team"))


def add_calendar_slot(team_id: str, member_id: str, member_name: str, start: str, end: str, summary: str = "", slot_type: str = "availability") -> None:
    _es_add_calendar_slot(team_id, member_id, member_name, start, end, summary, slot_type)


def add_knowledge(team_id: str, key: str, value: str, category: str = "fact") -> None:
    _es_add_knowledge(team_id, key, value, category)


def search_knowledge(team_id: str, query: str = "", category: str = "") -> list:
    return _es_query_knowledge(team_id, query, category)


def add_shopping_item(team_id: str, name: str, quantity: str = "1", added_by: str = "unknown") -> None:
    _es_add_shopping_item(team_id, name, quantity, added_by)


def get_shopping_list(team_id: str, filter_item: str = "") -> list:
    return _es_get_shopping_list(team_id, filter_item)


def remove_shopping_item(team_id: str, name: str) -> bool:
    return _es_remove_shopping_item(team_id, name)


def add_calendar_sync_member(
    team_id: str,
    member_id: str,
    member_name: str,
    poke_webhook_url: str = "",
    poke_webhook_token: str = "",
    poke_api_key: str = "",
) -> None:
    """Calendar sync uses poke_api_keys.txt; no ES storage."""
    pass
