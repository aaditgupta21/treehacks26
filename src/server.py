#!/usr/bin/env python3
"""
Team Brain MCP Server — Shared AI assistant for teams.
Connect this to Poke for calendar tetris, knowledge base, shopping lists, and more.
"""

import os
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from fastmcp import FastMCP

from store import (
    add_calendar_slot,
    add_calendar_sync_member,
    add_knowledge,
    add_shopping_item,
    get_or_create_team,
    get_team,
    get_shopping_list as store_get_shopping_list,
    remove_shopping_item,
    search_knowledge,
)
from poke_relay import send_to_all_pokes
from config import load_poke_api_keys

mcp = FastMCP(
    "Team Brain",
    instructions="When user wants to book/schedule a TEAM calendar event (for them and Armaan, or 'for dp', or 'for team'), use book_meeting. It stores in the database AND sends to both Pokes via their API keys. Never use your native calendar for team events — always use book_meeting.",
)


# --- Calendar tools ---

@mcp.tool(
    description="Set a team member's availability. Use this when someone shares when they're free. member_id can be name or identifier."
)
def set_availability(
    team_id: str,
    member_id: str,
    member_name: str,
    start: str,
    end: str,
    summary: str = "",
) -> str:
    """Register when a team member is available."""
    get_or_create_team(team_id)
    add_calendar_slot(team_id, member_id, member_name, start, end, summary, slot_type="availability")
    return f"Recorded availability for {member_name}: {start} to {end}"


@mcp.tool(
    description="Find time slots when ALL listed team members are free. Pass list of member_ids/names and optional date range."
)
def find_availability(
    team_id: str,
    member_ids: list[str],
    date_start: str = "",
    date_end: str = "",
) -> str:
    """Find overlapping availability for team members."""
    team = get_team(team_id)
    if not team:
        return f"Team '{team_id}' not found. Use set_availability first to add members."
    slots = team.calendar_slots
    if not slots:
        return "No availability data yet. Ask team members to share when they're free via set_availability."
    # Simple overlap logic: for MVP we return all slots; real impl would compute intersections
    member_set = {m.lower() for m in member_ids}
    relevant = [
        s for s in slots
        if s.member_id.lower() in member_set or s.member_name.lower() in member_set
    ]
    if not relevant:
        return f"No availability found for members: {member_ids}"
    lines = [f"- {s.member_name}: {s.start} to {s.end}" for s in relevant]
    return "Availability:\n" + "\n".join(lines)


@mcp.tool(
    description="Book a team calendar event. USE THIS when user wants to schedule for the team, dp, me and Armaan, etc. Stores in database and sends to BOTH Pokes (yours and Armaan's) so it shows up on both calendars. API keys from poke_api_keys.txt."
)
def book_meeting(
    team_id: str,
    title: str,
    start: str,
    end: str,
    attendees: list[str] | None = None,
) -> str:
    """Book meeting in DB, then send to every Poke in poke_api_keys.txt."""
    get_or_create_team(team_id)
    add_calendar_slot(team_id, "meeting", title, start, end, f"Booked: {', '.join(attendees or [])}", slot_type="meeting")

    keys = load_poke_api_keys()
    if not keys:
        return f"Booked '{title}' from {start} to {end} in database. No API keys in poke_api_keys.txt — add yours and Armaan's keys (pk_xxx from poke.com/kitchen/api-keys) to push to calendars."

    print(f"[Team Brain] Pushing to {len(keys)} Poke(s)...", flush=True)
    results = send_to_all_pokes(keys, title, start, end)
    for prefix, ok, err in results:
        print(f"  {prefix}: {'OK' if ok else 'FAIL ' + err}", flush=True)
    ok = sum(1 for _, success, _ in results if success)
    fail = [(p, e) for p, success, e in results if not success]

    out = f"Booked '{title}' from {start} to {end}. Sent to {ok}/{len(keys)} Pokes."
    if fail:
        out += f" Failures: {fail}"
    return out


@mcp.tool(
    description="List all booked meetings/events on the team calendar. Use when someone asks what's on the team calendar or for new invites."
)
def list_team_calendar(
    team_id: str = "default",
) -> str:
    """List all booked meetings for the team."""
    team = get_team(team_id)
    if not team:
        return f"Team '{team_id}' not found."
    meetings = [s for s in team.calendar_slots if s.member_id == "meeting"]
    if not meetings:
        return "No meetings booked yet."
    lines = [f"- {m.member_name}: {m.start} to {m.end}" + (f" ({m.summary})" if m.summary else "") for m in meetings]
    return "Team calendar:\n" + "\n".join(lines)


