#!/usr/bin/env python3
"""
Session Helper — search, list, and extract conversations from Claude CLI and Codex.

Usage:
    python3 session_helper.py search <query>         # Search by ID or keyword
    python3 session_helper.py list [--hours N] [--platform claude|codex|all]
    python3 session_helper.py extract <session-id>   # Extract full conversation
    python3 session_helper.py extract <session-id> --tail N  # Last N messages only
    python3 session_helper.py info <session-id>      # Show session metadata only
"""

import json
import os
import sys
import glob
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

CLAUDE_DIR = os.path.expanduser("~/.claude/projects")
CODEX_INDEX = os.path.expanduser("~/.codex/session_index.jsonl")
CODEX_SESSIONS = os.path.expanduser("~/.codex/sessions")
CODEX_ARCHIVED = os.path.expanduser("~/.codex/archived_sessions")


def parse_timestamp(ts_str):
    """Parse ISO timestamp to datetime."""
    if not ts_str:
        return None
    try:
        ts_str = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(ts_str)
    except:
        return None


def find_claude_sessions():
    """Find all Claude CLI session files."""
    sessions = []
    if not os.path.isdir(CLAUDE_DIR):
        return sessions
    for project_dir in os.listdir(CLAUDE_DIR):
        project_path = os.path.join(CLAUDE_DIR, project_dir)
        if not os.path.isdir(project_path):
            continue
        for f in os.listdir(project_path):
            if f.endswith(".jsonl"):
                sid = f.replace(".jsonl", "")
                full_path = os.path.join(project_path, f)
                mtime = os.path.getmtime(full_path)
                sessions.append({
                    "id": sid,
                    "platform": "claude",
                    "path": full_path,
                    "project": project_dir,
                    "mtime": mtime,
                    "mtime_dt": datetime.fromtimestamp(mtime),
                })
    return sessions


def find_codex_sessions():
    """Find all Codex session files using index + filesystem."""
    sessions = []

    # Build index lookup
    index = {}
    if os.path.isfile(CODEX_INDEX):
        with open(CODEX_INDEX) as f:
            for line in f:
                try:
                    d = json.loads(line.strip())
                    index[d["id"]] = d
                except:
                    continue

    # Scan session directories
    for base_dir in [CODEX_SESSIONS, CODEX_ARCHIVED]:
        if not os.path.isdir(base_dir):
            continue
        for root, dirs, files in os.walk(base_dir):
            for f in files:
                if not f.endswith(".jsonl"):
                    continue
                full_path = os.path.join(root, f)
                # Extract ID from filename: rollout-<timestamp>-<id>.jsonl
                parts = f.replace(".jsonl", "").split("-")
                # The UUID is the last 5 parts joined by hyphens
                if len(parts) >= 6:
                    sid = "-".join(parts[-5:])
                else:
                    sid = f.replace(".jsonl", "")

                mtime = os.path.getmtime(full_path)
                meta = index.get(sid, {})
                sessions.append({
                    "id": sid,
                    "platform": "codex",
                    "path": full_path,
                    "thread_name": meta.get("thread_name", ""),
                    "updated_at": meta.get("updated_at", ""),
                    "mtime": mtime,
                    "mtime_dt": datetime.fromtimestamp(mtime),
                })

    # Also add sessions from index that weren't found in filesystem
    found_ids = {s["id"] for s in sessions}
    for sid, meta in index.items():
        if sid not in found_ids:
            sessions.append({
                "id": sid,
                "platform": "codex",
                "path": None,
                "thread_name": meta.get("thread_name", ""),
                "updated_at": meta.get("updated_at", ""),
                "mtime": 0,
                "mtime_dt": datetime.min,
            })

    return sessions


def get_claude_session_name(path, sid):
    """Get a display name for a Claude session from its first user message."""
    try:
        with open(path) as f:
            for line in f:
                try:
                    d = json.loads(line.strip())
                    if d.get("type") == "user":
                        content = d.get("message", {}).get("content", "")
                        if isinstance(content, list):
                            content = " ".join(
                                b.get("text", "")
                                for b in content
                                if isinstance(b, dict) and b.get("type") == "text"
                            )
                        # Filter out system/command messages
                        if content and not content.startswith("<") and len(content) > 3:
                            return content[:80]
                except:
                    continue
    except:
        pass
    return sid[:16]


