#!/usr/bin/env python3
"""Snapshot/reconcile dashboard records for migration; NEVER alter either store.

Usage: prepare-dashboard-migration.py --my-root /path/to/My --output /new/private/directory
The output is a private preparation bundle, not a new editable source of truth.
A later migration must recheck every source_hashes entry before any commit.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def same_directory(left, right):
    try:
        return os.path.samefile(left, right)
    except (FileNotFoundError, OSError):
        return Path(left).resolve() == Path(right).resolve()


def reconcile(workspace, registry, home):
    """Link by actual directory identity; never guess aliases or register projects."""
    if not isinstance(workspace, dict):
        raise ValueError('Workspace is not an object')
    for kind in ('projects', 'tasks', 'reminders'):
        items = workspace.get(kind)
        if not isinstance(items, list):
            raise ValueError(f'Missing {kind} array')
        ids = [x.get('id') if isinstance(x, dict) else None for x in items]
        if any(not isinstance(x, str) or not x for x in ids) or len(set(ids)) != len(ids):
            raise ValueError(f'Invalid or duplicate {kind} identities; preserve and inspect before migration')
    entries = []
    for line in registry.splitlines():
        if not line.startswith('- '):
            continue
        match = re.fullmatch(r'- ([^\s]+)(?: \[([^\]]+)\])? - (.+)', line)
        if not match:
            raise ValueError('Unrecognized project registry line; do not infer a project mapping')
        name, posture, description = match.groups()
        if any(e['name'] == name for e in entries):
            raise ValueError('Duplicate Firstmate project name')
        entries.append({'name': name, 'posture': posture, 'description': description,
                        'path': str((home / 'projects' / name).resolve())})
    links = {}
    unmatched = []
    for project in workspace['projects']:
        path = project.get('path')
        if not isinstance(path, str) or not Path(path).is_absolute():
            raise ValueError('A dashboard project has no absolute path; inspect without discarding it')
        matches = [e['name'] for e in entries if same_directory(path, home / 'projects' / e['name'])]
        if len(matches) > 1:
            raise ValueError('Multiple registry entries refer to the same dashboard project')
        if matches:
            if matches[0] in links.values():
                raise ValueError('Multiple dashboard records refer to one registry project; resolve explicitly')
            links[project['id']] = matches[0]
        else:
            unmatched.append(project['id'])
    return {'project_links': links, 'unmatched_dashboard_project_ids': unmatched,
            'firstmate_only_projects': [e['name'] for e in entries if e['name'] not in links.values()],
            'registry_entries': entries}


def prepare(my_root, output):
    root = Path(my_root).resolve()
    output = Path(output).absolute()
    home = root / 'agent-workflow/firstmate'
    required = [root / 'data/todos.json', home / 'data/projects.md', home / 'data/captain.md']
    optional = [home / 'data/captain-shared.md', home / 'data/learnings.md',
                home / '.pi/APPEND_SYSTEM.md', home / '.pi/settings.json']
    snapshots = {}
    for path in required + optional:
        if path.exists():
            snapshots[path] = path.read_bytes()
        elif path in required:
            raise ValueError(f'Required source missing: {path}')
        else:
            snapshots[path] = None
    workspace = json.loads(snapshots[required[0]])
    mapping = reconcile(workspace, snapshots[required[1]].decode(), home)
    manifest = {'status': 'prepared_only_no_records_migrated', 'my_root': str(root),
                'firstmate_home': str(home), 'counts': {k: len(workspace[k]) for k in ('projects','tasks','reminders')},
                **mapping, 'source_hashes': {str(p): digest(raw) if raw is not None else None for p,raw in snapshots.items()},
                'record_hashes': {kind: {item['id']: digest(json.dumps(item,ensure_ascii=False,sort_keys=True).encode())
                                        for item in workspace[kind]} for kind in ('projects','tasks','reminders')},
                'normal_firstmate_context': ['data/projects.md','data/captain.md','data/captain-shared.md','data/learnings.md'],
                'personal_agenda_owner': 'not_selected',
                'safety': 'No source removal, registry change, worker dispatch, session mutation, or bridge retirement performed.'}
    if output.exists():
        raise ValueError('Output already exists; preparation never overwrites a prior bundle')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.migration-stage-',dir=output.parent) as staging:
        staging = Path(staging)
        staging.chmod(0o700)
        for path,raw in snapshots.items():
            if raw is None:
                continue
            relative=path.relative_to(root)
            dest=staging/'snapshot'/relative
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(raw); dest.chmod(0o600)
        for path,raw in snapshots.items():
            if (path.read_bytes() if path.exists() else None) != raw:
                raise ValueError(f'Source changed while preparing: {path}; rerun against fresh inputs')
        (staging/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        (staging/'manifest.json').chmod(0o600)
        # A new private bundle only. Neither Firstmate nor the dashboard reads it.
        os.rename(staging,output)
    return manifest


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--my-root',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    result=prepare(args.my_root,args.output)
    print(json.dumps({k:result[k] for k in ('status','counts','project_links','unmatched_dashboard_project_ids','firstmate_only_projects')},ensure_ascii=False,indent=2))
