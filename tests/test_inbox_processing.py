import json
import queue
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import serve
from context_fixture import create_context
from firstmate_context import render_context


class InboxProcessingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "data").mkdir()
        entry = root / "agent.js"
        entry.write_text("// subprocess is mocked\n", encoding="utf-8")
        replacements = {
            "ROOT": root,
            "DATA": root / "data",
            "INBOX": root / "data" / "inbox.md",
            "INBOX_PENDING": root / "data" / ".inbox-pending.md",
            "ARCHIVE": root / "data" / "inbox-archive.md",
            "STATUS": root / "data" / ".agent-status.json",
            "MY_AGENT_ENTRY": entry,
            "_workspace_agent_active": False,
            "_voice_pending": 0,
            "_job_queue": queue.Queue(),
        }
        paths = patch.multiple(serve, **replacements)
        paths.start()
        self.addCleanup(paths.stop)
        node = patch.object(serve.shutil, "which", return_value="/fake/node")
        node.start()
        self.addCleanup(node.stop)
        statuses = patch.object(serve, "write_status", wraps=serve.write_status)
        self.statuses = statuses.start()
        self.addCleanup(statuses.stop)

        self.note = "Buy milk tomorrow and remind me about the appointment Friday."
        serve.atomic_write(
            serve.INBOX, serve.INBOX_HEADER + "\n## 2026-09-22T09:00:00+08:00\n\n" + self.note + "\n"
        )
        serve.atomic_write(serve.INBOX_PENDING, "")
        serve.atomic_write(serve.ARCHIVE, "# Inbox archive\n\nAn earlier note must survive.\n")
        self.store = create_context(root, {
            "projects": [], "tasks": [self.item("existing-task", "Keep the existing task")], "reminders": []
        })
        self.current_workspace = self.store.path
        self.originals = {
            path: path.read_bytes() for path in (serve.INBOX, serve.ARCHIVE, self.current_workspace)
        }

    @staticmethod
    def item(item_id, title, due=None):
        return {
            "id": item_id,
            "title": title,
            "due": due,
            "status": "open",
            "created": "2026-09-22T09:00:00+08:00",
            "notes": "",
        }

    @staticmethod
    def completed(stdout="Created 99 reminders.", returncode=0):
        return subprocess.CompletedProcess(["fake-agent"], returncode, stdout, "")

    def overwrite_bookkeeping(self):
        serve.atomic_write(serve.INBOX, serve.INBOX_HEADER)
        serve.atomic_write(serve.ARCHIVE, "Fabricated archive replacing existing history.\n")

    def add_items(self):
        workspace = serve.read_workspace()
        workspace["tasks"].append(self.item("new-task", "Buy milk", "2026-09-23"))
        workspace["reminders"].append(
            self.item("new-reminder", "Appointment", "2026-09-25")
        )
        serve.write_workspace(workspace)

    def seed(self, workspace):
        workspace = {k: workspace[k] for k in ('projects','tasks','reminders')}
        self.store.path.write_text(render_context({'schema':1,'workspace':workspace,'project_links':{}}))

    def run_agent(self, behavior):
        def staged_behavior(*args, **kwargs):
            scratch = Path(kwargs['env']['AGENT_WORKSPACE']) / 'data'
            proposal = scratch / 'proposal.json'
            current = self.current_workspace
            self.current_workspace = proposal
            try:
                with patch.multiple(serve, INBOX=scratch/'inbox.md', ARCHIVE=scratch/'inbox-archive.md'):
                    with patch.object(serve, 'read_workspace', side_effect=lambda: json.loads(proposal.read_text())):
                        with patch.object(serve, 'write_workspace', side_effect=lambda value: serve.atomic_write(proposal,json.dumps(value))):
                            return behavior(*args, **kwargs)
            finally:
                self.current_workspace = current
        with patch.object(serve.subprocess, "run", side_effect=staged_behavior) as process:
            serve.run_agent_once(self.note)
        self.assertFalse(serve._workspace_agent_active)
        return process

    def assert_originals_preserved(self):
        for path, original in self.originals.items():
            with self.subTest(path=path.name):
                self.assertEqual(path.read_bytes(), original)

    def assert_failed(self):
        self.assertEqual(serve.read_status()["state"], "error")
        self.assertNotIn("done", [call.args[0] for call in self.statuses.call_args_list])
        self.assert_originals_preserved()

    def assert_archived_once(self):
        archive = serve.ARCHIVE.read_text(encoding="utf-8")
        self.assertTrue(archive.startswith(self.originals[serve.ARCHIVE].decode()))
        self.assertEqual(archive.count(self.note), 1)
        self.assertNotIn("Fabricated archive", archive)
        self.assertEqual(serve.INBOX.read_text(encoding="utf-8"), serve.INBOX_HEADER)

    def test_claimed_success_without_workspace_changes_retries_and_preserves_input(self):
        observed_inboxes = []

        def fake_agent(*args, **kwargs):
            observed_inboxes.append(serve.INBOX.read_bytes())
            self.overwrite_bookkeeping()
            return self.completed()

        process = self.run_agent(fake_agent)

        self.assertEqual(process.call_count, 2)
        self.assertEqual(observed_inboxes, [self.originals[serve.INBOX]] * 2)
        self.assert_failed()

    def test_retry_can_save_task_and_reminder_using_restored_original_input(self):
        observed_inboxes = []

        def fake_agent(*args, **kwargs):
            observed_inboxes.append(serve.INBOX.read_bytes())
            if len(observed_inboxes) == 2:
                self.add_items()
            self.overwrite_bookkeeping()
            return self.completed()

        process = self.run_agent(fake_agent)

        self.assertEqual(process.call_count, 2)
        self.assertEqual(observed_inboxes, [self.originals[serve.INBOX]] * 2)
        self.assertEqual(serve.read_status()["state"], "done")
        self.assertEqual([item["id"] for item in serve.read_workspace()["tasks"]],
                         ["existing-task", "new-task"])
        self.assertEqual([item["id"] for item in serve.read_workspace()["reminders"]],
                         ["new-reminder"])
        self.assert_archived_once()

    def test_valid_additions_are_archived_by_server_and_status_uses_persisted_data(self):
        def fake_agent(*args, **kwargs):
            self.add_items()
            return self.completed("Created 99 reminders.")

        process = self.run_agent(fake_agent)

        self.assertEqual(process.call_count, 1)
        status = serve.read_status()
        self.assertEqual(status["state"], "done")
        self.assertNotIn("99", status["message"])
        self.assertEqual(len(serve.read_workspace()["tasks"]), 2)
        self.assertEqual(len(serve.read_workspace()["reminders"]), 1)
        self.assert_archived_once()

    def test_explicit_final_noop_is_accepted_without_claiming_workspace_changes(self):
        for marker in ("No clear items; archived only.", "No changes; items already exist."):
            with self.subTest(marker=marker):
                for path, original in self.originals.items():
                    serve.atomic_write(path, original)

                def fake_agent(*args, **kwargs):
                    self.overwrite_bookkeeping()
                    return self.completed("Read the inbox and workspace.\n" + marker + "\n")

                process = self.run_agent(fake_agent)

                self.assertEqual(process.call_count, 1)
                status = serve.read_status()
                self.assertEqual(status["state"], "done")
                self.assertTrue(any(text in status["message"].lower()
                                    for text in ("no changes", "no clear items", "unchanged")),
                                status["message"])
                self.assertEqual(self.current_workspace.read_bytes(), self.originals[self.current_workspace])
                self.assert_archived_once()

    def test_noop_marker_only_counts_when_it_is_the_exact_final_line(self):
        def fake_agent(*args, **kwargs):
            self.overwrite_bookkeeping()
            return self.completed("No clear items; archived only.\nCreated 99 reminders.")

        process = self.run_agent(fake_agent)

        self.assertEqual(process.call_count, 2)
        self.assert_failed()

    def test_formatting_only_workspace_write_is_not_a_semantic_change(self):
        def fake_agent(*args, **kwargs):
            serve.atomic_write(self.current_workspace, json.dumps(serve.read_workspace(), separators=(",", ":")))
            self.overwrite_bookkeeping()
            return self.completed()

        process = self.run_agent(fake_agent)

        self.assertEqual(process.call_count, 2)
        self.assert_failed()

    def test_new_reminder_requires_a_due_date(self):
        for due_field in ("missing", "null"):
            with self.subTest(due_field=due_field):
                def fake_agent(*args, **kwargs):
                    workspace = serve.read_workspace()
                    reminder = self.item("new-reminder", "Appointment")
                    if due_field == "missing":
                        del reminder["due"]
                    workspace["reminders"].append(reminder)
                    serve.write_workspace(workspace)
                    self.overwrite_bookkeeping()
                    return self.completed()

                process = self.run_agent(fake_agent)

                self.assertEqual(process.call_count, 2)
                self.assert_failed()

    def test_deleting_existing_record_fields_does_not_complete_the_request(self):
        workspace = serve.read_workspace()
        workspace["tasks"][0].update(due="2026-09-30", notes="Keep these existing details.")
        serve.write_workspace(workspace)
        self.originals[self.current_workspace] = self.current_workspace.read_bytes()

        for field in ("due", "notes"):
            with self.subTest(field=field):
                def fake_agent(*args, **kwargs):
                    workspace = serve.read_workspace()
                    del workspace["tasks"][0][field]
                    serve.write_workspace(workspace)
                    self.overwrite_bookkeeping()
                    return self.completed()

                process = self.run_agent(fake_agent)

                self.assertEqual(process.call_count, 2)
                self.assert_failed()

    def test_timestamp_only_edits_do_not_complete_the_request(self):
        for field in ("created", "updated"):
            with self.subTest(field=field):
                def fake_agent(*args, **kwargs):
                    workspace = serve.read_workspace()
                    workspace["tasks"][0][field] = "2026-09-22T10:00:00+08:00"
                    serve.write_workspace(workspace)
                    self.overwrite_bookkeeping()
                    return self.completed()

                process = self.run_agent(fake_agent)

                self.assertEqual(process.call_count, 2)
                self.assert_failed()

    def test_replacing_workspace_root_or_omitting_collections_rolls_back(self):
        for corruption in ("root", "projects", "tasks", "reminders"):
            with self.subTest(corruption=corruption):
                def fake_agent(*args, **kwargs):
                    workspace = serve.read_workspace()
                    if corruption == "root":
                        workspace = []
                    else:
                        del workspace[corruption]
                    serve.atomic_write(self.current_workspace, json.dumps(workspace))
                    self.overwrite_bookkeeping()
                    return self.completed()

                process = self.run_agent(fake_agent)

                self.assertEqual(process.call_count, 2)
                self.assert_failed()

    def test_valid_additions_cannot_hide_removal_of_existing_items(self):
        def fake_agent(*args, **kwargs):
            self.add_items()
            workspace = serve.read_workspace()
            workspace["tasks"] = [item for item in workspace["tasks"]
                                  if item["id"] != "existing-task"]
            serve.write_workspace(workspace)
            self.overwrite_bookkeeping()
            return self.completed()

        process = self.run_agent(fake_agent)

        self.assertEqual(process.call_count, 2)
        self.assert_failed()

    def test_legacy_reminder_without_date_does_not_block_new_items(self):
        workspace = serve.read_workspace()
        legacy = self.item("legacy-reminder", "Existing undated reminder")
        workspace["reminders"].append(legacy)
        self.seed(workspace)
        self.originals[self.current_workspace] = self.current_workspace.read_bytes()

        def fake_agent(*args, **kwargs):
            self.add_items()
            return self.completed()

        process = self.run_agent(fake_agent)

        self.assertEqual(process.call_count, 1)
        self.assertEqual(serve.read_status()["state"], "done")
        self.assertEqual(serve.read_workspace()["reminders"][0], legacy)
        self.assert_archived_once()

    def test_legacy_reminder_without_date_can_be_completed(self):
        workspace = serve.read_workspace()
        workspace["reminders"].append(self.item("legacy-reminder", "Existing undated reminder"))
        self.seed(workspace)
        self.originals[self.current_workspace] = self.current_workspace.read_bytes()

        def fake_agent(*args, **kwargs):
            workspace = serve.read_workspace()
            workspace["reminders"][0]["status"] = "done"
            serve.write_workspace(workspace)
            return self.completed("Completed the existing reminder.")

        process = self.run_agent(fake_agent)

        self.assertEqual(process.call_count, 1)
        self.assertEqual(serve.read_status()["state"], "done")
        self.assertEqual(serve.read_workspace()["reminders"][0]["status"], "done")
        self.assertIsNone(serve.read_workspace()["reminders"][0]["due"])
        self.assert_archived_once()

    def test_malformed_workspace_write_rolls_back_all_files(self):
        def fake_agent(*args, **kwargs):
            serve.atomic_write(self.current_workspace, '{"tasks": [')
            self.overwrite_bookkeeping()
            return self.completed()

        self.run_agent(fake_agent)

        self.assert_failed()

    def test_nonzero_exit_rolls_back_even_valid_workspace_additions(self):
        def fake_agent(*args, **kwargs):
            self.add_items()
            self.overwrite_bookkeeping()
            return self.completed(returncode=1)

        self.run_agent(fake_agent)

        self.assert_failed()

    def test_timeout_rolls_back_partial_agent_writes(self):
        def fake_agent(*args, **kwargs):
            self.add_items()
            self.overwrite_bookkeeping()
            raise subprocess.TimeoutExpired(["fake-agent"], 900)

        self.run_agent(fake_agent)

        self.assert_failed()

    def test_note_arriving_during_success_remains_pending_for_the_next_run(self):
        pending_note = "A second independent note arriving during processing."

        def fake_agent(*args, **kwargs):
            serve.append_pending_inbox(pending_note)
            self.add_items()
            self.overwrite_bookkeeping()
            return self.completed()

        self.run_agent(fake_agent)

        self.assertEqual(serve.read_status()["state"], "done")
        self.assert_archived_once()
        self.assertIn(pending_note, serve.INBOX_PENDING.read_text(encoding="utf-8"))
        self.assertNotIn(pending_note, serve.ARCHIVE.read_text(encoding="utf-8"))
        self.assertTrue(serve.stage_pending_inbox())
        self.assertIn(pending_note, serve.INBOX.read_text(encoding="utf-8"))

    def test_note_arriving_during_failure_is_preserved_with_original_input(self):
        pending_note = "Do not lose the note that arrived after processing started."
        attempts = 0

        def fake_agent(*args, **kwargs):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                serve.append_pending_inbox(pending_note)
            self.overwrite_bookkeeping()
            return self.completed()

        self.run_agent(fake_agent)

        self.assert_failed()
        self.assertIn(pending_note, serve.INBOX_PENDING.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