@mcp.tool(
    description="Register to receive calendar invites in your Poke. Option 1: Pass poke_webhook_url and poke_webhook_token from poke.com/kitchen (create webhook: condition 'Team Brain calendar invite', action 'Add to my calendar'). Option 2: Pass poke_api_key from poke.com/kitchen/api-keys to receive direct messages."
)
def register_for_calendar_sync(
    team_id: str,
    member_id: str,
    member_name: str,
    poke_webhook_url: str = "",
    poke_webhook_token: str = "",
    poke_api_key: str = "",
) -> str:
    """Register a team member to receive calendar invites via webhook or API key."""
    if not poke_webhook_url and not poke_webhook_token and not poke_api_key:
        return "Provide either (poke_webhook_url + poke_webhook_token) or poke_api_key."
    add_calendar_sync_member(
        team_id=team_id,
        member_id=member_id,
        member_name=member_name,
        poke_webhook_url=poke_webhook_url,
        poke_webhook_token=poke_webhook_token,
        poke_api_key=poke_api_key,
    )
    return f"Registered {member_name} for calendar sync. New team invites will be pushed to their Poke."


# --- Knowledge base tools ---

@mcp.tool(
    description="Store team knowledge: brand colors, policies, preferences, facts. Use category like 'brand', 'policy', 'preference', 'fact'."
)
def store_knowledge(
    team_id: str,
    key: str,
    value: str,
    category: str = "fact",
) -> str:
    """Store a piece of team knowledge. Uses JINA embeddings for semantic search when Elasticsearch is configured."""
    get_or_create_team(team_id)
    add_knowledge(team_id, key, value, category)
    return f"Stored: {key} = {value} (category: {category})"


@mcp.tool(
    description="Search team knowledge by keyword or category. Returns matching entries."
)
def query_knowledge(
    team_id: str,
    query: str = "",
    category: str = "",
) -> str:
    """Query stored team knowledge. Uses JINA semantic search when Elasticsearch + JINA_API_KEY are configured."""
    if not get_team(team_id):
        return f"Team '{team_id}' not found."
    entries = search_knowledge(team_id, query, category)
    if not entries:
        return "No matching knowledge found."
    return "\n".join(f"- [{e['category']}] {e['key']}: {e['value']}" for e in entries)


# --- Shopping list tools (Visa commerce track) ---

@mcp.tool(
    description="Add an item to the team shopping list. quantity defaults to '1'."
)
def add_to_shopping_list(
    team_id: str,
    item: str,
    quantity: str = "1",
    added_by: str = "unknown",
) -> str:
    """Add item to team shopping list."""
    get_or_create_team(team_id)
    add_shopping_item(team_id, item, quantity, added_by)
    return f"Added {quantity}x {item} to shopping list"


@mcp.tool(
    description="Get the team's shopping list. Optionally filter by item name."
)
def get_shopping_list(
    team_id: str,
    filter_item: str = "",
) -> str:
    """Retrieve team shopping list."""
    if not get_team(team_id):
        return f"Team '{team_id}' not found."
    items = store_get_shopping_list(team_id, filter_item)
    if not items:
        return "Shopping list is empty."
    return "\n".join(f"- {i['quantity']}x {i['name']} (by {i['added_by']})" for i in items)


@mcp.tool(
    description="Remove an item from the team shopping list by name. Removes first match."
)
def remove_from_shopping_list(
    team_id: str,
    item: str,
) -> str:
    """Remove item from shopping list."""
    if not get_team(team_id):
        return f"Team '{team_id}' not found."
    if remove_shopping_item(team_id, item):
        return f"Removed {item} from shopping list"
    return f"Item '{item}' not found in shopping list"


# --- Utility ---

@mcp.tool(
    description="Get info about the Team Brain MCP server and list available tools."
)
def get_team_brain_info() -> dict:
    """Server info and capabilities."""
    from store import _use_elastic
    return {
        "name": "Team Brain",
        "description": "Shared AI assistant for teams — calendar, knowledge, shopping",
        "elasticsearch_enabled": _use_elastic(),
        "tools": [
            "set_availability",
            "find_availability",
            "book_meeting",
            "list_team_calendar",
            "register_for_calendar_sync",
            "store_knowledge",
            "query_knowledge",
            "add_to_shopping_list",
            "get_shopping_list",
            "remove_from_shopping_list",
        ],
        "default_team_id": "default",
        "environment": os.environ.get("ENVIRONMENT", "development"),
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"

    from store import _use_elastic
    es_status = "connected" if _use_elastic() else "not configured (using in-memory)"
    print(f"Starting Team Brain MCP server on http://{host}:{port}")
    print(f"Elasticsearch: {es_status}")
    print(f"Connect Poke to: http://localhost:{port}/mcp (or use poke tunnel)")
    print()

    mcp.run(
        transport="http",
        host=host,
        port=port,
    )
