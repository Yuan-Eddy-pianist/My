"""Synthetic browser acceptance server; never invokes a mic, model or live home.

Run with MY_AGENDA_TEST_INBOX_ROOT pointing to read-only owner script sources.
Control endpoints exist ONLY in this fixture, not in serve.py.
"""
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import serve
from agenda_fixture import fixture, note, reply


def main():
    with tempfile.TemporaryDirectory(prefix='my-agenda-browser-') as temporary:
        root = Path(temporary)
        store, outbox = fixture(root, lambda path: '合成语音：提醒我周五买牛奶。')
        serve.DATA = root / 'data'
        serve.INBOX = serve.DATA / 'inbox.md'
        serve.INBOX_PENDING = serve.DATA / '.inbox-pending.md'
        serve.ARCHIVE = serve.DATA / 'inbox-archive.md'
        serve.STATUS = serve.DATA / '.agent-status.json'
        serve.transcribe_path = outbox.transcribe
        serve.start_agenda_worker = lambda: None  # Explicit fixture ticks only.
        serve.ensure_data()

        class FixtureHandler(serve.Handler):
            lose_next_upload = False

            def do_POST(self):
                if self.path.startswith('/fixture/'):
                    payload = self._read_json()
                    if self.path == '/fixture/tick':
                        outbox.tick()
                    elif self.path == '/fixture/reply':
                        reply(outbox, payload['requestId'], payload['outcome'], payload['summary'])
                        outbox.tick()
                    elif self.path == '/fixture/offline':
                        script = store.home / 'bin/fm-inbox.sh'
                        if payload['offline'] and script.exists():
                            script.rename(script.with_suffix('.off'))
                        elif not payload['offline'] and script.with_suffix('.off').exists():
                            script.with_suffix('.off').rename(script)
                    elif self.path == '/fixture/lose-upload-response':
                        FixtureHandler.lose_next_upload = True
                    self._send_json(200, outbox.snapshot())
                    return
                if self.path == '/api/voice' and FixtureHandler.lose_next_upload:
                    FixtureHandler.lose_next_upload = False
                    # Accepted durably but the browser never receives a successful response.
                    serve.enqueue_voice(self._read_body(), self.headers.get('X-Filename', 'audio.webm'),
                                        self.headers.get('X-Request-ID'))
                    self._send_json(503, {'error': 'synthetic lost response'})
                    return
                super().do_POST()

        server = serve.ThreadingHTTPServer(('127.0.0.1', 0), FixtureHandler)
        print(json.dumps({'url': 'http://127.0.0.1:' + str(server.server_address[1])}), flush=True)
        try:
            server.serve_forever()
        finally:
            server.server_close()


if __name__ == '__main__':
    main()
