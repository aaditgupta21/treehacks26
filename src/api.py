"""
REST API for Team Brain — Flask app serving Elasticsearch-backed data.
Run: python run_api.py  (from project root)
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path
from dotenv import load_dotenv

# Load .env before any store/elastic imports
for p in [Path(__file__).resolve().parent.parent / ".env", Path.cwd() / ".env"]:
    if p.exists():
        load_dotenv(p)
        break
else:
    load_dotenv()

from flask import Flask, request, jsonify
from flask_cors import CORS

from store import (
    get_team,
    get_or_create_team,
    search_knowledge,
    add_knowledge,
    add_shopping_item,
    get_shopping_list as store_get_shopping_list,
    remove_shopping_item,
    remove_meeting,
)
from elastic_store import get_calendar_slots

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

DEFAULT_TEAM = "default"


def _parse_attendees(summary: str) -> list:
    if not summary:
        return []
    m = re.search(r"Booked:\s*(.+)", summary, re.I)
    if not m:
        return []
    return [s.strip() for s in m.group(1).split(",") if s.strip()]


@app.route("/api/health")
def health():
    # Debug: try to fetch shopping count
    try:
        items = store_get_shopping_list(DEFAULT_TEAM)
        return jsonify({"ok": True, "elasticsearch": True, "shopping_count": len(items)})
    except Exception as ex:
        return jsonify({"ok": True, "elasticsearch": True, "error": str(ex)})


@app.route("/api/meetings")
def get_meetings():
    team_id = request.args.get("team_id", DEFAULT_TEAM)
    get_or_create_team(team_id)
    slots = get_calendar_slots(team_id, slot_type="meeting")
    meetings = [
        {"title": s["member_name"], "start": s["start"], "end": s["end"], "attendees": _parse_attendees(s.get("summary", ""))}
        for s in slots
    ]
    return jsonify({"meetings": meetings})


@app.route("/api/meetings", methods=["DELETE"])
def delete_meeting():
    team_id = request.args.get("team_id", DEFAULT_TEAM)
    title = request.args.get("title", "")
    start = request.args.get("start", "")
    end = request.args.get("end", "")
    if not title:
        return jsonify({"detail": "title required"}), 400
    if remove_meeting(team_id, title, start, end):
        return jsonify({"ok": True, "removed": title})
    return jsonify({"detail": f"Meeting '{title}' not found"}), 404


@app.route("/api/knowledge")
def get_knowledge():
    team_id = request.args.get("team_id", DEFAULT_TEAM)
    q = request.args.get("q", "")
    category = request.args.get("category", "")
    if not get_team(team_id):
        get_or_create_team(team_id)
    entries = search_knowledge(team_id, query=q, category=category)
    return jsonify({
        "knowledge": [
            {"key": e["key"], "value": e["value"], "category": e["category"], "created_at": e.get("created_at", "")}
            for e in entries
        ]
    })


@app.route("/api/knowledge", methods=["POST"])
def post_knowledge():
    team_id = request.args.get("team_id", DEFAULT_TEAM)
    key = request.args.get("key", "")
    value = request.args.get("value", "")
    category = request.args.get("category", "fact")
    if not key or not value:
        return jsonify({"detail": "key and value required"}), 400
    get_or_create_team(team_id)
    add_knowledge(team_id, key, value, category)
    return jsonify({"ok": True, "key": key})


@app.route("/api/shopping")
def get_shopping():
    team_id = request.args.get("team_id", DEFAULT_TEAM)
    filter_item = request.args.get("filter_item", "")
    items = store_get_shopping_list(team_id, filter_item)
    return jsonify({
        "shoppingList": [
            {
                "name": i["name"],
                "quantity": int(i["quantity"]) if str(i.get("quantity", "1")).isdigit() else 1,
                "added_by": i.get("added_by", "unknown"),
                "created_at": i.get("created_at", ""),
            }
            for i in items
        ]
    })


@app.route("/api/shopping", methods=["POST"])
def post_shopping():
    team_id = request.args.get("team_id", DEFAULT_TEAM)
    item = request.args.get("item", "")
    quantity = request.args.get("quantity", "1")
    added_by = request.args.get("added_by", "unknown")
    if not item:
        return jsonify({"detail": "item required"}), 400
    get_or_create_team(team_id)
    add_shopping_item(team_id, item, quantity, added_by)
    return jsonify({"ok": True, "item": item})


@app.route("/api/shopping", methods=["DELETE"])
def delete_shopping():
    team_id = request.args.get("team_id", DEFAULT_TEAM)
    item = request.args.get("item", "")
    if not item:
        return jsonify({"detail": "item required"}), 400
    if remove_shopping_item(team_id, item):
        return jsonify({"ok": True, "removed": item})
    return jsonify({"detail": f"Item '{item}' not found"}), 404
