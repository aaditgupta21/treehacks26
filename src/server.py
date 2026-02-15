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
    add_knowledge,
    add_shopping_item,
    get_or_create_team,
    get_team,
    get_shopping_list as store_get_shopping_list,
    has_synced_calendar,
    remove_shopping_item,
    remove_meeting,
    search_knowledge,
    sync_member_calendar,
)
from elastic_store import get_calendar_slots as es_get_calendar_slots
from poke_relay import send_to_all_pokes
from config import load_poke_api_keys, load_poke_api_keys_with_names

mcp = FastMCP(
    "Team Brain",
    instructions="""IMPORTANT — two types of calendar events:

1. TEAM EVENTS (use book_meeting): When user wants to schedule something for BOTH of them (me and Armaan, team meeting, dp). Use book_meeting — it adds to both calendars and both attend. Never add team events via personal calendar.

2. SYNCED / INDIVIDUAL EVENTS (use sync_my_calendar): When user says 'sync my calendar', get THEIR events (next 7 days) and call sync_my_calendar. These are that person's personal events — stored in Team Brain ONLY for visibility so teammates can see when they're busy. NEVER add or book these events to anyone else's calendar. Armaan's synced events stay his; do NOT put them on Aadit's calendar. When checking availability, we read synced events to know when someone is busy — we do NOT copy them to other people's calendars.

Sync: member_id 'aadit' or 'armaan' based on who is messaging. Do NOT ask for API keys.
Availability: get_member_availability for whole-day, check_member_free for specific time. Pass requester_id.""",
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
    # Use names from poke_api_keys.txt as attendees (everyone who receives the invite)
    # Don't merge with AI-passed attendees — avoids duplicates like "Aadit" + "Aadit Gupta"
    keys_with_names = load_poke_api_keys_with_names()
    attendee_names = [n for n, _ in keys_with_names]
    keys = [k for _, k in keys_with_names]
    summary = f"Booked: {', '.join(attendee_names)}"
    add_calendar_slot(team_id, "meeting", title, start, end, summary, slot_type="meeting")

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
    description="Sync a member's calendar into Team Brain (next 7 days only). When user says 'sync my calendar', get their events for the next week and call this with events=[{title, start, end}, ...]. member_id: 'aadit' or 'armaan'. Do NOT ask for API key."
)
def sync_my_calendar(
    team_id: str,
    member_id: str,
    member_name: str,
    events: list[dict],
) -> str:
    """Import a member's calendar into Elasticsearch. Use when they join or ask to sync."""
    ev_list = events or []
    print(f"[Team Brain] sync_my_calendar: {member_name} ({member_id}) — received {len(ev_list)} events", flush=True)
    for i, ev in enumerate(ev_list[:5]):  # log first 5
        print(f"  [{i+1}] {ev.get('title', ev.get('name', '?'))[:40]} | {ev.get('start', '')} → {ev.get('end', '')}", flush=True)
    if len(ev_list) > 5:
        print(f"  ... and {len(ev_list) - 5} more", flush=True)
    print(f"[Team Brain] Putting {len(ev_list)} events into Team Brain calendar (Elasticsearch)...", flush=True)
    get_or_create_team(team_id)
    n = sync_member_calendar(team_id, member_id, member_name, ev_list)
    print(f"[Team Brain] sync_my_calendar done: indexed {n} events for {member_name}", flush=True)
    return f"Synced {n} calendar events for {member_name} into Team Brain."


