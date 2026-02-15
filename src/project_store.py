"""
Store for Vercel/GitHub projects per team. Used by request_code_change MCP tool.
Uses Elasticsearch if available, else JSON file in data/projects.json.
"""

import json
import os
from typing import Optional

from elastic_store import _es_client, _ensure_indices, _log

IDX_PROJECTS = "team_brain_projects"

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
_PROJECTS_FILE = os.path.join(_DATA_DIR, "projects.json")


def _file_load() -> dict:
    """Load projects from JSON file. Keys: team_id -> list of project dicts."""
    if not os.path.exists(_PROJECTS_FILE):
        return {}
    try:
        with open(_PROJECTS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _file_save(data: dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_PROJECTS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _use_elastic() -> bool:
    return _es_client() is not None


def register_project(
    team_id: str,
    repo_url: str,
    default_branch: str = "main",
    name: Optional[str] = None,
) -> str:
    """Register a project for this team. Returns project_id or name to use in request_code_change."""
    # Normalize repo URL to https form
    repo_url = repo_url.strip()
    if repo_url.startswith("git@github.com:"):
        repo_url = "https://github.com/" + repo_url.replace("git@github.com:", "").replace(".git", "")
    if not repo_url.endswith(".git") and "/github.com/" in repo_url:
        pass
    else:
        repo_url = repo_url.replace(".git", "")

    # project_id: slug from repo (owner/repo)
    if "github.com/" in repo_url:
        project_id = repo_url.split("github.com/")[-1].strip("/").replace(".git", "")
    else:
        project_id = repo_url.replace("https://", "").replace("http://", "").strip("/").replace("/", "_")
    display_name = name or project_id

    if _use_elastic():
        es = _es_client()
        _ensure_indices(es)
        if not es.indices.exists(index=IDX_PROJECTS):
            es.indices.create(
                index=IDX_PROJECTS,
                body={
                    "mappings": {
                        "properties": {
                            "team_id": {"type": "keyword"},
                            "project_id": {"type": "keyword"},
                            "repo_url": {"type": "keyword"},
                            "default_branch": {"type": "keyword"},
                            "name": {"type": "text"},
                        }
                    }
                },
            )
        # Upsert by team_id + project_id
        doc = {
            "team_id": team_id,
            "project_id": project_id,
            "repo_url": repo_url,
            "default_branch": default_branch,
            "name": display_name,
        }
        es.index(index=IDX_PROJECTS, id=f"{team_id}:{project_id}", document=doc)
        _log("INDEX", IDX_PROJECTS, 1, f"team_id={team_id} project_id={project_id}")
        return f"Registered project '{display_name}' ({project_id}). Use request_code_change with project_name='{display_name}' or project_id='{project_id}'."
    else:
        data = _file_load()
        if team_id not in data:
            data[team_id] = []
        projects = data[team_id]
        existing = next((p for p in projects if p.get("project_id") == project_id), None)
        entry = {
            "project_id": project_id,
            "repo_url": repo_url,
            "default_branch": default_branch,
            "name": display_name,
        }
        if existing:
            idx = projects.index(existing)
            projects[idx] = entry
        else:
            projects.append(entry)
        _file_save(data)
        return f"Registered project '{display_name}' ({project_id}). Use request_code_change with project_name='{display_name}' or project_id='{project_id}'."


def get_project(team_id: str, project_name_or_id: str) -> Optional[dict]:
    """Get project by team_id and name or project_id."""
    key = (project_name_or_id or "").strip().lower()

    if _use_elastic():
        es = _es_client()
        if not es or not es.indices.exists(index=IDX_PROJECTS):
            return None
        r = es.search(
            index=IDX_PROJECTS,
            query={"term": {"team_id": team_id}},
            size=50,
        )
        hits = r.get("hits", {}).get("hits", [])
        for h in hits:
            src = h["_source"]
            pid = (src.get("project_id") or "").lower()
            n = (src.get("name") or "").lower()
            if pid == key or n == key:
                return src
        return None
    else:
        data = _file_load()
        projects = data.get(team_id, [])
        for p in projects:
            if (p.get("project_id") or "").lower() == key or (p.get("name") or "").lower() == key:
                return p
        return None


def list_projects(team_id: str) -> list[dict]:
    """List all projects for a team."""
    if _use_elastic():
        es = _es_client()
        if not es or not es.indices.exists(index=IDX_PROJECTS):
            return []
        r = es.search(index=IDX_PROJECTS, query={"term": {"team_id": team_id}}, size=50)
        return [h["_source"] for h in r.get("hits", {}).get("hits", [])]
    else:
        return _file_load().get(team_id, [])
