#!/usr/bin/env python3
"""Quiesce this workspace and check that its projects can be copied safely."""
import json, os, shutil, subprocess, time
from pathlib import Path
from workflow_paths import backup_state

root=Path(__file__).resolve().parents[1]
repo=root/'firstmate'
if list((repo/'state').glob('*.meta')):
    raise SystemExit('Firstmate still has task records. Ask it to finish and clean up all workers, then retry.')
# Complete project checks before stopping the idle primary.
for project in (repo/'projects').iterdir():
    if project.is_symlink() and not project.exists():
        raise SystemExit(f'{project.name} has a missing linked project. Repair it before transfer.')
    if project.is_symlink() and not project.resolve().is_relative_to(root.parent):
        print(f'Also copy this external project separately: {project.resolve()}')
    if not (project/'.git').exists(): continue
    listing=subprocess.check_output(['git','worktree','list','--porcelain'],cwd=project,text=True)
    if sum(line.startswith('worktree ') for line in listing.splitlines())!=1:
        raise SystemExit(f'{project.name} still has linked worktrees. Nothing was stopped or deleted. Ask Firstmate to inspect them before copying.')
def call(*args):
    return json.loads(subprocess.check_output(['herdr','--session','firstmate',*args],text=True))
if call('status','--json').get('server',{}).get('running'):
    agents=call('agent','list')['result']['agents']
    if len(agents)>1 or any(a.get('cwd')!=str(repo) or a.get('agent_status') not in ['idle','done'] for a in agents):
        raise SystemExit('An agent is active or this session belongs to another folder. Finish it before transfer.')
    for agent in agents:
        call('agent','prompt',agent['pane_id'],'/quit')
    for _ in range(60):
        if not call('agent','list')['result']['agents']: break
        time.sleep(.5)
    else: raise SystemExit('Pi did not exit. Its work is preserved; stop it manually before transfer.')
    subprocess.run(['herdr','--session','firstmate','server','stop'],check=True)
settings=json.loads((Path.home()/'.pi/agent/settings.json').read_text())
keys=['defaultProvider','defaultModel','defaultThinkingLevel','packages','theme','hideThinkingBlock','steeringMode','followUpMode','compaction']
(root/'config/pi-profile.json').write_text(json.dumps({k:settings[k] for k in keys if k in settings},indent=2)+'\n')
for src,dst in [('.config/herdr/config.toml','herdr.toml'),('.config/wezterm/wezterm.lua','wezterm.lua')]:
    p=Path.home()/src
    if p.exists(): shutil.copy2(p,root/'config'/dst)
stamp=time.strftime('%Y%m%d-%H%M%S')
backup_state(root, 'runtime-before-transfer-'+stamp)
(root/'local/transfer-ready.txt').write_text('Prepared '+stamp+'\nCopy the entire folder, including hidden .git directories.\n')
print('Ready to copy. Firstmate is stopped; projects and conversation files are preserved.')
print('On the destination run Setup.command, sign in there, then run firstmate in your terminal.')