@mcp.tool(
    description="Get a team member's availability for a whole day — when they're busy and when they're free. Use when user asks 'What's Armaan's availability for tomorrow' or 'when is Armaan free tomorrow'. member_id: 'aadit' or 'armaan'. date: YYYY-MM-DD. requester_id: who is asking."
)
def get_member_availability(
    team_id: str,
    member_id: str,
    date: str,
    requester_id: str = "",
) -> str:
    """Return member's schedule for a date — busy blocks and free slots. Uses synced calendar + team meetings."""
    if not get_team(team_id):
        return f"Team '{team_id}' not found."
    mid_lower = member_id.lower().strip()
    req_lower = requester_id.lower().strip() if requester_id else ""
    if not has_synced_calendar(team_id, mid_lower):
        return f"{member_id.capitalize()}'s calendar isn't in Team Brain yet. Ask them to say 'sync my calendar' in Poke so we can see their availability."
    slots = es_get_calendar_slots(team_id, slot_type=None)
    date_prefix = date if "-" in date else date[:10]
    busy = []
    for s in slots:
        slot_type = s.get("type", "")
        slot_mid = (s.get("member_id") or "").lower()
        slot_start = s.get("start") or ""
        slot_end = s.get("end") or ""
        if not slot_start or not slot_end or not slot_start.startswith(date_prefix):
            continue
        if slot_type == "synced" and slot_mid != mid_lower:
            continue
        if slot_type == "meeting":
            pass
        elif slot_type != "synced":
            continue
        try:
            start_t = slot_start[11:16] if len(slot_start) >= 16 else slot_start
            end_t = slot_end[11:16] if len(slot_end) >= 16 else slot_end
            busy.append((slot_start, slot_end, f"{s.get('member_name', 'Event')} ({start_t}–{end_t})"))
        except Exception:
            busy.append((slot_start, slot_end, s.get("member_name", "Event")))
    busy.sort(key=lambda x: x[0])
    if not busy:
        return f"{member_id.capitalize()} has no events on {date} — they're free all day."
    lines = [f"{member_id.capitalize()}'s schedule for {date}:"]
    for _, _, desc in busy:
        lines.append(f"• {desc}")
    requester_note = ""
    if req_lower and req_lower != mid_lower and not has_synced_calendar(team_id, req_lower):
        requester_note = " (Your calendar isn't in Team Brain — say 'sync my calendar' to add it.)"
    return "\n".join(lines) + requester_note


