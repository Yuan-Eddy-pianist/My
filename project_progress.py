"""Select unreported Git commits and maintain the displayed progress history."""

from __future__ import annotations

import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


DATED_ENTRY = re.compile(r"^(\d{4}-\d{2}-\d{2})[：:]\s*(.*)$")


def git(path: str, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", path, *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.rstrip("\r\n")


def inspect_project(project: dict, checkpoint: dict, checked_at: str) -> dict | None:
    path = str(Path(project.get("path") or "").expanduser().resolve())
    if not project.get("path") or not Path(path).is_dir():
        return None
    try:
        head = git(path, "rev-parse", "--verify", "HEAD")
    except subprocess.CalledProcessError:
        return None  # Missing repository or a repository with no commits yet.

    if checkpoint.get("path") != path:
        checkpoint = {}
    previous = checkpoint.get("head")
    revisions = [head]
    if previous:
        # Commit identities also catch evening work and multiple runs in one day.
        revisions = [f"{previous}..{head}"]
    else:
        dates = [
            match[1]
            for line in project.get("progress", "").splitlines()
            if (match := DATED_ENTRY.match(line))
        ]
        # Legacy entries have only a date. Include that whole day on the first
        # inspection; subsequent inspections use the saved commit, never dates.
        since = (
            max(dates) + " 00:00:00"
            if dates
            else (datetime.fromisoformat(checked_at) - timedelta(days=7)).isoformat()
        )
        revisions.append(f"--since-as-filter={since}")

    raw = git(path, "log", "--reverse", "--topo-order", "--format=%H%x1f%s%x1f%b%x1e", *revisions)
    commits = []
    for record in raw.split("\x1e"):
        if not record.strip():
            continue
        commit, subject, body = record.strip("\r\n").split("\x1f", 2)
        commits.append({"hash": commit, "subject": subject, "body": body.strip()})

    # A change and its standard Git revert in this batch have no net progress.
    hashes = {commit["hash"] for commit in commits}
    cancelled = set()
    for commit in reversed(commits):
        if commit["hash"] in cancelled:
            continue
        revert = re.search(r"^This reverts commit ([0-9a-f]+)\.", commit["body"], re.MULTILINE)
        if revert and revert[1] in hashes:
            cancelled.update((commit["hash"], revert[1]))

    return {
        "id": project["id"],
        "title": project.get("title", project["id"]),
        "path": path,
        "head": head,
        "commits": [commit for commit in commits if commit["hash"] not in cancelled],
        "dirty": bool(git(path, "status", "--porcelain")),
    }


def clean_progress(progress: str) -> str:
    """Keep the newest copy of each dated description, including legacy repeats."""
    dated = []
    undated = []
    for line in progress.splitlines():
        match = DATED_ENTRY.match(line)
        if match:
            dated.append((match[1], match[2].strip()))
        elif line.strip():
            undated.append(line)
    if not dated:
        return progress
    seen = set()
    result = []
    for day, body in sorted(dated, key=lambda entry: entry[0], reverse=True):
        key = body.rstrip("。.")
        if key and key not in seen:
            seen.add(key)
            result.append(f"{day}：{body}")
    return "\n".join(result[:7] + undated)


def add_progress(progress: str, day: str, summary: str) -> str:
    summary = " ".join(summary.split())
    return clean_progress(f"{day}：{summary}\n{progress}")
