"""In-memory store for team data. Replace with DB (e.g. Elasticsearch) for production."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# Global in-memory store keyed by team_id
_teams: dict[str, "TeamData"] = {}


@dataclass
class CalendarSyncMember:
    """A team member registered to receive calendar invites."""
    member_id: str
    member_name: str
    poke_webhook_url: str = ""
    poke_webhook_token: str = ""
    poke_api_key: str = ""  # Alternative: send message directly to their Poke


@dataclass
class CalendarSlot:
    """A calendar availability slot."""
    member_id: str
    member_name: str
    start: str
    end: str
    summary: Optional[str] = None


@dataclass
class KnowledgeEntry:
    """A stored knowledge item."""
    key: str
    value: str
    category: str
    created_at: str


@dataclass
class ShoppingItem:
    """A shopping list item."""
    name: str
    quantity: str = "1"
    added_by: str = "unknown"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class TeamData:
    team_id: str
    name: str
    members: list[dict] = field(default_factory=list)
    calendar_sync_members: list[CalendarSyncMember] = field(default_factory=list)
    calendar_slots: list[CalendarSlot] = field(default_factory=list)
    knowledge: list[KnowledgeEntry] = field(default_factory=list)
    shopping_list: list[ShoppingItem] = field(default_factory=list)


def get_or_create_team(team_id: str, name: str = "My Team") -> TeamData:
    """Get existing team or create new one."""
    if team_id not in _teams:
        _teams[team_id] = TeamData(team_id=team_id, name=name)
    return _teams[team_id]


def get_team(team_id: str) -> Optional[TeamData]:
    """Get team by ID."""
    return _teams.get(team_id)


def add_calendar_sync_member(
    team_id: str,
    member_id: str,
    member_name: str,
    poke_webhook_url: str = "",
    poke_webhook_token: str = "",
    poke_api_key: str = "",
) -> TeamData:
    """Register a team member to receive calendar invites via Poke webhook."""
    team = get_or_create_team(team_id)
    # Replace if already registered
    team.calendar_sync_members = [
        m for m in team.calendar_sync_members if m.member_id != member_id
    ]
    team.calendar_sync_members.append(
        CalendarSyncMember(
            member_id=member_id,
            member_name=member_name,
            poke_webhook_url=poke_webhook_url,
            poke_webhook_token=poke_webhook_token,
            poke_api_key=poke_api_key,
        )
    )
    return team