@mcp.tool(
    description="Check if a team member is free at a specific time. Use when user asks 'is Armaan free tomorrow at 2pm' or similar. member_id: 'aadit' or 'armaan'. date: YYYY-MM-DD. time: HH:MM or '2pm'. requester_id: who is asking. duration_minutes: default 60."
)
def check_member_free(
    team_id: str,
    member_id: str,
    date: str,
    time: str,
    requester_id: str = "",
    duration_minutes: int = 60,
) -> str:
    """Check if member has any calendar conflict. First verifies both calendars are synced in Team Brain."""
    if not get_team(team_id):
        return f"Team '{team_id}' not found."
    # Auto-check: is the member's calendar in Team Brain?
    mid_lower = member_id.lower()
    req_lower = requester_id.lower() if requester_id else ""
    if not has_synced_calendar(team_id, mid_lower):
        return f"{member_id.capitalize()}'s calendar isn't in Team Brain yet. Ask them to say 'sync my calendar' in Poke so we can check their availability."
    if req_lower and req_lower != mid_lower and not has_synced_calendar(team_id, req_lower):
        # Requester hasn't synced — add note but still check the member
        pass  # we'll add a note at the end if we can answer
    # Parse requested slot
    try:
        from datetime import datetime, timedelta
        # Normalize time: "2pm" -> "14:00", "2:30pm" -> "14:30"
        t = time.strip().lower().replace(" ", "")
        if "pm" in t:
            h = int(t.replace("pm", "").split(":")[0] or t.replace("pm", "").split(".")[0])
            if h < 12:
                h += 12
            m = int(t.split(":")[1]) if ":" in t else 0
        elif "am" in t:
            h = int(t.replace("am", "").split(":")[0] or t.replace("am", "").split(".")[0])
            if h == 12:
                h = 0
            m = int(t.split(":")[1]) if ":" in t else 0
        else:
            parts = t.replace(":", ".").split(".")
            h = int(parts[0]) if parts else 0
            m = int(parts[1]) if len(parts) > 1 else 0
        start_dt = datetime.fromisoformat(f"{date}T{h:02d}:{m:02d}:00")
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        req_start = start_dt.isoformat()
        req_end = end_dt.isoformat()
    except Exception as e:
        return f"Could not parse date/time: {date} {time}. Use YYYY-MM-DD and HH:MM or '2pm'. Error: {e}"
    # Get all slots that indicate member is busy: synced for this member, or team meetings
    slots = es_get_calendar_slots(team_id, slot_type=None)
    conflicts = []
    mid = member_id.lower()
    for s in slots:
        slot_type = s.get("type", "")
        slot_mid = (s.get("member_id") or "").lower()
        slot_start = s.get("start") or ""
        slot_end = s.get("end") or ""
        if not slot_start or not slot_end:
            continue
        # Member is busy if: (1) synced event for this member, or (2) team meeting (everyone attends)
        if slot_type == "synced" and slot_mid != mid:
            continue
        if slot_type == "meeting":
            pass  # team meeting - member attends
        elif slot_type != "synced":
            continue
        # Check overlap: (slot_start < req_end) and (slot_end > req_start)
        try:
            slot_s = datetime.fromisoformat(slot_start.replace("Z", "+00:00")[:26])
            slot_e = datetime.fromisoformat(slot_end.replace("Z", "+00:00")[:26])
            if slot_s.tzinfo:
                start_dt = start_dt.replace(tzinfo=slot_s.tzinfo) if not start_dt.tzinfo else start_dt
                end_dt = end_dt.replace(tzinfo=slot_s.tzinfo) if not end_dt.tzinfo else end_dt
            if slot_s < end_dt and slot_e > start_dt:
                conflicts.append(f"{s.get('member_name', 'Event')} ({slot_start[:16]} – {slot_end[11:16]})")
        except Exception:
            if slot_start < req_end and slot_end > req_start:
                conflicts.append(f"{s.get('member_name', 'Event')} ({slot_start[:16]} – {slot_end[11:16]})")
    requester_note = ""
    if req_lower and req_lower != mid_lower and not has_synced_calendar(team_id, req_lower):
        requester_note = " (Your calendar isn't in Team Brain yet — say 'sync my calendar' to add it.)"
    if not conflicts:
        return f"{member_id.capitalize()} is free at {date} {time}.{requester_note}"
    return f"{member_id.capitalize()} has a conflict: " + "; ".join(conflicts[:3]) + (" ..." if len(conflicts) > 3 else "") + requester_note


@mcp.tool(
    description="Delete a meeting from the team calendar. Pass the meeting title (e.g. 'Celebration for TreeHacks Win'). Optionally pass start and end if there are multiple meetings with same title."
)
def delete_meeting(
    team_id: str,
    title: str,
    start: str = "",
    end: str = "",
) -> str:
    """Remove a meeting from the team calendar."""
    if not get_team(team_id):
        return f"Team '{team_id}' not found."
    if remove_meeting(team_id, title, start, end):
        return f"Deleted meeting '{title}' from the calendar."
    return f"Meeting '{title}' not found. Use list_team_calendar to see current meetings."


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
    return {
        "name": "Team Brain",
        "description": "Shared AI assistant for teams — calendar, knowledge, shopping",
        "elasticsearch_enabled": True,
        "tools": [
            "set_availability",
            "find_availability",
            "book_meeting",
            "list_team_calendar",
            "sync_my_calendar",
            "get_member_availability",
            "check_member_free",
            "delete_meeting",
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

    es_status = "connected"
    print(f"Team Brain MCP server on http://{host}:{port}/mcp")
    print(f"Elasticsearch: {es_status}")
    print(f"Connect Poke:  poke tunnel http://localhost:{port}/mcp --name \"Team Brain\"")
    print()

    mcp.run(
        transport="http",
        host=host,
        port=port,
    )
