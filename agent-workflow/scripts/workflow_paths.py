"""Narrow relocation helpers. Never discard Firstmate's durable state."""
import os
from pathlib import Path
import shutil


def project_link_updates(root, prior):
    """Plan links inside the old My tree; reject unavailable external projects."""
    root = Path(root).resolve()
    old_root = Path(prior['root']) if prior.get('root') else root
    old_my = old_root.parent
    new_my = root.parent
    updates = []
    projects = root / 'firstmate/projects'
    for link in projects.iterdir():
        if not link.is_symlink():
            continue
        raw = Path(os.readlink(link))
        if raw.is_absolute() and raw.is_relative_to(old_my):
            target = new_my / raw.relative_to(old_my)
            if not target.exists():
                raise RuntimeError(f'Project {link.name} is missing at its relocated path: {target}')
            if link.resolve() != target.resolve():
                updates.append((link, target))
        elif not link.exists():
            raise RuntimeError(f'Project {link.name} links outside this copy ({raw}). Copy that project and update its link before Setup.')
    return updates


def apply_project_links(updates):
    for link, target in updates:
        # Relative links keep working on subsequent whole-My folder moves.
        replacement = link.with_name(link.name + '.relocating')
        if replacement.exists() or replacement.is_symlink():
            raise RuntimeError(f'Relocation temporary path already exists: {replacement}')
        replacement.symlink_to(os.path.relpath(target, link.parent))
        try:
            os.replace(replacement, link)
        finally:
            replacement.unlink(missing_ok=True)


def backup_state(root, label):
    state = root / 'firstmate/state'
    if state.exists() and any(state.iterdir()):
        destination = root / 'archives' / label
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(state, destination, symlinks=True)
        return destination
    return None
