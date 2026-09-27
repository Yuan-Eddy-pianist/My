#!/usr/bin/env python3
"""Start or reattach one explicitly scoped Firstmate workspace."""
import json, os, platform, subprocess, time
from pathlib import Path

root=Path(__file__).resolve().parents[1]
repo=root/'firstmate'
marker=root/'local/installation.json'
binding=json.loads(marker.read_text()) if marker.exists() else {}
if (binding.get('root'),binding.get('home'),binding.get('host')) != (str(root),str(Path.home()),platform.node()):
    raise SystemExit('Run Setup.command on this device/location first.')
env=os.environ.copy()
env['FM_HOME']=str(repo)
env['PI_CODING_AGENT_SESSION_DIR']=str(root/'sessions/crew')
npm=subprocess.check_output(['npm','root','-g'],text=True).strip()
env['CHROME_DEVTOOLS_AXI_MCP_PATH']=str(Path(npm)/'chrome-devtools-mcp/build/src/bin/chrome-devtools-mcp.js')
def call(*args):
    p=subprocess.run(['herdr','--session','firstmate',*args],env=env,cwd=repo,text=True,capture_output=True)
    if p.returncode: raise RuntimeError(p.stderr or p.stdout)
    return json.loads(p.stdout)
status=call('status','--json')
if not status.get('server',{}).get('running'):
    (root/'local').mkdir(exist_ok=True)
    with (root/'local/herdr-start.log').open('a') as log:
        subprocess.Popen(['herdr','--session','firstmate','server'],cwd=repo,env=env,
                         stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
    for _ in range(40):
        time.sleep(.25)
        try:
            if call('status','--json').get('server',{}).get('running'): break
        except RuntimeError: pass
    else: raise SystemExit('Herdr did not start; inspect local/herdr-start.log.')
panes=call('pane','list')['result']['panes']
matches=[p for p in panes if Path(p.get('cwd',''))==repo]
if not matches:
    if panes: raise SystemExit('Existing firstmate session belongs to another folder. Stop it before switching copies.')
    result=call('workspace','create','--cwd',str(repo),'--label','firstmate')['result']
    pane=result['root_pane']['pane_id']
else:
    if len(matches)!=1: raise SystemExit('Multiple primary panes found; select one manually with herdr --session firstmate.')
    pane=matches[0]['pane_id']
agents=call('agent','list')['result']['agents']
if not any(a.get('pane_id')==pane for a in agents):
    call('agent','start','firstmate-primary','--kind','pi','--pane',pane,'--timeout','30000','--',
         '-a','--session-dir',str(root/'sessions/primary'),'--continue',
         '--append-system-prompt',f'The current Firstmate home is {repo}. The workspace has moved; historical absolute paths in old messages are not current locations. Use the current working directory and FM_HOME. New crew sessions are stored under {root}/sessions/crew.')
if '--headless' not in os.sys.argv:
    os.chdir(repo)
    os.execvpe('herdr',['herdr','--session','firstmate'],env)
print('Firstmate is ready in',repo)