def list_sessions(hours=24, platform="all"):
    """List recent sessions from specified platform(s)."""
    now = datetime.now()
    cutoff = now - timedelta(hours=hours)
    results = []

    if platform in ("all", "claude"):
        for s in find_claude_sessions():
            if s["mtime_dt"] >= cutoff:
                name = get_claude_session_name(s["path"], s["id"])
                results.append({
                    "id": s["id"],
                    "platform": "claude",
                    "name": name,
                    "project": s["project"],
                    "time": s["mtime_dt"].isoformat(),
                    "path": s["path"],
                })

    if platform in ("all", "codex"):
        for s in find_codex_sessions():
            if s["mtime_dt"] >= cutoff:
                results.append({
                    "id": s["id"],
                    "platform": "codex",
                    "name": s.get("thread_name", "") or "(unnamed)",
                    "project": "",
                    "time": s.get("updated_at") or s["mtime_dt"].isoformat(),
                    "path": s["path"],
                })

    # Sort by time descending
    results.sort(key=lambda x: x["time"], reverse=True)
    return results


def search_sessions(query):
    """Search sessions by ID prefix or keyword in name."""
    query_lower = query.lower()
    results = []

    for s in find_claude_sessions():
        name = get_claude_session_name(s["path"], s["id"])
        if query_lower in s["id"].lower() or query_lower in name.lower():
            results.append({
                "id": s["id"],
                "platform": "claude",
                "name": name,
                "project": s["project"],
                "time": s["mtime_dt"].isoformat(),
                "path": s["path"],
            })

    for s in find_codex_sessions():
        name = s.get("thread_name", "")
        if query_lower in s["id"].lower() or query_lower in name.lower():
            results.append({
                "id": s["id"],
                "platform": "codex",
                "name": name or "(unnamed)",
                "project": "",
                "time": s.get("updated_at") or s["mtime_dt"].isoformat(),
                "path": s["path"],
            })

    results.sort(key=lambda x: x["time"], reverse=True)
    return results


def find_session_file(session_id):
    """Find the JSONL file for a given session ID (supports partial match)."""
    sid_lower = session_id.lower()

    # Search Claude
    for s in find_claude_sessions():
        if s["id"].lower().startswith(sid_lower) or sid_lower in s["id"].lower():
            return s["path"], "claude", s

    # Search Codex
    for s in find_codex_sessions():
        if s["id"].lower().startswith(sid_lower) or sid_lower in s["id"].lower():
            return s["path"], "codex", s

    return None, None, None


def extract_claude(path, tail=None):
    """Extract messages from Claude CLI session JSONL."""
    messages = []
    try:
        with open(path) as f:
            for line in f:
                try:
                    d = json.loads(line.strip())
                    t = d.get("type")
                    if t == "user":
                        content = d.get("message", {}).get("content", "")
                        if isinstance(content, list):
                            content = " ".join(
                                b.get("text", "")
                                for b in content
                                if isinstance(b, dict) and b.get("type") == "text"
                            )
                        # Filter noise
                        if content and not content.startswith("<turn_aborted>") and not content.startswith("<local-command") and not content.startswith("<command-"):
                            messages.append({"role": "user", "content": content[:2000]})
                    elif t == "assistant":
                        blocks = d.get("message", {}).get("content", [])
                        texts = []
                        for b in blocks:
                            if isinstance(b, dict) and b.get("type") == "text":
                                texts.append(b.get("text", ""))
                        if texts:
                            messages.append({"role": "assistant", "content": "\n".join(texts)[:2000]})
                except:
                    continue
    except Exception as e:
        return {"error": str(e), "messages": []}

    if tail:
        messages = messages[-tail:]

    return {"messages": messages, "total": len(messages)}


