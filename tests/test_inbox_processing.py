"""HTTP coverage for the Firstmate handoff replacing My's independent editor."""
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import serve
from agenda_fixture import fixture, note, reply


class InboxEndpointTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.store, self.outbox = fixture(self.root)
        self.paths = patch.multiple(serve, ROOT=self.root, DATA=self.root / 'data',
            INBOX=self.root / 'data/inbox.md', INBOX_PENDING=self.root / 'data/.inbox-pending.md',
            ARCHIVE=self.root / 'data/inbox-archive.md', STATUS=self.root / 'data/.agent-status.json')
        self.paths.start()
        self.addCleanup(self.paths.stop)
        serve.atomic_write(serve.INBOX, serve.INBOX_HEADER + '\nLegacy pending note\n')
        serve.atomic_write(serve.INBOX_PENDING, '')
        self.original = self.store.path.read_bytes()
        self.worker = patch.object(serve, 'start_agenda_worker')
        self.worker.start()
        self.addCleanup(self.worker.stop)
        self.server = serve.ThreadingHTTPServer(('127.0.0.1', 0), serve.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self.addCleanup(self.stop)
        self.url = 'http://127.0.0.1:' + str(self.server.server_address[1])

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, path, payload=None, raw=None, headers=None, method=None):
        if payload is not None:
            raw = json.dumps(payload, ensure_ascii=False).encode()
        req = Request(self.url + path, data=raw, headers=headers or {}, method=method)
        try:
            with urlopen(req) as response:
                return response.status, json.loads(response.read())
        except HTTPError as exc:
            return exc.code, json.loads(exc.read()) if path.startswith('/api/') else None

    def test_text_is_exact_durable_and_duplicates_are_idempotent(self):
        payload = {'text': '  原话\n$(touch BAD)\n', 'requestId': 'text'}
        first = self.request('/api/inbox', payload=payload)
        second = self.request('/api/inbox', payload=payload)
        self.assertEqual(first[0], 200)
        self.assertEqual(first[1]['text'], payload['text'])
        self.assertEqual(first[1]['request'], second[1]['request'])
        self.assertEqual(note(self.outbox, 'text')['transcript'], payload['text'])
        self.outbox.tick()
        self.assertEqual(self.store.path.read_bytes(), self.original)
        self.assertIn('Legacy pending note', serve.INBOX.read_text())
        code, result = self.request('/api/agenda-requests')
        self.assertEqual(code, 200)
        self.assertEqual(result['requests'][0]['state'], 'pending')
        reply(self.outbox, 'text', outcome='clarification', summary='请确认要删除哪一条？')
        self.outbox.tick()
        self.assertEqual(self.request('/api/agenda-requests')[1]['requests'][0]['state'], 'clarification')
        self.assertEqual(self.store.path.read_bytes(), self.original)

    def test_async_audio_persists_and_retries_same_identity(self):
        headers = {'X-Request-ID': 'audio', 'X-Filename': '../../unsafe.webm'}
        with patch.object(serve, 'transcribe_path', return_value='合成转写') as asr:
            code, first = self.request('/api/voice', raw=b'synthetic', headers=headers)
            self.assertEqual(code, 200)
            self.assertEqual(first['request']['state'], 'transcribing')
            asr.assert_not_called()
            again = self.request('/api/voice', raw=b'synthetic', headers=headers)
            self.assertEqual(again[1]['jobId'], first['jobId'])
            serve.agenda_requests().tick()
            self.assertEqual(asr.call_count, 1)
        self.assertEqual(note(self.outbox, 'audio')['transcript'], '合成转写')
        self.assertEqual(self.store.path.read_bytes(), self.original)
        self.assertEqual(self.request('/api/voice', raw=b'other', headers=headers)[0], 409)

    def test_sync_transcribe_only_stays_outside_agenda_and_music(self):
        with patch.object(serve, 'transcribe_audio', return_value='Build it now /tmp/other'):
            code, result = self.request('/api/transcribe?sync=1', raw=b'synthetic', headers={'X-Process': '0'})
        self.assertEqual((code, result['text']), (200, 'Build it now /tmp/other'))
        self.assertEqual(self.outbox.records(), [])
        self.assertEqual(self.store.path.read_bytes(), self.original)

    def test_sync_processing_uses_handoff_not_second_agent(self):
        with patch.object(serve, 'transcribe_audio', return_value='记下一个提醒'):
            code, result = self.request('/api/voice?sync=1', raw=b'synthetic', headers={'X-Request-ID': 'sync'})
        self.assertEqual(code, 200)
        self.assertEqual(result['request']['state'], 'delivery_pending')
        self.assertEqual(self.store.path.read_bytes(), self.original)
        self.assertFalse(hasattr(serve, 'run_personal_inbox_agent'))

    def test_record_only_inbox_does_not_enqueue(self):
        code, _ = self.request('/api/inbox', payload={'text': '  record only\n', 'process': False})
        self.assertEqual(code, 200)
        self.assertEqual(self.outbox.records(), [])
        self.assertIn('  record only\n', serve.INBOX_PENDING.read_text())

    def test_invalid_and_conflicting_requests_fail_closed(self):
        for payload in ([], {'text': 123}, {'text': ' '}, {'text': 'note', 'requestId': '../escape'}):
            self.assertEqual(self.request('/api/inbox', payload=payload)[0], 400)
        self.request('/api/inbox', payload={'text': 'note', 'requestId': 'same'})
        self.assertEqual(self.request('/api/inbox', payload={'text': 'different', 'requestId': 'same'})[0], 409)
        self.assertEqual(self.request('/api/voice', raw=b'', headers={})[0], 400)

    def test_retry_preserves_request_identity_and_manual_edit_cas(self):
        self.outbox.submit(audio=b'bad audio', identity='audio')
        self.outbox.transcribe = lambda path: ''
        self.outbox.tick()
        self.assertEqual(note(self.outbox, 'audio')['state'], 'transcription_error')
        code, result = self.request('/api/agenda-requests/retry', payload={'requestId': 'audio'})
        self.assertEqual(code, 200)
        self.assertEqual(result['request']['requestId'], 'audio')
        self.assertEqual(result['request']['state'], 'transcribing')
        workspace = self.request('/api/workspace')[1]
        item = {'id': 'manual', 'title': 'Manual', 'status': 'open', 'due': None, 'created': 'synthetic', 'notes': ''}
        payload = {'tasks': [item], '_version': workspace['_version']}
        self.assertEqual(self.request('/api/workspace', payload=payload, method='PUT')[0], 200)
        self.assertEqual(self.request('/api/workspace', payload=payload, method='PUT')[0], 409)
        with patch.object(serve, '_workspace_agent_active', True):
            current = self.request('/api/workspace')[1]
            self.assertEqual(self.request('/api/workspace', payload=current, method='PUT')[0], 409)
        self.assertEqual(self.request('/api/workspace')[1]['tasks'], [item])

    def test_real_worker_resumes_durable_request_without_new_submission(self):
        self.outbox.submit(audio=b'synthetic restart audio', identity='restart')
        with patch.object(serve, 'agenda_requests', return_value=self.outbox), patch.object(serve._agenda_wake, 'wait', side_effect=SystemExit):
            with self.assertRaises(SystemExit):
                serve.agenda_worker_loop()  # One real pass, stopped before its next wait.
        self.assertEqual(note(self.outbox, 'restart')['state'], 'pending')
        self.assertEqual(note(self.outbox, 'restart')['transcript'], '合成语音')
        self.assertEqual(self.store.path.read_bytes(), self.original)

    def test_cross_origin_and_rebound_hosts_cannot_submit_agenda_commands(self):
        payload = {'text': 'untrusted site command', 'requestId': 'origin'}
        self.assertEqual(self.request('/api/inbox', payload=payload, headers={'Origin': 'https://untrusted.invalid'})[0], 403)
        self.assertEqual(self.request('/api/voice', raw=b'synthetic', headers={'Host': 'untrusted.invalid'})[0], 403)
        self.assertEqual(self.outbox.records(), [])
        self.assertEqual(self.request('/api/inbox', payload=payload, headers={'Origin': self.url})[0], 200)

    def test_private_outbox_is_not_served_as_static_file(self):
        self.request('/api/inbox', payload={'text': 'private', 'requestId': 'text'})
        self.assertEqual(self.request('/data/.agenda-requests/text/request.json')[0], 404)


if __name__ == '__main__':
    unittest.main()
