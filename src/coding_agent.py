"""
Coding agent: clone repo, run Claude with file/git tools, push branch, create PR.
Used by the request_code_change MCP tool.
"""

import os
import subprocess
import tempfile
import re
from typing import Any, Optional

import httpx

# Optional: use anthropic if available
try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


def _clone_repo(repo_url: str, default_branch: str, work_dir: str, github_token: Optional[str]) -> bool:
    """Clone repo into work_dir. Uses token in URL if provided for private repos."""
    url = repo_url.replace("https://github.com/", "https://github.com/").strip()
    if not url.endswith(".git"):
        url = url + ".git"
    if github_token and "github.com" in url:
        # Insert token for auth
        url = url.replace("https://github.com/", f"https://x-access-token:{github_token}@github.com/")
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", "-b", default_branch, url, work_dir],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"[coding_agent] clone failed: {e.stderr}", flush=True)
        return False
    except Exception as e:
        print(f"[coding_agent] clone error: {e}", flush=True)
        return False


def _run_tool(work_dir: str, name: str, args: dict) -> str:
    """Execute a single tool in the repo workspace."""
    if name == "list_dir":
        path = args.get("path", ".")
        full = os.path.join(work_dir, path.lstrip("/"))
        if not os.path.abspath(full).startswith(os.path.abspath(work_dir)):
            return "Error: path outside repo"
        if not os.path.isdir(full):
            return f"Not a directory: {path}"
        try:
            entries = os.listdir(full)
            return "\n".join(entries) if entries else "(empty)"
        except Exception as e:
            return str(e)

    if name == "read_file":
        path = args.get("path", "")
        full = os.path.join(work_dir, path.lstrip("/"))
        if not os.path.abspath(full).startswith(os.path.abspath(work_dir)):
            return "Error: path outside repo"
        try:
            with open(full, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except FileNotFoundError:
            return f"File not found: {path}"
        except Exception as e:
            return str(e)

    if name == "write_file":
        path = args.get("path", "")
        content = args.get("content", "")
        full = os.path.join(work_dir, path.lstrip("/"))
        if not os.path.abspath(full).startswith(os.path.abspath(work_dir)):
            return "Error: path outside repo"
        try:
            os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
            with open(full, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Wrote {path}"
        except Exception as e:
            return str(e)

    if name == "run_command":
        cmd = args.get("command", "")
        if not cmd:
            return "Error: command required"
        # Restrict to a few allowed commands for safety (git, npm, npx, ls, cat, node)
        raw = cmd.strip()
        allowed = ("git ", "npm ", "npx ", "ls ", "cat ", "node ")
        if not any(raw.startswith(p) for p in allowed):
            return "Error: only git, npm, npx, ls, cat, node commands allowed"
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )
            out = (result.stdout or "").strip() or (result.stderr or "").strip()
            if result.returncode != 0:
                out = f"[exit {result.returncode}]\n{out}"
            return out or "(no output)"
        except subprocess.TimeoutExpired:
            return "Error: command timed out"
        except Exception as e:
            return str(e)

    return f"Unknown tool: {name}"


def _create_pr(owner: str, repo: str, head: str, base: str, title: str, body: str, github_token: str) -> Optional[str]:
    """Create a pull request. Returns PR URL or None."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {"title": title, "head": head, "base": base, "body": body or title}
    try:
        with httpx.Client(timeout=30) as client:
            r = client.post(url, json=payload, headers=headers)
            if r.status_code != 201:
                return None
            data = r.json()
            return data.get("html_url")
    except Exception:
        return None


def run_code_change(
    repo_url: str,
    default_branch: str,
    instruction: str,
    github_token: Optional[str] = None,
    anthropic_api_key: Optional[str] = None,
) -> dict:
    """
    Clone repo, run Claude to apply instruction, push branch, create PR.
    Returns {"ok": bool, "pr_url": str | None, "message": str, "preview_url": str | None}.
    """
    api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not HAS_ANTHROPIC or not api_key:
        return {
            "ok": False,
            "pr_url": None,
            "message": "Coding agent requires anthropic package and ANTHROPIC_API_KEY.",
            "preview_url": None,
        }
    token = github_token or os.environ.get("GITHUB_TOKEN")
    if not token:
        return {
            "ok": False,
            "pr_url": None,
            "message": "GITHUB_TOKEN is required to push and create PR. Set it in env or pass github_token.",
            "preview_url": None,
        }

    # Parse owner/repo from URL
    match = re.search(r"github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?$", repo_url)
    if not match:
        return {"ok": False, "pr_url": None, "message": "Repo URL must be a GitHub URL (e.g. https://github.com/owner/repo).", "preview_url": None}
    owner, repo = match.group(1), match.group(2).replace(".git", "")

    print(f"[coding_agent] Starting: repo={owner}/{repo} branch={default_branch} instruction={instruction[:80]}{'...' if len(instruction) > 80 else ''}", flush=True)

    with tempfile.TemporaryDirectory(prefix="team_brain_code_") as tmp:
        work_dir = os.path.join(tmp, "repo")
        print(f"[coding_agent] Cloning {repo_url} ...", flush=True)
        if not _clone_repo(repo_url, default_branch, work_dir, token):
            return {"ok": False, "pr_url": None, "message": "Failed to clone repo. Check repo_url and GITHUB_TOKEN.", "preview_url": None}
        print(f"[coding_agent] Clone OK. Starting Claude agent.", flush=True)

        branch_name = f"team-brain-{os.urandom(4).hex()}"
        client = Anthropic(api_key=api_key)

        tools = [
            {
                "name": "list_dir",
                "description": "List files in a directory in the repo. path is relative to repo root.",
                "input_schema": {
                    "type": "object",
                    "properties": {"path": {"type": "string", "description": "Path relative to repo root, e.g. . or src"}},
                    "required": ["path"],
                },
            },
            {
                "name": "read_file",
                "description": "Read contents of a file. path is relative to repo root.",
                "input_schema": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            },
            {
                "name": "write_file",
                "description": "Write or overwrite a file. path relative to repo root.",
                "input_schema": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                    "required": ["path", "content"],
                },
            },
            {
                "name": "run_command",
                "description": "Run a shell command in the repo (git, npm, npx, ls, cat, node only).",
                "input_schema": {
                    "type": "object",
                    "properties": {"command": {"type": "string"}},
                    "required": ["command"],
                },
            },
        ]

        system = f"""You are a coding agent. The user wants you to make changes to their codebase.

Instruction from the user: {instruction}

Repo is cloned at the workspace root. Use list_dir to explore, read_file to read, write_file to edit, run_command to run git/npm etc.

When you are done making the changes:
1. Create a new branch: run_command with "git checkout -b {branch_name}"
2. Stage and commit: run_command with "git add -A" then "git config user.email 'agent@team-brain.local'; git config user.name 'Team Brain'; git commit -m 'Your short commit message'"
3. Push: run_command with "git push -u origin {branch_name}"

After pushing, reply in your final message with exactly this line so the system can create the PR:
PR_TITLE: Your PR title
PR_BODY: Optional description

Do not make up files that don't exist. Prefer editing existing files. Keep changes minimal and focused."""

        messages: list[dict[str, Any]] = [
            {"role": "user", "content": f"Apply this change to the repo: {instruction}\n\nStart by listing the repo root with list_dir to see the structure."}
        ]
        max_steps = 25
        pr_title = "Updates from Team Brain"
        pr_body = instruction

        for step in range(max_steps):
            print(f"[coding_agent] Step {step + 1}/{max_steps}: calling Claude ...", flush=True)
            response = client.messages.create(
                model=os.environ.get("CLAUDE_CODING_MODEL", "claude-sonnet-4-5"),
                max_tokens=4096,
                system=system,
                messages=messages,
                tools=tools,
            )
            print(f"[coding_agent] Step {step + 1}: stop_reason={response.stop_reason}", flush=True)

            if response.stop_reason == "end_turn":
                # Parse final text for PR_TITLE/PR_BODY
                for block in response.content:
                    if block.type == "text":
                        text = block.text
                        for line in text.split("\n"):
                            if line.strip().startswith("PR_TITLE:"):
                                pr_title = line.replace("PR_TITLE:", "").strip() or pr_title
                            if line.strip().startswith("PR_BODY:"):
                                pr_body = line.replace("PR_BODY:", "").strip() or pr_body
                print(f"[coding_agent] Claude finished (end_turn). PR title: {pr_title}", flush=True)
                break

            if response.stop_reason != "tool_use":
                print(f"[coding_agent] Stopping: stop_reason={response.stop_reason}", flush=True)
                break

            # Append assistant content and run tools
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                tool_id = block.id
                tool_name = block.name
                tool_args = block.input
                # Log tool call (truncate file content for readability)
                if tool_name == "read_file":
                    print(f"[coding_agent]   tool: {tool_name} path={tool_args.get('path', '')}", flush=True)
                elif tool_name == "write_file":
                    path = tool_args.get("path", "")
                    content_len = len(tool_args.get("content", ""))
                    print(f"[coding_agent]   tool: {tool_name} path={path} content_len={content_len}", flush=True)
                elif tool_name == "run_command":
                    cmd = (tool_args.get("command", "") or "")[:60]
                    print(f"[coding_agent]   tool: {tool_name} command={cmd}{'...' if len(tool_args.get('command', '')) > 60 else ''}", flush=True)
                else:
                    print(f"[coding_agent]   tool: {tool_name} {tool_args}", flush=True)
                result = _run_tool(work_dir, tool_name, tool_args)
                result_preview = result[:100] + "..." if len(result) > 100 else result
                print(f"[coding_agent]   result: {result_preview}", flush=True)
                tool_results.append({"type": "tool_result", "tool_use_id": tool_id, "content": result})

            if not tool_results:
                break
            messages.append({"role": "user", "content": tool_results})

        # Push branch and create PR (we already told the agent to push; if it didn't, try ourselves)
        print(f"[coding_agent] Git: checkout -b {branch_name}, add, commit, push ...", flush=True)
        try:
            subprocess.run(["git", "checkout", "-b", branch_name], cwd=work_dir, check=True, capture_output=True, timeout=10)
        except subprocess.CalledProcessError:
            pass  # branch might exist
        try:
            subprocess.run(["git", "add", "-A"], cwd=work_dir, check=True, capture_output=True, timeout=10)
            subprocess.run(
                ["git", "config", "user.email", "agent@team-brain.local"],
                cwd=work_dir,
                check=True,
                capture_output=True,
                timeout=5,
            )
            subprocess.run(
                ["git", "config", "user.name", "Team Brain"],
                cwd=work_dir,
                check=True,
                capture_output=True,
                timeout=5,
            )
            subprocess.run(
                ["git", "commit", "-m", pr_title],
                cwd=work_dir,
                capture_output=True,
                timeout=10,
            )  # may fail if nothing to commit
        except subprocess.CalledProcessError:
            pass

        # Push to origin (clone URL already had token). Agent may have pushed already.
        try:
            subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.CalledProcessError as e:
            err = (e.stderr or e.stdout or str(e)) or ""
            if "already exists" in err or "rejected" in err:
                print(f"[coding_agent] Push (branch may already exist), creating PR ...", flush=True)
                pass  # Agent may have pushed; still try to create PR
            else:
                print(f"[coding_agent] Push failed: {err[:200]}", flush=True)
                return {
                    "ok": False,
                    "pr_url": None,
                    "message": f"Push failed: {err}",
                    "preview_url": None,
                }
        else:
            print(f"[coding_agent] Push OK. Creating PR ...", flush=True)

        pr_url = _create_pr(owner, repo, branch_name, default_branch, pr_title, pr_body, token)
        if pr_url:
            print(f"[coding_agent] PR created: {pr_url}", flush=True)
            preview_url = f"https://vercel.com/teams/.../preview"  # Optional: could resolve from Vercel API
            return {"ok": True, "pr_url": pr_url, "message": f"PR created: {pr_url}", "preview_url": None}
        print(f"[coding_agent] PR creation failed.", flush=True)
        return {"ok": False, "pr_url": None, "message": "PR creation failed. Check GitHub token permissions.", "preview_url": None}
