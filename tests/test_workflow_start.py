"""Launcher regressions, exercised without touching the user's agent processes."""
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'agent-workflow/scripts/start.py'
spec = importlib.util.spec_from_file_location('workflow_start', SCRIPT)
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = (Path(self.tmp.name) / 'Moved folder' / 'agent-workflow').resolve()
        self.repo = self.root / 'firstmate'
        self.repo.mkdir(parents=True)
        (self.root / 'local').mkdir()
        (self.root / 'local/installation.json').write_text(json.dumps({
            'root': str(self.root), 'home': str(Path.home()), 'host': platform.node()}))
        self.shell = {'pane_id': 'primary:p1', 'workspace_id': 'primary', 'cwd': str(self.repo)}
        self.worker = {'pane_id': 'worker:p2', 'workspace_id': 'worker', 'cwd': str(self.repo),
                       'agent': 'pi', 'agent_session': {'kind': 'path', 'value': str(self.root / 'sessions/crew/worker.jsonl')}}
        self.spaces = [{'workspace_id': 'primary', 'label': 'firstmate'},
                       {'workspace_id': 'worker', 'label': 'worker-health'}]

    def test_worker_in_same_folder_does_not_make_primary_ambiguous(self):
        result = launcher.select_primary(self.root, [self.shell, self.worker], [self.worker], self.spaces)
        self.assertEqual(result, self.shell)

    def test_running_primary_session_wins_even_if_workspace_renamed(self):
        primary = {**self.shell, 'agent': 'pi', 'agent_session': {
            'kind': 'path', 'value': str(self.root / 'sessions/primary/saved.jsonl')}}
        self.assertEqual(launcher.select_primary(self.root, [primary, self.worker], [primary, self.worker], []), primary)

    def test_never_adopts_worker_even_if_it_is_in_named_workspace(self):
        worker = {**self.worker, 'workspace_id': 'primary'}
        with self.assertRaises(RuntimeError):
            launcher.select_primary(self.root, [worker], [worker], self.spaces)

    def test_other_copy_and_multiple_shells_are_not_automatically_replaced(self):
        for panes in ([{**self.shell, 'cwd': '/another/copy/firstmate'}],
                      [self.shell, {**self.shell, 'pane_id': 'primary:p3'}]):
            with self.subTest(panes=panes), self.assertRaises(RuntimeError):
                launcher.select_primary(self.root, panes, [], self.spaces)

    def test_start_reuses_primary_shell_and_reattaches_without_duplicate(self):
        calls = []
        agents = [self.worker]
        def run(command, **kwargs):
            args = command[3:]
            calls.append(args)
            if args == ['status', '--json']:
                result = {'server': {'running': True}}
            elif args == ['pane', 'list']:
                result = {'result': {'panes': [self.shell, self.worker]}}
            elif args == ['agent', 'list']:
                result = {'result': {'agents': agents}}
            elif args == ['workspace', 'list']:
                result = {'result': {'workspaces': self.spaces}}
            elif args == ['agent', 'focus', self.shell['pane_id']]:
                result = {'result': {}}
            elif args[:2] == ['agent', 'start']:
                self.assertEqual(args[args.index('--pane') + 1], self.shell['pane_id'])
                agents.append({**self.shell, 'agent': 'pi', 'agent_session': {
                    'kind': 'path', 'value': str(self.root / 'sessions/primary/resumed.jsonl')}})
                result = {'result': {}}
            else:
                self.fail(f'Unexpected mutation or command: {args}')
            return subprocess.CompletedProcess(command, 0, json.dumps(result), '')
        with patch.object(launcher.subprocess, 'run', side_effect=run):
            launcher.main(['--headless'], root=self.root)
            launcher.main(['--headless'], root=self.root)
            launcher.main(['--status'], root=self.root)
            with patch.object(launcher.shutil, 'which', return_value='/usr/local/bin/wezterm'):
                with patch.object(launcher.os, 'execvpe') as launch:
                    launcher.main([], root=self.root)
            launch.assert_called_once()
            self.assertEqual(launch.call_args.args[:2], ('wezterm', [
                'wezterm', 'start', '--cwd', str(self.repo), '--', 'herdr', '--session', 'firstmate']))
        self.assertEqual(sum(c[:2] == ['agent', 'start'] for c in calls), 1)

    def test_missing_wezterm_fails_before_changing_the_session(self):
        with patch.object(launcher.shutil, 'which', return_value=None):
            with patch.object(launcher.subprocess, 'run') as run:
                with self.assertRaisesRegex(RuntimeError, 'WezTerm is required'):
                    launcher.main([], root=self.root)
        run.assert_not_called()
        self.assertFalse((self.root / 'local/start.lock').exists())

    def test_status_is_read_only_and_does_not_require_npm(self):
        with patch.object(launcher.subprocess, 'run', return_value=subprocess.CompletedProcess(
            [], 0, '{"server":{"running":false}}', '')) as call:
            launcher.main(['--status'], root=self.root)
        self.assertEqual(call.call_count, 1)
        self.assertFalse((self.root / 'local/start.lock').exists())

    def test_suspended_owner_blocks_another_primary(self):
        (self.repo / 'state').mkdir()
        (self.repo / 'state/.lock').write_text('19428\n')
        info = {'result': {'process_info': {'foreground_processes': [{'pid': 69362}]}}}
        with patch.object(launcher.os, 'kill'), patch.object(launcher.subprocess, 'run',
                return_value=subprocess.CompletedProcess([], 0, 'pi\n', '')):
            with self.assertRaisesRegex(RuntimeError, '19428.*still owns control'):
                launcher.check_supervisor_owner(self.repo, self.shell, lambda *args: info)
            info['result']['process_info']['foreground_processes'] = [{'pid': 19428}]
            launcher.check_supervisor_owner(self.repo, self.shell, lambda *args: info)
        with patch.object(launcher.os, 'kill', side_effect=ProcessLookupError):
            launcher.check_supervisor_owner(self.repo, None, None)

    def test_standalone_owner_blocks_starting_a_server(self):
        with patch.object(launcher.subprocess, 'run', return_value=subprocess.CompletedProcess(
                [], 0, '{"server":{"running":false}}', '')):
            with patch.object(launcher, 'check_supervisor_owner', side_effect=RuntimeError('owner is alive')):
                with patch.object(launcher.subprocess, 'Popen') as start:
                    with self.assertRaisesRegex(RuntimeError, 'owner is alive'):
                        launcher.main(['--headless'], root=self.root)
        start.assert_not_called()

    def test_recovery_resumes_selected_conversation_instead_of_latest_duplicate(self):
        sessions = self.root / 'sessions/primary'
        sessions.mkdir(parents=True)
        (sessions / 'original.jsonl').write_text('{}\n')
        (sessions / 'duplicate.jsonl').write_text('{}\n')
        marker = self.root / 'local/resume-primary.json'
        marker.write_text('{"session":"original.jsonl"}')
        args = launcher.pi_arguments(self.root)
        self.assertNotIn('--continue', args)
        self.assertEqual(args[args.index('--session')+1], str(sessions / 'original.jsonl'))
        marker.write_text('{"session":"../outside.jsonl"}')
        with self.assertRaises(RuntimeError):
            launcher.pi_arguments(self.root)

    @unittest.skipUnless(os.environ.get('PI_PACKAGE_DIR'), 'Set PI_PACKAGE_DIR for real Pi loading')
    def test_actual_launch_arguments_load_personal_agenda_and_relocation_hint(self):
        (self.repo / '.pi').mkdir()
        (self.repo / '.pi/APPEND_SYSTEM.md').write_text('Personal agenda sentinel 73852')
        args = launcher.pi_arguments(self.root)
        appends = [args[i+1] for i, value in enumerate(args) if value == '--append-system-prompt']
        script = '''
import {pathToFileURL} from 'node:url';
const {DefaultResourceLoader}=await import(pathToFileURL(process.env.PI_PACKAGE_DIR+'/dist/core/resource-loader.js'));
const loader=new DefaultResourceLoader({cwd:process.env.FIXTURE_HOME,agentDir:process.env.FIXTURE_HOME+'/empty-agent',appendSystemPrompt:JSON.parse(process.env.APPENDS),noExtensions:true,noSkills:true,noPromptTemplates:true,noThemes:true});
await loader.reload({resolveProjectTrust:async()=>true});
const text=loader.getAppendSystemPrompt().join('\\n');
if(!text.includes('Personal agenda sentinel 73852') || !text.includes('current Firstmate home')) throw new Error('Launch dropped context');
'''
        result = subprocess.run(['node', '--input-type=module', '-'], input=script, text=True, capture_output=True,
            env={**os.environ, 'FIXTURE_HOME': str(self.repo), 'APPENDS': json.dumps(appends)})
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
