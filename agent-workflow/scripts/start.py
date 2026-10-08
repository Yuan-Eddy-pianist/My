#!/usr/bin/env python3
"""Start or reattach the primary Firstmate, without mistaking crew for it."""
import argparse
import fcntl
import json
import os
import platform
import shutil
import subprocess
import time
from pathlib import Path


def in_directory(value, directory):
    return bool(value) and Path(value).resolve().is_relative_to(directory.resolve())


def select_primary(root, panes, agents, workspaces):
    """Use primary session identity first, then the explicitly named workspace."""
    repo = (root / 'firstmate').resolve()
    by_pane = {a['pane_id']: a for a in agents}
    primary = []
    for pane in panes:
        agent = by_pane.get(pane['pane_id'], pane)
        session = agent.get('agent_session', {})
        if session.get('kind') == 'path' and in_directory(session.get('value'), root / 'sessions/primary'):
            if Path(pane.get('cwd', '')).resolve() != repo:
                raise RuntimeError('Primary session is in another folder; inspect it before switching copies.')
            primary.append(pane)
    if len(primary) == 1:
        return primary[0]
    if len(primary) > 1:
        raise RuntimeError('Multiple primary conversations are running; select one manually in Herdr.')
    named = {w['workspace_id'] for w in workspaces if w.get('label') == 'firstmate'}
    candidates = []
    for pane in panes:
        if pane.get('workspace_id') not in named:
            continue
        if Path(pane.get('cwd', '')).resolve() != repo:
            raise RuntimeError('The firstmate workspace belongs to another folder; inspect it before switching copies.')
        agent = by_pane.get(pane['pane_id'])
        # A named workspace may contain workers too. Never start over them or
        # claim an unknown conversation as the primary merely because of cwd.
        if agent or pane.get('agent'):
            continue
        candidates.append(pane)
    if len(candidates) == 1:
        return candidates[0]
    if candidates or named or panes:
        raise RuntimeError('Cannot safely identify the primary Firstmate pane. Inspect the firstmate workspace in Herdr.')
    return None


def check_supervisor_owner(repo, pane, call):
    """A suspended Pi still owns supervision although Herdr sees a shell."""
    lock = repo / 'state/.lock'
    if not lock.exists():
        return
    try:
        pid = int(lock.read_text().strip())
    except ValueError:
        raise RuntimeError('Invalid Firstmate supervisor lock; inspect state/.lock before starting.')
    if pid <= 1:
        raise RuntimeError('Invalid Firstmate supervisor PID.')
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return
    process = subprocess.run(['ps', '-p', str(pid), '-o', 'comm='],
                             capture_output=True, text=True, timeout=5)
    if process.returncode:
        raise RuntimeError(f'Cannot verify Firstmate lock owner PID {pid}; retry after checking it.')
    if Path(process.stdout.strip()).name not in ('pi', 'node'):
        return  # PID reused by an unrelated executable; upstream reclaims stale locks.
    foreground = []
    if pane:
        info = call('pane', 'process-info', '--pane', pane['pane_id'])['result']['process_info']
        foreground = info.get('foreground_processes', [])
    if not any(p.get('pid') == pid for p in foreground):
        raise RuntimeError(f'Firstmate PID {pid} still owns control but is not the primary foreground process. '
                           'It may be suspended. Resume or stop that process before starting another Firstmate.')


def pi_arguments(root):
    repo = root / 'firstmate'
    args = ['-a', '--session-dir', str(root / 'sessions/primary')]
    recovery = root / 'local/resume-primary.json'
    if recovery.exists():
        name = json.loads(recovery.read_text())['session']
        session = root / 'sessions/primary' / name
        if Path(name).name != name or not session.is_file():
            raise RuntimeError('The selected recovery conversation is missing or invalid.')
        args.extend(['--session', str(session)])
    else:
        args.append('--continue')
    # Explicit append prompts disable Pi's automatic APPEND_SYSTEM discovery.
    # Preserve the file Pi would normally load as well as the relocation hint.
    for path in (repo / '.pi/APPEND_SYSTEM.md', Path.home() / '.pi/agent/APPEND_SYSTEM.md'):
        if path.is_file():
            args.extend(['--append-system-prompt', str(path)])
            break
    args.extend(['--append-system-prompt',
                 f'The current Firstmate home is {repo}. Historical absolute paths in old messages are not current locations. '
                 f'Use the current working directory and FM_HOME. New crew sessions are stored under {root}/sessions/crew.'])
    return args


