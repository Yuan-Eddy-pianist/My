#!/usr/bin/env python3
"""Bind portable preferences to this computer; leave authentication local."""
import json, os, platform, shutil, subprocess, time
from pathlib import Path
from workflow_paths import project_link_updates, apply_project_links, backup_state

ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
stamp = time.strftime('%Y%m%d-%H%M%S')
backup = ROOT / 'archives' / ('settings-' + stamp)
marker = ROOT/'local/installation.json'
prior = json.loads(marker.read_text()) if marker.exists() else {}
try:
    link_updates = project_link_updates(ROOT, prior)
except RuntimeError as exc:
    raise SystemExit(str(exc))
if marker.exists():
    if (prior.get('root'),prior.get('home'),prior.get('host')) != (str(ROOT),str(HOME),platform.node()):
        state=ROOT/'firstmate/state'
        if state.exists() and any(state.iterdir()) and not (ROOT/'local/transfer-ready.txt').is_file():
            raise SystemExit('This copy has unprepared Firstmate state. Run Prepare transfer.command at the original location before copying; no records were moved.')
        if list(state.glob('*.meta')):
            raise SystemExit('Copied workspace has task records. Finish/park its workers on the original device before migration.')
        for project in (ROOT/'firstmate/projects').iterdir():
            if (project/'.git/worktrees').exists() and any((project/'.git/worktrees').iterdir()):
                raise SystemExit('Copied project has linked worktrees. Run Prepare transfer.command on the original device first.')
        backup_state(ROOT, 'runtime-before-rebind-'+stamp)
def save(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text() != text:
        backup.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup / str(path.relative_to(HOME)).replace('/', '__'))
    path.write_text(text)
def run(*args):
    return subprocess.check_output(args, text=True).strip()

for name in ['python3','node','npm','bash','pi','herdr','treehouse']:
    if not shutil.which(name): raise SystemExit(f'Missing {name}; run Setup.command first.')
if int(run('bash','-c','echo ${BASH_VERSINFO[0]}')) < 5:
    raise SystemExit('Bash 5+ must be first on PATH.')
npm = Path(run('npm','root','-g'))
profile = json.loads((ROOT/'config/pi-profile.json').read_text())
settings_path = HOME/'.pi/agent/settings.json'
settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
settings.update(profile)
skills = [str(npm/name/'skills'/skill) for name,skill in [
    ('lavish-axi','lavish'),('gh-axi','gh-axi'),('tasks-axi','tasks-axi'),
    ('quota-axi','quota-axi'),('chrome-devtools-axi','chrome-devtools-axi'),('gnhf','gnhf')]]
skills.append(str(ROOT/'config/skills/herdr'))
# Replace only the paths owned by this workflow, preserving unrelated skills.
owned = ('/node_modules/lavish-axi/', '/node_modules/gh-axi/', '/node_modules/tasks-axi/',
         '/node_modules/quota-axi/', '/node_modules/chrome-devtools-axi/', '/node_modules/gnhf/',
         '/skills/herdr')
settings['skills'] = [s for s in settings.get('skills',[]) if not any(x in s for x in owned)] + skills
settings['shellPath'] = shutil.which('bash')
bridge = npm/'chrome-devtools-mcp/build/src/bin/chrome-devtools-mcp.js'
import shlex
settings['shellCommandPrefix'] = 'export CHROME_DEVTOOLS_AXI_MCP_PATH=' + shlex.quote(str(bridge)) + ';'
save(settings_path, json.dumps(settings,indent=2)+'\n')
for src,dst in [('herdr.toml','.config/herdr/config.toml'),('wezterm.lua','.config/wezterm/wezterm.lua')]:
    save(HOME/dst,(ROOT/'config'/src).read_text())
tree_path=HOME/'.config/treehouse/config.toml'
if tree_path.exists():
    import re
    tree=tree_path.read_text()
    # This workflow owns the root only; preserve other settings and hooks.
    tree=re.sub(r'^root\s*=.*\n?', '', tree, flags=re.M)
else: tree=''
save(tree_path,'root = '+json.dumps(str(ROOT/'.runtime/worktrees'))+'\n'+tree)
save(HOME/'.gnhf/config.yml', 'agent: pi\nagentModel:\n  pi: openai-codex/gpt-6-sol\nmaxConsecutiveFailures: 3\npreventSleep: true\n')
wrapper='#!/bin/sh\nset -eu\nexport PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"\nexec python3 '+shlex.quote(str(ROOT/'scripts/start.py'))+' "$@"\n'
save(HOME/'.local/bin/firstmate',wrapper)
(HOME/'.local/bin/firstmate').chmod(0o755)
for name in ['pi','codex']:
    subprocess.run(['herdr','integration','install',name],check=True)
apply_project_links(link_updates)
(ROOT/'local').mkdir(exist_ok=True)
(ROOT/'local/installation.json').write_text(json.dumps({'root':str(ROOT),'home':str(HOME),'host':platform.node()},indent=2)+'\n')
(ROOT/'local/transfer-ready.txt').unlink(missing_ok=True)
print('Configured this device. Credentials remain in its own account stores.')
