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

**Option A: Tunnel (local dev)** — if you have the Poke CLI:

```bash
poke tunnel http://localhost:8000/mcp --name "Team Brain"
```

**Option B: Add remote URL** — no Poke CLI needed: run `ngrok http 8000`, then use `https://YOUR-NGROK-URL/mcp` in Poke settings.

1. Deploy to Render (see below) or expose via ngrok
2. Go to [poke.com/settings/connections](https://poke.com/settings/connections)
3. Create Integration → MCP Server URL: `https://your-url/mcp` → Name: "Team Brain"

### 3. Try it in Poke

Ask Poke things like:

- *"Use the Team Brain integration to store that our brand colors are #FF6B35 and #004E89"*
- *"Use Team Brain to add milk to the shopping list"*
- *"Use Team Brain to find when Alice and Bob are free next week"*

**Text-to-PR (Vercel / GitHub):** Register a repo once, then request changes via text. Poke will use Claude to edit the code and open a PR.

1. *"Use Team Brain to register my project: repo https://github.com/username/my-app, branch main, name my Vercel project"* → calls `register_project`
2. *"Use Team Brain to make changes on my Vercel project: make the header say Welcome and add a blue CTA button"* → calls `request_code_change`; you get back a PR link (and optional Vercel preview).

Requires on the server: `GITHUB_TOKEN` (repo push + create PR), `ANTHROPIC_API_KEY` (Claude for code edits). Optional: `CLAUDE_CODING_MODEL` (default `claude-sonnet-4-5`).

## Tools (14 total)

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
| `register_project` | Register a GitHub repo for “text-to-PR” (Vercel project) |
| `list_projects_tool` | List registered projects for the team |
| `request_code_change` | Request code changes on a registered project → agent makes edits and opens a PR |
| `get_team_brain_info` | Server info |

Use `team_id` (default: `"default"`) to scope to a team. Each teammate adds the same MCP server; the server stores data per team.

### Calendar sync flow

1. **Add API keys** — Create `poke_api_keys.txt` in the project root with your and teammates' Poke API keys (one per line):
   ```
   me:pk_your_key
   friend:pk_their_key
   ```
   Get keys at [poke.com/kitchen/api-keys](https://poke.com/kitchen/api-keys)

2. **You text Cortex** (e.g. via SMS): *"Book 7pm for tonight"* or *"Make a calendar invite for today at 7pm"*
3. **Poke** calls `book_meeting` → event stored in Team Brain
4. **All keys in the file** receive the invite in their Poke → adds to their calendar (Poke calendar sync)
5. **Anyone** can ask *"What's on the team calendar?"* → sees all meetings

## Deploy to Render

1. Push to GitHub
2. Connect repo to Render
3. New Web Service → Render will use `render.yaml`
4. Your MCP URL: `https://team-brain-mcp.onrender.com/mcp`

## Frontend (Next.js)

The dashboard displays calendar, knowledge, and shopping data from the API (Elasticsearch when configured):

```bash
# Terminal 1: MCP server (for Poke)
python src/server.py

# Terminal 2: REST API (for frontend) — run from project root so .env loads
python run_api.py

# Terminal 3: Frontend
cd frontend && npm install && npm run dev
```

- MCP (Poke): http://localhost:8000/mcp
- REST API: http://localhost:8001/api/...
- Frontend: http://localhost:3000

Set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` to override the API URL (e.g. when deployed).

## Elasticsearch + JINA (Optional)

For persistent storage and semantic knowledge search:

1. **Elastic Cloud** — Create a deployment at [cloud.elastic.co](https://cloud.elastic.co)
2. **Env vars:**
   - `ELASTIC_CLOUD_ID` + `ELASTIC_API_KEY` (from Elastic Cloud)
   - Or `ELASTIC_URL` (e.g. `http://localhost:9200`) + `ELASTIC_API_KEY` for self-hosted
   - `JINA_API_KEY` — from [jina.ai](https://jina.ai) for embeddings
3. **Knowledge base** — `store_knowledge` and `query_knowledge` use JINA v3 embeddings for semantic search (finds by meaning, not just keywords)

The `elastic/` folder contains a workflow template for Elastic Agent Builder integration.

## Sponsor Tracks

- **Poke / Interaction Co.** — MCP server, Poke-native, team coordination
- **Elastic** — JINA v3 embeddings, semantic search, Elastic Cloud, Agent Builder workflows
- **Decagon** — Multi-turn conversational agent
- **Anthropic** — Reduces calendar anxiety; tool-using agent
- **Greylock** — Multi-turn agent; chains tools
- **Visa** — Shopping automation; shared lists
- **Graphite** — Real product; team calendar + shared brain
