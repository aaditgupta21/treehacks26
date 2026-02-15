# Team Brain MCP Server

Multiplayer Poke — a shared AI assistant for teams. Connect this MCP server to Poke for:

- **Calendar tetris** — Find 30-min windows when the whole dev team is free
- **Shared knowledge** — "Remember: our brand colors are #FF6B35 and #004E89"
- **Meeting booking** — Book slots and relay to team members
- **Shopping lists** — Team shopping lists (Visa commerce track)

## Quick Start

### 1. Install & run locally

```bash
python -m venv venv
source venv/bin/activate   # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
python src/server.py
```

Server runs at `http://localhost:8000/mcp`

### 2. Connect to Poke

**Option A: Tunnel (local dev)**

```bash
poke tunnel http://localhost:8000/mcp --name "Team Brain"
```

**Option B: Add remote URL**

1. Deploy to Render (see below) or expose via ngrok
2. Go to [poke.com/settings/connections](https://poke.com/settings/connections)
3. Create Integration → MCP Server URL: `https://your-url/mcp` → Name: "Team Brain"

### 3. Try it in Poke

Ask Poke things like:

- *"Use the Team Brain integration to store that our brand colors are #FF6B35 and #004E89"*
- *"Use Team Brain to add milk to the shopping list"*
- *"Use Team Brain to find when Alice and Bob are free next week"*

## Tools (11 total)

| Tool | Description |
|------|-------------|
| `set_availability` | Record when a team member is free |
| `find_availability` | Find overlapping free slots for team |
| `book_meeting` | Book a meeting — stores internally and pushes to teammates' Pokes |
| `list_team_calendar` | List all booked meetings (shared team calendar) |
| `register_for_calendar_sync` | Register your Poke webhook/API key to receive calendar invites |
| `store_knowledge` | Store team facts (brand, policy, etc.) |
| `query_knowledge` | Search team knowledge |
| `add_to_shopping_list` | Add item to shared list |
| `get_shopping_list` | Get shopping list |
| `remove_from_shopping_list` | Remove item |
| `get_team_brain_info` | Server info |

Use `team_id` (default: `"default"`) to scope to a team. Each teammate adds the same MCP server; the server stores data per team.

### Calendar sync flow

1. **You text Cortex** (e.g. via SMS): *"Make a calendar invite for today at 7pm"*
2. **Poke** calls `book_meeting` → event stored in Team Brain
3. **Teammates** who registered via `register_for_calendar_sync` receive the invite in their Poke
4. **Anyone** can ask *"What's on the team calendar?"* → Poke calls `list_team_calendar` → sees all meetings

**To receive pushes:** Register at poke.com/kitchen (create webhook) or get your API key from poke.com/kitchen/api-keys, then use `register_for_calendar_sync` with your team.

## Deploy to Render

1. Push to GitHub
2. Connect repo to Render
3. New Web Service → Render will use `render.yaml`
4. Your MCP URL: `https://team-brain-mcp.onrender.com/mcp`

## Sponsor Tracks

- **Poke / Interaction Co.** — MCP server, Poke-native, team coordination
- **Decagon** — Multi-turn conversational agent
- **Anthropic** — Reduces calendar anxiety; tool-using agent
- **Greylock** — Multi-turn agent; chains tools
- **Visa** — Shopping automation; shared lists
- **Graphite** — Real product; team calendar + shared brain
