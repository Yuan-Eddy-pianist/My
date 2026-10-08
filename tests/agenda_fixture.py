"""Read-only owner sources copied into a fully isolated fixture home."""
import os
from pathlib import Path
import shutil
import unittest

from context_fixture import create_context
from agenda_requests import AgendaRequests


def fixture(root, transcribe=lambda path: '合成语音'):
    store = create_context(root, {'projects': [], 'tasks': [], 'reminders': []})
    source = os.environ.get('MY_AGENDA_TEST_INBOX_ROOT')
    if not source:
        raise unittest.SkipTest('Set MY_AGENDA_TEST_INBOX_ROOT to read-only Firstmate owner sources')
    (store.home / 'bin').mkdir()
    for name in ('fm-inbox.sh', 'fm-wake-lib.sh', 'fm-path-lib.sh'):
        shutil.copyfile(Path(source) / 'bin' / name, store.home / 'bin' / name)
    outbox = AgendaRequests(root / 'data/.agenda-requests', store.home, transcribe)
    return store, outbox


def note(outbox, identity):
    return outbox.read(outbox.folder(identity))


def reply(outbox, identity, outcome='applied', summary='已更新。', request_identity=None):
    import json
    record = note(outbox, identity)
    payload = {'schema': 'my-agenda-outcome.v1', 'requestId': request_identity or identity,
               'outcome': outcome, 'summary': summary}
    outbox.call('reply', '--json', record['inboxId'], '-', body=json.dumps(payload, ensure_ascii=False))
    ack(outbox, record['inboxId'])


def ack(outbox, inbox_id):
    import subprocess
    subprocess.run(['bash', str(outbox.home / 'bin/fm-inbox.sh'), 'drain', '--ack', inbox_id],
                   check=True, capture_output=True, env=outbox.env())
