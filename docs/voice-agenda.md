# Local voice agenda requests

The browser microphone flow uses the existing local Whisper implementation.
My saves a durable request, then calls the **existing Firstmate** `fm-inbox.sh
note --request-id --json -` owner. My no longer launches an independent agenda
editing agent. Daily project-progress inspection and manual dashboard editors
are unchanged. The separate music inspiration shortcut remains notebook-only.

## Prerequisites and scope

Use the existing `data/.firstmate-context.json` binding and the bound home's
`bin/fm-inbox.sh`. Firstmate must have its existing `personal_context_read` and
`personal_context_update` tools loaded. No new model, service, framework, project
registration, or external transcription API is introduced by this handoff.

Every request has a fixed trusted agenda-only instruction followed by one JSON
object containing the exact, quoted ASR transcript. Dictation never selects a
home, executable, shell command, configuration path or delivery destination.
Firstmate interprets it as personal-agenda data, not permission to execute work.
It must preserve projects long-term; delete only confirmed completed personal
tasks / one-off reminders; and ask for clarification when ASR or the target is
ambiguous. No personal-context snapshot belongs in its reply.

The inbox is a natural-language interface, not a typed policy sandbox. These
scope rules must be followed by primary Firstmate; quoting alone cannot enforce
an agent's interpretation. Manual editors still participate in the same existing
file lock and version check. A concurrent edit requires a fresh read/reconsider.

## Capture, recovery and feedback

- Successful upload means **saved locally**, not applied. Local audio survives
  transcription errors and server restarts. After the exact transcript is durable,
  the worker removes the audio; cleanup failure may leave a retained recording.
- Requests and outcomes are private local files in `data/.agenda-requests/`,
  ignored by Git and refused by the static-file server. They are retained for
  recovery; this change does not introduce automatic transcript-history deletion.
- Delivery retries automatically while My runs. Missing inbox owner, wake failure
  (exit 3), or unknown delivery result preserve the same identity and body. The
  owner's replay contract yields the original note, not a second agenda request.
- A stopped Firstmate may still receive a durable pending note. Announcement and
  acknowledgment do **not** mean agenda changes were applied.
- Firstmate publishes a concise durable result with `fm-inbox.sh reply <note-id> -`,
  then acknowledges that note using `drain --ack`. The body is a JSON object:

```json
{"schema":"my-agenda-outcome.v1","requestId":"the My request ID","outcome":"applied","summary":"One short line in the user's language."}
```

  Outcomes are `applied`, `no_change`, `clarification`, or `rejected`. The summary
  is at most 240 characters and one line. Only an actual confirmed tool change
  merits `applied`. Wrong-request, malformed or unstructured replies do not show
  success; the UI says the outcome is not confirmed.
- The UI distinguishes transcription, local delivery pending, Firstmate pending /
  received, applied, no-change and clarification. Recent request summaries are
  available in the expandable history; confirmed outcomes refresh dashboard lists.
- If an upload response is lost, keep that page open and click **重试**. The browser
  retains that blob and uses its original ID. Do not create a second recording as
  a retry. Before confirmed upload, the browser copy is in memory only and closing
  the page can lose an unsent recording. Accepted server requests survive reloads.
- An ASR error exposes **重试** for the retained server recording. Pending delivery
  already retries automatically. Browser polling is bounded to five minutes;
  refocusing/reopening the page resumes status checks without resubmitting input.

Inbox delivery is idempotent. This is **not** a new transactional exactly-once
agenda editor: the current personal-context tools do not persist a request-ID
ledger atomically with an edit. Firstmate must reconcile current records if it
crashes after an edit but before its reply. Stronger receiver-side crash guarantees
would require a separately reviewed tool/receiver change, not raw agenda writes
or a second editing agent.

## API

- `POST /api/voice` (also `/api/transcribe`): audio body, `X-Request-ID` stable ID,
  optional `X-Filename` for media suffix. Returns a locally saved request.
- `POST /api/inbox`: `{text, requestId, process:true}` submits exact text to the
  same owner. `process:false` still records only in the old pending inbox; it
  does not dispatch. Legacy pending notes are preserved, not silently migrated.
- `GET /api/agenda-requests`: latest 20 requests and total pending count.
- `POST /api/agenda-requests/retry`: `{requestId}` retries retained ASR audio or
  wakes delivery using the existing identity. A different body with an existing
  identity returns 409; unsafe identities and empty input are refused.
- Synchronous `?sync=1` plus `X-Process: 0` remains transcription-only, with no
  agenda handoff. It does not change the separate music shortcut's behavior.
- These POST paths require a local My Host and reject foreign browser Origins.
  This guard is not a general authentication redesign of older dashboard APIs.
  `/api/agent` remains the separate project-progress job status.

## Focused synthetic validation

```sh
MY_AGENDA_TEST_INBOX_ROOT=/absolute/read-only/firstmate \
  python3 -m unittest discover -s tests -p test_agenda_requests.py
MY_AGENDA_TEST_INBOX_ROOT=/absolute/read-only/firstmate \
  python3 -m unittest discover -s tests -p test_inbox_processing.py
python3 -m unittest discover -s tests -p test_serve.py
node --check --input-type=module < app/app.js
```

Tests copy the unchanged inbox/wake/path owner scripts to temporary homes. No live
inbox, microphone, real agenda or model is used. `tests/voice_browser_fixture.py`
serves the real UI against a temporary agenda/outbox with synthetic transcription
and fixture-only delivery/reply controls. It never starts primary Firstmate.

Live acceptance still needs a user-controlled microphone test and primary
Firstmate consumption: correct recognition, target clarification, confirmed edit
and language-preserving concise reply, retained projects, confirmed task/reminder
cleanup, offline recovery, and manual-edit conflicts. Synthetic receiver/tool
fixtures test plumbing/CAS, not a model's semantic judgment or prompt-injection
resistance. Do not infer live activation from the tests.
