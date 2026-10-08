import tempfile
import threading
import unittest
from pathlib import Path

import serve
from context_fixture import create_context


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.original_paths = (
            serve.DATA,
            serve.INBOX,
            serve.INBOX_PENDING,
        )
        serve.DATA = root / "data"
        serve.INBOX = root / "inbox.md"
        serve.INBOX_PENDING = root / ".inbox-pending.md"
        serve.atomic_write(serve.INBOX, serve.INBOX_HEADER)
        serve.atomic_write(serve.INBOX_PENDING, "")
        self.store = create_context(root, {"projects":[],"tasks":[],"reminders":[]})
        serve._workspace_agent_active = False

    def tearDown(self):
        (
            serve.DATA,
            serve.INBOX,
            serve.INBOX_PENDING,
        ) = self.original_paths
        serve._workspace_agent_active = False
        self.tmp.cleanup()

    @staticmethod
    def task(identity):
        return {"id":identity,"title":identity,"due":None,"status":"open","created":"before","notes":""}

    def test_stale_workspace_update_is_rejected(self):
        first = serve.read_workspace_snapshot()
        _, new_version = serve.update_workspace(
            {"tasks": [self.task("first")]}, first["_version"]
        )

        with self.assertRaises(serve.WorkspaceConflict):
            serve.update_workspace(
                {"tasks": [self.task("stale")]}, first["_version"]
            )

        current = serve.read_workspace_snapshot()
        self.assertEqual(current["tasks"], [self.task("first")])
        self.assertEqual(current["_version"], new_version)

    def test_browser_update_is_rejected_while_agent_is_active(self):
        snapshot = serve.read_workspace_snapshot()
        serve._workspace_agent_active = True

        with self.assertRaises(serve.WorkspaceBusy):
            serve.update_workspace({"tasks": []}, snapshot["_version"])

    def test_malformed_workspace_is_not_treated_as_empty(self):
        malformed = b'{"tasks": ['
        serve.atomic_write(self.store.path, malformed)

        with self.assertRaises(serve.WorkspaceDataError):
            serve.read_workspace()

        self.assertEqual(self.store.path.read_bytes(), malformed)

    def test_concurrent_workspace_reads_never_see_partial_json(self):
        failures = []

        def writer(prefix):
            for index in range(30):
                while True:
                    snapshot = serve.read_workspace_snapshot()
                    item = {**self.task(f"{prefix}-{index}"), "notes":"x"*5000}
                    try:
                        serve.update_workspace({"tasks":[item]}, snapshot['_version'])
                        break
                    except serve.WorkspaceConflict:
                        continue


        threads = [threading.Thread(target=writer, args=(name,)) for name in ("a", "b")]
        for thread in threads:
            thread.start()
        while any(thread.is_alive() for thread in threads):
            try:
                serve.read_workspace()
            except Exception as exc:  # pragma: no cover - assertion captures the type
                failures.append(exc)
        for thread in threads:
            thread.join()

        self.assertEqual(failures, [])

    def test_note_arriving_during_run_remains_for_next_run(self):
        serve.append_pending_inbox("first note")
        self.assertTrue(serve.stage_pending_inbox())
        self.assertIn("first note", serve.INBOX.read_text(encoding="utf-8"))

        # This append represents a request received while the agent owns inbox.md.
        serve.append_pending_inbox("second note")
        serve.atomic_write(serve.INBOX, serve.INBOX_HEADER)

        self.assertTrue(serve.stage_pending_inbox())
        self.assertIn("second note", serve.INBOX.read_text(encoding="utf-8"))
        self.assertEqual(serve.INBOX_PENDING.read_text(encoding="utf-8"), "")


if __name__ == "__main__":
    unittest.main()