def extract_codex(path, tail=None):
    """Extract messages from Codex session JSONL."""
    messages = []
    meta = {}
    try:
        with open(path) as f:
            for line in f:
                try:
                    d = json.loads(line.strip())
                    t = d.get("type")
                    payload = d.get("payload", {})

                    if t == "session_meta":
                        meta = {
                            "id": payload.get("id", ""),
                            "cwd": payload.get("cwd", ""),
                            "originator": payload.get("originator", ""),
                            "model": payload.get("model_provider", ""),
                            "created": d.get("timestamp", ""),
                        }
                    elif t == "response_item" and payload.get("type") == "message":
                        role = payload.get("role", "")
                        content_parts = payload.get("content", [])
                        texts = []
                        for c in content_parts:
                            if isinstance(c, dict):
                                if c.get("type") in ("input_text", "output_text", "text"):
                                    texts.append(c.get("text", ""))
                        if texts and role in ("user", "assistant"):
                            messages.append({"role": role, "content": "\n".join(texts)[:2000]})
                except:
                    continue
    except Exception as e:
        return {"error": str(e), "messages": [], "meta": {}}

    if tail:
        messages = messages[-tail:]

    return {"messages": messages, "meta": meta, "total": len(messages)}


def extract_session(session_id, tail=None):
    """Extract conversation from a session by ID."""
    path, platform, info = find_session_file(session_id)
    if not path:
        return {"error": f"Session not found: {session_id}", "suggestions": search_sessions(session_id)[:5]}

    if not os.path.isfile(path):
        return {"error": f"Session file not found: {path}"}

    if platform == "codex":
        result = extract_codex(path, tail)
    else:
        result = extract_claude(path, tail)

    result["platform"] = platform
    result["session_id"] = info["id"]
    result["path"] = path
    if platform == "claude":
        result["project"] = info.get("project", "")
        result["name"] = get_claude_session_name(path, info["id"])
    else:
        result["name"] = info.get("thread_name", "")
    return result


def session_info(session_id):
    """Get metadata about a session without extracting messages."""
    path, platform, info = find_session_file(session_id)
    if not path:
        return {"error": f"Session not found: {session_id}"}

    result = {
        "id": info["id"],
        "platform": platform,
        "path": path,
        "mtime": info["mtime_dt"].isoformat() if info["mtime_dt"] else None,
    }

    if platform == "claude":
        result["project"] = info.get("project", "")
        result["name"] = get_claude_session_name(path, info["id"])
        # Count messages quickly
        try:
            with open(path) as f:
                lines = f.readlines()
            result["file_lines"] = len(lines)
        except:
            pass
    else:
        result["thread_name"] = info.get("thread_name", "")
        result["updated_at"] = info.get("updated_at", "")

    return result


def main():
    parser = argparse.ArgumentParser(description="Session Helper for Claude CLI and Codex")
    sub = parser.add_subparsers(dest="command")

    # list
    list_p = sub.add_parser("list", help="List recent sessions")
    list_p.add_argument("--hours", type=int, default=24, help="Hours to look back (default: 24)")
    list_p.add_argument("--platform", choices=["all", "claude", "codex"], default="all")

    # search
    search_p = sub.add_parser("search", help="Search sessions by ID or keyword")
    search_p.add_argument("query", help="Search query (ID prefix or keyword)")

    # extract
    extract_p = sub.add_parser("extract", help="Extract conversation from a session")
    extract_p.add_argument("session_id", help="Session ID (full or prefix)")
    extract_p.add_argument("--tail", type=int, default=None, help="Only last N messages")

    # info
    info_p = sub.add_parser("info", help="Show session metadata")
    info_p.add_argument("session_id", help="Session ID (full or prefix)")

    args = parser.parse_args()

    if args.command == "list":
        result = list_sessions(args.hours, args.platform)
    elif args.command == "search":
        result = search_sessions(args.query)
    elif args.command == "extract":
        result = extract_session(args.session_id, args.tail)
    elif args.command == "info":
        result = session_info(args.session_id)
    else:
        parser.print_help()
        return

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
