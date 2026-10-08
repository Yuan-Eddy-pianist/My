"""Relocation must not target the source tree or discard supervision records."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'agent-workflow/scripts'
spec = importlib.util.spec_from_file_location('workflow_paths', SCRIPTS / 'workflow_paths.py')
paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paths)


class RelocationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.old = self.base / 'old My/agent-workflow'
        self.root = self.base / 'new My/agent-workflow'
        self.projects = self.root / 'firstmate/projects'
        self.projects.mkdir(parents=True)
        self.old.mkdir(parents=True)
        self.prior = {'root': str(self.old), 'host': 'same-host'}

    def test_self_project_rebinds_to_copy_and_survives_another_move(self):
        link = self.projects / 'My'
        link.symlink_to(self.old.parent)
        paths.apply_project_links(paths.project_link_updates(self.root, self.prior))
        self.assertEqual(link.resolve(), self.root.parent)
        self.assertFalse(Path(os.readlink(link)).is_absolute())
        moved = self.base / 'another My'
        shutil.move(self.root.parent, moved)
        self.assertEqual((moved / 'agent-workflow/firstmate/projects/My').resolve(), moved)

    def test_external_links_must_exist_and_can_be_repaired_before_setup(self):
        external = self.base / 'external'
        external.mkdir()
        (self.projects / 'External').symlink_to(external)
        self.assertEqual(paths.project_link_updates(self.root, self.prior), [])
        external.rmdir()
        with self.assertRaises(RuntimeError):
            paths.project_link_updates(self.root, self.prior)
        external.mkdir()
        self.assertEqual(paths.project_link_updates(self.root, self.prior), [])

    def test_failed_plan_changes_no_links(self):
        (self.projects / 'My').symlink_to(self.old.parent)
        (self.projects / 'Missing').symlink_to('/no/such/project')
        with self.assertRaises(RuntimeError):
            paths.project_link_updates(self.root, self.prior)
        self.assertEqual((self.projects / 'My').resolve(), self.old.parent)

    def test_prepare_transfer_keeps_durable_state_in_place(self):
        state = self.root / 'firstmate/state'
        state.mkdir()
        records = {'branch-outcomes.jsonl': '{"seq":1,"verdict":"captain"}\n',
                   '.branch-outcomes-cursor': '0\n', '.branch-outcomes-processed': '0\n'}
        for name, content in records.items():
            (state / name).write_text(content)
        (self.root / 'scripts').mkdir()
        for name in ('prepare-transfer.py', 'workflow_paths.py'):
            shutil.copy2(SCRIPTS / name, self.root / 'scripts' / name)
        for name in ('config', 'local'):
            (self.root / name).mkdir()
        home = self.base / 'home'
        (home / '.pi/agent').mkdir(parents=True)
        (home / '.pi/agent/settings.json').write_text('{}')
        tools = self.base / 'bin'
        tools.mkdir()
        herdr = tools / 'herdr'
        herdr.write_text('#!/bin/sh\ncase "$*" in "--session firstmate status --json") echo \'{"server":{"running":false}}\';; *) exit 90;; esac\n')
        herdr.chmod(0o755)
        result = subprocess.run(['python3', str(self.root / 'scripts/prepare-transfer.py')], text=True,
                                capture_output=True, env={**os.environ, 'HOME': str(home), 'PATH': str(tools)+os.pathsep+os.environ['PATH']})
        self.assertEqual(result.returncode, 0, result.stderr)
        backup = next((self.root / 'archives').iterdir())
        for name, content in records.items():
            self.assertEqual((state / name).read_text(), content)
            self.assertEqual((backup / name).read_text(), content)


if __name__ == '__main__':
    unittest.main()
