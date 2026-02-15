"""
Unified store: uses Elasticsearch + JINA when configured, else in-memory.
Set ELASTIC_CLOUD_ID + ELASTIC_API_KEY (or ELASTIC_URL) and JINA_API_KEY for Elastic + semantic search.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

# Try Elasticsearch backend
try:
    from elastic_store import (
        is_available as _es_available,
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
except ImportError:
    _es_available = lambda: False

# In-memory fallback
_teams: dict[str, "TeamData"] = {}


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
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class CalendarSyncMember:
    member_id: str
    member_name: str
    poke_webhook_url: str = ""
    poke_webhook_token: str = ""
    poke_api_key: str = ""


@dataclass
class TeamData:
    team_id: str
    name: str
    members: list = field(default_factory=list)
    calendar_sync_members: list = field(default_factory=list)
    calendar_slots: list = field(default_factory=list)
    knowledge: list = field(default_factory=list)
    shopping_list: list = field(default_factory=list)


def _use_elastic() -> bool:
    return _es_available()


# --- Public API ---

def get_or_create_team(team_id: str, name: str = "My Team") -> TeamData:
    if _use_elastic():
        _es_get_or_create_team(team_id, name)
        return _team_from_elastic(team_id, name)
    if team_id not in _teams:
        _teams[team_id] = TeamData(team_id=team_id, name=name)
    return _teams[team_id]


def get_team(team_id: str) -> Optional[TeamData]:
    if _use_elastic():
        t = _es_get_team(team_id)
        if not t:
            return None
        return _team_from_elastic(team_id, t.get("name", "My Team"))
    return _teams.get(team_id)


def _team_from_elastic(team_id: str, name: str) -> TeamData:
    """Build TeamData from Elasticsearch."""
    slots = _es_get_calendar_slots(team_id) if _use_elastic() else []  # no slot_type = all
    knowledge = _es_query_knowledge(team_id, limit=100) if _use_elastic() else []
    shopping = _es_get_shopping_list(team_id) if _use_elastic() else []
    return TeamData(
        team_id=team_id,
        name=name,
        calendar_slots=[CalendarSlot(**{k: s.get(k, "") for k in ["member_id", "member_name", "start", "end", "summary"]}) for s in slots],
        knowledge=[KnowledgeEntry(key=e["key"], value=e["value"], category=e["category"], created_at=e.get("created_at", "")) for e in knowledge],
        shopping_list=[ShoppingItem(name=i["name"], quantity=i.get("quantity", "1"), added_by=i.get("added_by", "unknown"), created_at=i.get("created_at", "")) for i in shopping],
    )


def add_calendar_slot(team_id: str, member_id: str, member_name: str, start: str, end: str, summary: str = "", slot_type: str = "availability") -> None:
    if _use_elastic():
        _es_add_calendar_slot(team_id, member_id, member_name, start, end, summary, slot_type)
        return
    team = get_or_create_team(team_id)
    team.calendar_slots.append(CalendarSlot(member_id=member_id, member_name=member_name, start=start, end=end, summary=summary or None))


def add_knowledge(team_id: str, key: str, value: str, category: str = "fact") -> None:
    if _use_elastic():
        _es_add_knowledge(team_id, key, value, category)
        return
    team = get_or_create_team(team_id)
    team.knowledge.append(KnowledgeEntry(key=key, value=value, category=category, created_at=datetime.utcnow().isoformat()))


def search_knowledge(team_id: str, query: str = "", category: str = "") -> list:
    if _use_elastic():
        return _es_query_knowledge(team_id, query, category)
    team = get_team(team_id)
    if not team:
        return []
    entries = team.knowledge
    if query:
        q = query.lower()
        entries = [e for e in entries if q in e.key.lower() or q in e.value.lower()]
    if category:
        entries = [e for e in entries if e.category.lower() == category.lower()]
    return [{"key": e.key, "value": e.value, "category": e.category, "created_at": e.created_at} for e in entries]


def add_shopping_item(team_id: str, name: str, quantity: str = "1", added_by: str = "unknown") -> None:
    if _use_elastic():
        _es_add_shopping_item(team_id, name, quantity, added_by)
        return
    team = get_or_create_team(team_id)
    team.shopping_list.append(ShoppingItem(name=name, quantity=quantity, added_by=added_by))


def get_shopping_list(team_id: str, filter_item: str = "") -> list:
    if _use_elastic():
        return _es_get_shopping_list(team_id, filter_item)
    team = get_team(team_id)
    if not team:
        return []
    items = team.shopping_list
    if filter_item:
        fq = filter_item.lower()
        items = [i for i in items if fq in i.name.lower()]
    return [{"name": i.name, "quantity": i.quantity, "added_by": i.added_by, "created_at": i.created_at} for i in items]


def remove_shopping_item(team_id: str, name: str) -> bool:
    if _use_elastic():
        return _es_remove_shopping_item(team_id, name)
    team = get_team(team_id)
    if not team:
        return False
    for i, x in enumerate(team.shopping_list):
        if x.name.lower() == name.lower():
            team.shopping_list.pop(i)
            return True
    return False


def add_calendar_sync_member(
    team_id: str,
    member_id: str,
    member_name: str,
    poke_webhook_url: str = "",
    poke_webhook_token: str = "",
    poke_api_key: str = "",
) -> None:
    """Only used for in-memory; calendar push uses poke_api_keys.txt."""
    if _use_elastic():
        return
    team = get_or_create_team(team_id)
    team.calendar_sync_members = [m for m in team.calendar_sync_members if m.member_id != member_id]
    team.calendar_sync_members.append(
        CalendarSyncMember(member_id=member_id, member_name=member_name, poke_webhook_url=poke_webhook_url, poke_webhook_token=poke_webhook_token, poke_api_key=poke_api_key)
    )