def main(argv=None, root=None):
    parser = argparse.ArgumentParser(prog='firstmate', description='Open Firstmate in WezTerm, starting or reattaching the primary session.')
    parser.add_argument('--headless', action='store_true', help='ensure Firstmate is running without opening WezTerm')
    parser.add_argument('--status', action='store_true', help='inspect the primary session without starting or changing it')
    options = parser.parse_args(argv)
    root = (root or Path(__file__).resolve().parents[1]).resolve()
    repo = root / 'firstmate'
    marker = root / 'local/installation.json'
    binding = json.loads(marker.read_text()) if marker.exists() else {}
    if (binding.get('root'), binding.get('home'), binding.get('host')) != (str(root), str(Path.home()), platform.node()):
        raise RuntimeError('Run Setup.command on this device/location first.')
    env = os.environ.copy()
    env['FM_HOME'] = str(repo)
    env['PI_CODING_AGENT_SESSION_DIR'] = str(root / 'sessions/crew')

    def call(*args):
        proc = subprocess.run(['herdr', '--session', 'firstmate', *args], env=env, cwd=repo,
                              text=True, capture_output=True, timeout=45)
        if proc.returncode:
            raise RuntimeError((proc.stderr or proc.stdout).strip())
        result = json.loads(proc.stdout)
        if result.get('error'):
            raise RuntimeError(str(result['error']))
        return result

    def primary():
        return select_primary(root, call('pane', 'list')['result']['panes'],
                              call('agent', 'list')['result']['agents'],
                              call('workspace', 'list')['result']['workspaces'])

    if options.status:
        if not call('status', '--json').get('server', {}).get('running'):
            check_supervisor_owner(repo, None, call)
            print('Firstmate server is stopped.')
            return
        pane = primary()
        check_supervisor_owner(repo, pane, call)
        agents = call('agent', 'list')['result']['agents']
        running = pane and any(a['pane_id'] == pane['pane_id'] for a in agents)
        print('Firstmate is ' + ('running' if running else 'stopped') +
              (f" in {pane['pane_id']}" if pane else '') + f' ({repo}).')
        return

    if not options.headless and not shutil.which('wezterm'):
        raise RuntimeError('WezTerm is required. Install WezTerm, then run firstmate again.')
    (root / 'local').mkdir(exist_ok=True)
    # Two simultaneous launches must not create two primary conversations.
    with (root / 'local/start.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        (root / 'local/transfer-ready.txt').unlink(missing_ok=True)
        if not call('status', '--json').get('server', {}).get('running'):
            check_supervisor_owner(repo, None, call)
            npm = subprocess.check_output(['npm', 'root', '-g'], text=True, timeout=30).strip()
            env['CHROME_DEVTOOLS_AXI_MCP_PATH'] = str(Path(npm) / 'chrome-devtools-mcp/build/src/bin/chrome-devtools-mcp.js')
            with (root / 'local/herdr-start.log').open('a') as log:
                subprocess.Popen(['herdr', '--session', 'firstmate', 'server'], cwd=repo, env=env,
                                 stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
            for _ in range(40):
                time.sleep(.25)
                try:
                    if call('status', '--json').get('server', {}).get('running'):
                        break
                except RuntimeError:
                    pass
            else:
                raise RuntimeError('Herdr did not start; inspect local/herdr-start.log.')
        pane = primary()
        check_supervisor_owner(repo, pane, call)
        if pane is None:
            result = call('workspace', 'create', '--cwd', str(repo), '--label', 'firstmate')['result']
            pane = result['root_pane']
        pane_id = pane['pane_id']
        agents = call('agent', 'list')['result']['agents']
        if not any(a['pane_id'] == pane_id for a in agents):
            call('agent', 'start', 'firstmate-primary', '--kind', 'pi', '--pane', pane_id,
                 '--timeout', '30000', '--', *pi_arguments(root))
            (root / 'local/resume-primary.json').unlink(missing_ok=True)
    if not options.headless:
        call('agent', 'focus', pane_id)
        os.execvpe('wezterm', ['wezterm', 'start', '--cwd', str(repo), '--',
                              'herdr', '--session', 'firstmate'], env)
    print('Firstmate is ready in', repo)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as exc:
        raise SystemExit(str(exc))
