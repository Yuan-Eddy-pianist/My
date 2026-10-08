#!/usr/bin/env python3
"""Local My server: static UI, local Whisper STT, inbox + my-agent."""

from __future__ import annotations

import json
import mimetypes
import os
import platform
import queue
import shutil
import subprocess
import tempfile
import threading
import traceback
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from project_progress import add_progress, clean_progress, inspect_project
from firstmate_context import ContextStore, ContextError, ContextConflict

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
INBOX = DATA / "inbox.md"
INBOX_PENDING = DATA / ".inbox-pending.md"
ARCHIVE = DATA / "inbox-archive.md"
STATUS = DATA / ".agent-status.json"
PROGRESS_STATE = DATA / ".project-progress.json"
ENV_FILE = ROOT / ".env"
HOST = "127.0.0.1"
PORT = 8765
INBOX_HEADER = "# Inbox\n\nVoice notes land here and are processed automatically.\n"


def load_dotenv(path: Path = ENV_FILE) -> None:
    """Load KEY=VALUE pairs from .env into os.environ (does not override existing)."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


load_dotenv()

AGENT_PROMPT = """You are the My workspace inbox processor.

Temporary proposal file: data/proposal.json with three arrays. This scratch file is not the durable store; the server validates and commits it to Firstmate after you finish:
- projects: longer-term work, each with a linked local directory (path)
- tasks: short-term to-dos
- reminders: date-based nudges (birthdays, appointments, "remind me on …")

1. Read data/inbox.md (raw speech-to-text; often imperfect).
2. Classify each clear item (skip greetings, filler, tests, garbled ASR):
   - reminder → due date matters more than a work action (birthdays, appointments, "remind me")
   - short-term task → concrete action for the next few days
   - project update → mentions an existing project by name/title, or asks to track long-term work
   - new project → ONLY if the user clearly names a long-term project AND gives an absolute
     local path (e.g. /Users/…). Never invent paths. If they want a project but give no path,
     put a short-term task instead noting "needs project path".
   - heavy request → anything requiring multi-step execution (writing reports/周报,
     inspecting multiple repos, code changes). DO NOT execute it. Record it as a task
     whose title summarizes the request, and move on. Keep total runtime under 2 minutes.
3. For project updates on an existing project with a path:
   - Read that directory lightly (README, recent git log if .git exists, recent file mtimes)
     to ground a short progress note. Sandbox is disabled so those paths are readable.
   - Update the matching project's progress / status / goal fields; set updated to now.
4. Field shapes (keep existing ids; invent short unique ids for new items):
   - project: id, title, path (absolute string), status ("active"|"paused"|"done"),
     goal (string), progress (string), created (ISO), updated (ISO)
   - task: id, title, due (YYYY-MM-DD|null), status ("open"|"done"), created (ISO), notes
   - reminder: id, title, due (YYYY-MM-DD), status ("open"|"done"), created (ISO), notes
   When fixing obvious ASR typos in titles, just write the corrected title. NEVER put ASR
   correction chatter in notes (no "ASR：闲语→闲鱼", no "ASR: x -> y", no "heard as…").
   Leave notes empty unless there is real user context beyond the title.
5. First READ data/proposal.json, then write the merged result back with the write tool:
   keep every existing item, merge new/changed items; do not duplicate clearly identical
   open items; preserve projects/tasks/reminders keys even if empty; pretty JSON
   (2-space indent). NEVER write proposal.json from scratch — it holds all existing data.
   If you classified ANY item into tasks/reminders/projects, you MUST write
   data/proposal.json in this run. Claiming you created a task/reminder without actually
   writing the file is a FAILED run. If every item was filler/tests, skip this write.
6. NEVER edit data/inbox.md or data/inbox-archive.md. The server verifies your
   workspace changes, then appends the original note to the archive and clears the
   inbox. Only write data/proposal.json.
7. Do not ask questions. Do not edit app/, serve.py, or schedule/.
8. Reply with one short line summarizing what you actually saved. If ALL notes are
   filler/tests with no actionable items, reply exactly "No clear items; archived only."
   If ALL requested items already exist unchanged, reply exactly
   "No changes; items already exist." Never use either response for an unsaved item.
"""

PROGRESS_JOB = "project-progress"

_job_queue: queue.Queue[tuple | None] = queue.Queue()
_voice_queue: queue.Queue[dict | None] = queue.Queue()
_status_lock = threading.Lock()
_inbox_lock = threading.Lock()
_workspace_lock = threading.RLock()
_worker_start_lock = threading.Lock()
_workspace_agent_active = False
_worker_started = False
_voice_worker_started = False
_whisper_model = None
_whisper_lock = threading.Lock()
_voice_pending = 0
_job_seq = 0


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class WorkspaceDataError(RuntimeError):
    """The persisted workspace exists but is not valid JSON."""


class WorkspaceConflict(RuntimeError):
    """A client attempted to replace a workspace version it did not read."""


class WorkspaceBusy(RuntimeError):
    """The agent currently owns the workspace update transaction."""


def atomic_write(path: Path, content: str | bytes) -> None:
    """Durably replace a file so readers see either the old or new contents."""
    path.parent.mkdir(parents=True, exist_ok=True)
    binary = isinstance(content, bytes)
    mode = "wb" if binary else "w"
    kwargs = {} if binary else {"encoding": "utf-8"}
    tmp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode=mode,
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
            **kwargs,
        ) as tmp:
            tmp_name = tmp.name
            tmp.write(content)
            tmp.flush()
            os.fsync(tmp.fileno())
        if path.exists():
            os.chmod(tmp_name, path.stat().st_mode & 0o777)
        os.replace(tmp_name, path)
        tmp_name = None
    finally:
        if tmp_name:
            try:
                os.unlink(tmp_name)
            except FileNotFoundError:
                pass


def read_workspace() -> dict:
    with _workspace_lock:
        personal = personal_snapshot()
        return {**personal['workspace'], '_version': personal['version']}


def read_workspace_snapshot() -> dict:
    return {**read_workspace(), '_owner': 'Firstmate'}


def write_workspace(payload: dict) -> dict:
    result = personal_replace(payload, payload.get('_version'))
    return {**result['workspace'], '_version': result['version']}


def update_workspace(payload: dict, expected_version: object) -> tuple[dict, str]:
    """Commit browser edits only to the Firstmate-owned, versioned store."""
    with _workspace_lock:
        if _workspace_agent_active:
            raise WorkspaceBusy("my-agent is updating personal context; retry after it finishes")
        result = personal_replace(payload, expected_version)
        return result['workspace'], result['version']


def personal_store():
    marker = DATA / '.firstmate-context.json'
    if not marker.exists():
        raise WorkspaceDataError('Firstmate context binding is missing; legacy dashboard storage is retired')
    try:
        config = json.loads(marker.read_text())
        if config != {'schema': 1, 'home': '../agent-workflow/firstmate'}:
            raise ValueError('Unsupported Firstmate context binding')
        return ContextStore(DATA / config['home'])
    except (OSError, ValueError) as exc:
        raise WorkspaceDataError(f'Invalid Firstmate context binding: {exc}') from exc


def personal_snapshot():
    store = personal_store()
    try:
        return store.snapshot()
    except (ContextError, OSError) as exc:
        raise WorkspaceDataError(str(exc)) from exc


def personal_replace(payload, version):
    try:
        return personal_store().replace(payload, version)
    except ContextConflict as exc:
        raise WorkspaceConflict(str(exc)) from exc
    except (ContextError, OSError) as exc:
        raise WorkspaceDataError(str(exc)) from exc


def append_pending_inbox(text: str) -> None:
    """Persist a note somewhere the active agent never resets."""
    block = f"\n## {now_iso()}\n\n{text}\n"
    with _inbox_lock:
        previous = INBOX_PENDING.read_text(encoding="utf-8") if INBOX_PENDING.exists() else ""
        atomic_write(INBOX_PENDING, previous + block)


def stage_pending_inbox() -> bool:
    """Move queued notes into the agent-visible inbox immediately before a run."""
    with _inbox_lock:
        pending = INBOX_PENDING.read_text(encoding="utf-8") if INBOX_PENDING.exists() else ""
        if not pending.strip():
            return False
        current = INBOX.read_text(encoding="utf-8") if INBOX.exists() else INBOX_HEADER
        atomic_write(INBOX, current.rstrip() + "\n" + pending)
        # Write the inbox first: a crash can duplicate a note, but cannot lose it.
        atomic_write(INBOX_PENDING, "")
        return True


def read_visible_inbox() -> str:
    with _inbox_lock:
        current = INBOX.read_text(encoding="utf-8") if INBOX.exists() else INBOX_HEADER
        pending = INBOX_PENDING.read_text(encoding="utf-8") if INBOX_PENDING.exists() else ""
        return current.rstrip() + ("\n" + pending if pending else "\n")


def path_info(raw: str) -> dict:
    """Describe a linked project directory for the UI / agent."""
    text = (raw or "").strip()
    if not text:
        return {"ok": False, "path": "", "exists": False, "isDir": False, "error": "path required"}
    path = Path(text).expanduser()
    try:
        resolved = path.resolve()
    except OSError as exc:
        return {
            "ok": False,
            "path": text,
            "exists": False,
            "isDir": False,
            "error": str(exc),
        }
    exists = resolved.exists()
    is_dir = resolved.is_dir()
    return {
        "ok": exists and is_dir,
        "path": str(resolved),
        "exists": exists,
        "isDir": is_dir,
        "error": None if (exists and is_dir) else ("not a directory" if exists else "not found"),
    }


def ensure_data() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "daily").mkdir(exist_ok=True)
    (DATA / "weekly").mkdir(exist_ok=True)
    (DATA / "tmp").mkdir(exist_ok=True)
    if not INBOX.exists():
        atomic_write(INBOX, INBOX_HEADER)
    if not INBOX_PENDING.exists():
        atomic_write(INBOX_PENDING, "")
    if not ARCHIVE.exists():
        atomic_write(ARCHIVE, "# Inbox archive\n")
    personal_snapshot()  # Required sole owner; never create a replacement store.
    if not STATUS.exists():
        write_status("idle", "Ready for voice input.")


def write_status(state: str, message: str, **extra: object) -> dict:
    with _status_lock:
        prev = {}
        if STATUS.exists():
            try:
                prev = json.loads(STATUS.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                prev = {}
        payload = {
            **prev,
            "state": state,
            "message": message,
            "updatedAt": now_iso(),
            "voicePending": _voice_pending,
            "agentPending": _job_queue.qsize(),
            **extra,
        }
        STATUS.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return payload


def read_status() -> dict:
    with _status_lock:
        if not STATUS.exists():
            return {
                "state": "idle",
                "message": "Ready.",
                "updatedAt": now_iso(),
                "voicePending": _voice_pending,
                "agentPending": _job_queue.qsize(),
            }
        try:
            data = json.loads(STATUS.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {"state": "idle", "message": "Ready.", "updatedAt": now_iso()}
        data["voicePending"] = _voice_pending
        data["agentPending"] = _job_queue.qsize()
        return data


# Mac note: CUDA is NVIDIA-only. On Apple Silicon we use MLX (Metal GPU).
# Override with MY_WHISPER_BACKEND=mlx|faster|auto and MY_WHISPER_MODEL=...
_IS_APPLE_SILICON = platform.system() == "Darwin" and platform.machine() == "arm64"
# medium quality on Metal (what you liked); turbo/large is bigger & often slower to start.
_DEFAULT_MLX_MODEL = "mlx-community/whisper-medium-mlx"
_DEFAULT_FASTER_MODEL = "medium"


def _hf_cache_has(repo: str) -> bool:
    """True if HF cache looks complete (has a sizable weight file)."""
    name = "models--" + repo.replace("/", "--")
    root = Path.home() / ".cache" / "huggingface" / "hub" / name
    if not root.is_dir():
        return False
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in {".safetensors", ".npz", ".bin", ".pt", ".npz4bit"}:
            try:
                if path.stat().st_size > 50_000_000:  # >50MB
                    return True
            except OSError:
                continue
    return False


def _resolve_backend() -> str:
    choice = (os.environ.get("MY_WHISPER_BACKEND") or "auto").strip().lower()
    if choice in ("mlx", "faster"):
        return choice
    if not _IS_APPLE_SILICON:
        return "faster"
    # Prefer MLX on Apple Silicon; if the chosen model isn't cached yet, fall back.
    mlx_model = os.environ.get("MY_WHISPER_MODEL", _DEFAULT_MLX_MODEL)
    if not ("/" in mlx_model or "mlx" in mlx_model.lower()):
        mlx_model = _DEFAULT_MLX_MODEL
    return "mlx" if _hf_cache_has(mlx_model) else "faster"


WHISPER_BACKEND = _resolve_backend()
WHISPER_MODEL = os.environ.get(
    "MY_WHISPER_MODEL",
    _DEFAULT_MLX_MODEL if WHISPER_BACKEND == "mlx" else _DEFAULT_FASTER_MODEL,
)
# If auto fell back to faster but env still points at an MLX repo name, use CPU medium.
if WHISPER_BACKEND == "faster" and ("mlx" in WHISPER_MODEL.lower() or "/" in WHISPER_MODEL):
    WHISPER_MODEL = _DEFAULT_FASTER_MODEL

_mlx_ready = False


def get_whisper():
    """faster-whisper CPU fallback (used when MLX unavailable)."""
    global _whisper_model
    with _whisper_lock:
        if _whisper_model is None:
            from faster_whisper import WhisperModel

            model_name = os.environ.get("MY_WHISPER_MODEL", _DEFAULT_FASTER_MODEL)
            if "mlx" in model_name.lower() or "/" in model_name:
                model_name = _DEFAULT_FASTER_MODEL
            print(f"Loading faster-whisper {model_name} on CPU…")
            _whisper_model = WhisperModel(
                model_name, device="cpu", compute_type="int8"
            )
            print("faster-whisper ready.")
        return _whisper_model


def warm_asr() -> None:
    """Load ASR backend once so the first voice note is faster."""
    global _mlx_ready
    if WHISPER_BACKEND == "mlx":
        try:
            import mlx_whisper  # noqa: F401

            # Trigger model download/load with a tiny silent wav via ffmpeg.
            silent = DATA / "tmp" / "warmup-silence.wav"
            silent.parent.mkdir(parents=True, exist_ok=True)
            if not silent.exists():
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-f",
                        "lavfi",
                        "-i",
                        "anullsrc=r=16000:cl=mono",
                        "-t",
                        "0.4",
                        str(silent),
                    ],
                    check=False,
                    capture_output=True,
                )
            if not silent.exists():
                raise RuntimeError("ffmpeg failed to create warmup audio")
            print(f"Loading MLX Whisper on Apple Silicon (Metal): {WHISPER_MODEL}")
            mlx_whisper.transcribe(
                str(silent),
                path_or_hf_repo=WHISPER_MODEL,
                verbose=False,
            )
            _mlx_ready = True
            print("MLX Whisper ready.")
            return
        except Exception as exc:  # noqa: BLE001
            print(f"MLX Whisper failed ({exc}); falling back to faster-whisper CPU.")
    get_whisper()


def transcribe_path_mlx(tmp_path: str) -> str:
    import mlx_whisper

    result = mlx_whisper.transcribe(
        tmp_path,
        path_or_hf_repo=WHISPER_MODEL,
        verbose=False,
        condition_on_previous_text=False,
        initial_prompt="项目、待办、提醒、截止日期。Projects, todos, reminders, deadlines.",
        # fp16 on Apple Silicon Metal
        fp16=True,
    )
    text = (result.get("text") or "").strip()
    if not text:
        # Prefer segment join if top-level text empty.
        segs = result.get("segments") or []
        text = " ".join((s.get("text") or "").strip() for s in segs if s.get("text")).strip()
    if not text:
        raise ValueError(
            "No clear speech detected "
            f"(lang={result.get('language', '?')}, backend=mlx)."
        )
    return text


def transcribe_path_faster(tmp_path: str) -> str:
    model = get_whisper()
    segments, info = model.transcribe(
        tmp_path,
        beam_size=5,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
        language=None,
        condition_on_previous_text=False,
        initial_prompt="项目、待办、提醒、截止日期。Projects, todos, reminders, deadlines.",
    )
    parts: list[str] = []
    for seg in segments:
        text = (seg.text or "").strip()
        if not text:
            continue
        if getattr(seg, "no_speech_prob", 0) > 0.7:
            continue
        if getattr(seg, "avg_logprob", 0) < -1.35:
            continue
        parts.append(text)
    text = " ".join(parts).strip()
    if not text:
        raise ValueError(
            "No clear speech detected "
            f"(lang={getattr(info, 'language', '?')}, backend=faster)."
        )
    return text


def transcribe_path(tmp_path: str) -> str:
    if WHISPER_BACKEND == "mlx":
        try:
            return transcribe_path_mlx(tmp_path)
        except Exception as exc:  # noqa: BLE001
            print(f"MLX transcribe failed ({exc}); trying faster-whisper…")
            return transcribe_path_faster(tmp_path)
    return transcribe_path_faster(tmp_path)


def transcribe_audio(raw: bytes, filename: str = "audio.webm") -> str:
    suffix = Path(filename).suffix or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=DATA / "tmp") as tmp:
        tmp.write(raw)
        tmp_path = tmp.name
    try:
        return transcribe_path(tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


MY_AGENT_DIR = ROOT / "my-agent"
MY_AGENT_ENTRY = MY_AGENT_DIR / "dist" / "index.js"


def verified_inbox_result(before: dict, output: str, workspace_path: Path) -> str:
    """Validate persisted records, and describe changes without trusting agent prose."""
    try:
        after = json.loads(workspace_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WorkspaceDataError(f"Agent did not save a valid workspace: {exc}") from exc
    if not isinstance(after, dict):
        raise WorkspaceDataError("Agent workspace must be a JSON object")
    changes = []
    for key in ("projects", "tasks", "reminders"):
        records = after.get(key)
        if not isinstance(records, list):
            raise WorkspaceDataError(f"Agent workspace is missing the {key} array")
        current = {}
        for item in records:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
                raise WorkspaceDataError(f"Agent saved an invalid {key} record")
            if item["id"] in current:
                raise WorkspaceDataError(f"Agent saved duplicate {key} ids")
            current[item["id"]] = item
        previous = {item["id"]: item for item in before[key]}
        if previous.keys() - current.keys():
            raise WorkspaceDataError(f"Agent removed existing {key}; original data retained")
        added = updated = 0
        for item_id, item in current.items():
            old_item = previous.get(item_id)
            if item == old_item:
                continue
            required = set(old_item) if old_item is not None else (
                {"id", "title", "path", "status", "goal", "progress", "created", "updated"}
                if key == "projects" else {"id", "title", "due", "status", "created", "notes"}
            )
            if required - item.keys():
                raise WorkspaceDataError(f"Agent removed or omitted required {key} fields")
            if not isinstance(item.get("title"), str) or not item["title"].strip():
                raise WorkspaceDataError(f"Agent saved a {key} record without a title")
            allowed_statuses = ("active", "paused", "done") if key == "projects" else ("open", "done")
            if item.get("status") not in allowed_statuses:
                raise WorkspaceDataError(f"Agent saved a {key} record with an invalid status")
            if key == "reminders" and item.get("due") is None and not (
                old_item is not None and "due" in old_item and old_item["due"] is None
            ):
                raise WorkspaceDataError("Agent saved a reminder without a due date")
            if key != "projects" and item.get("due") is not None:
                try:
                    due = item["due"]
                    if not isinstance(due, str) or datetime.strptime(due, "%Y-%m-%d").strftime("%Y-%m-%d") != due:
                        raise ValueError("expected YYYY-MM-DD")
                except ValueError as exc:
                    raise WorkspaceDataError(f"Agent saved an invalid {key} due date") from exc
            if old_item is not None:
                # Refreshing bookkeeping dates alone does not apply an inbox request.
                meaningful_keys = (item.keys() | old_item.keys()) - {"created", "updated"}
                if any(item.get(field) != old_item.get(field) for field in meaningful_keys):
                    updated += 1
            else:
                added += 1
        if added:
            changes.append(f"{added} {key[:-1] if added == 1 else key} added")
        if updated:
            changes.append(f"{updated} {key[:-1] if updated == 1 else key} updated")
    if changes:
        return "Saved: " + ", ".join(changes) + "."
    final_line = output.strip().splitlines()[-1] if output.strip() else ""
    no_changes = {
        "No clear items; archived only.": "No clear items; archived only. No workspace changes.",
        "No changes; items already exist.": "No changes; items already exist. Note archived.",
    }
    if final_line in no_changes:
        return no_changes[final_line]
    raise WorkspaceDataError("Agent reported completion without saving any workspace changes")


def run_personal_inbox_agent(note_preview: str, node: str) -> None:
    """Let voice propose edits in scratch, then commit to Firstmate with CAS.

    A failed or conflicting proposal never restores an old Firstmate snapshot.
    Incoming notes remain queued until the proposal commits successfully.
    """
    global _workspace_agent_active
    with _workspace_lock:
        _workspace_agent_active = True
    try:
        snapshot = personal_snapshot()
        before = snapshot['workspace']
        with _inbox_lock:
            original = INBOX.read_bytes()
        with tempfile.TemporaryDirectory(prefix='my-voice-proposal-') as scratch:
            root = Path(scratch)
            (root / 'data').mkdir()
            proposal = root / 'data/proposal.json'
            prompt = AGENT_PROMPT + f'\nCurrent local date/time: {now_iso()}\n'
            prompt += '\nThis is a temporary proposal workspace. Do not access or edit Firstmate files. The server validates and commits your proposal.\n'
            for attempt in range(2):
                atomic_write(proposal, json.dumps(before, ensure_ascii=False, indent=2) + '\n')
                atomic_write(root / 'data/inbox.md', original)
                write_status('running', 'Processing note into Firstmate personal context…', lastNote=note_preview)
                proc = subprocess.run([node, str(MY_AGENT_ENTRY), prompt], cwd=root,
                    capture_output=True, text=True, timeout=900,
                    env={**os.environ, 'AGENT_WORKSPACE': str(root)})
                out, err = (proc.stdout or '').strip(), (proc.stderr or '').strip()
                if proc.returncode:
                    raise RuntimeError(err or out or 'Voice agent failed')
                try:
                    summary = verified_inbox_result(before, out, proposal)
                except WorkspaceDataError as exc:
                    if attempt == 1:
                        raise
                    prompt += f'\nPrevious proposal was rejected: {exc}. Correct it and save the merged records.\n'
                    continue
                after = json.loads(proposal.read_text())
                if after != before:
                    personal_replace(after, snapshot['version'])
                break
        with _inbox_lock:
            # New incoming notes use INBOX_PENDING; refuse unexpected manual edits.
            if INBOX.read_bytes() != original:
                raise WorkspaceConflict('Inbox changed during processing; context saved, note retained for review')
            body = original.decode().removeprefix(INBOX_HEADER.rstrip()).strip()
            archive = ARCHIVE.read_text() if ARCHIVE.exists() else '# Inbox archive\n'
            if body:
                archive = archive.rstrip() + '\n\n' + body + '\n'
            atomic_write(ARCHIVE, archive)
            atomic_write(INBOX, INBOX_HEADER)
        write_status('done', summary, lastNote=note_preview, lastResult=out[-2000:])
    except Exception as exc:
        write_status('error', f'Note retained; Firstmate context was not rolled back: {str(exc)[-600:]}',
                     lastNote=note_preview)
    finally:
        with _workspace_lock:
            _workspace_agent_active = False


def run_agent_once(
    note_preview: str,
    prompt: str = AGENT_PROMPT,
) -> None:
    global _workspace_agent_active
    node = shutil.which("node")
    if not node:
        write_status(
            "error",
            "Node.js not found. Install Node, then restart serve.py.",
            lastNote=note_preview,
        )
        return
    if not MY_AGENT_ENTRY.is_file():
        write_status(
            "error",
            "my-agent not built. Run `cd my-agent && npm install && npm run build`, then restart serve.py.",
            lastNote=note_preview,
        )
        return

    if prompt == AGENT_PROMPT:
        run_personal_inbox_agent(note_preview, node)
        return

    write_status('error', 'Unsupported job; use the shared personal context update path.', lastNote=note_preview)


def summarize_progress(inspections: list[dict]) -> dict[str, str]:
    evidence = [
        {key: item[key] for key in ("id", "title", "commits")}
        for item in inspections if item["commits"]
    ]
    if not evidence:
        return {}
    entry = MY_AGENT_DIR / "dist" / "summarize.js"
    if not entry.is_file():
        raise RuntimeError("Build the progress summarizer: cd my-agent && npm run build")
    proc = subprocess.run(
        [shutil.which("node") or "node", str(entry)],
        input=json.dumps(evidence, ensure_ascii=False),
        cwd=str(ROOT), capture_output=True, text=True, timeout=900,
    )
    if proc.returncode:
        raise RuntimeError(proc.stderr.strip() or "Progress summarizer failed")
    output = proc.stdout.strip()
    if output.startswith("```"):
        output = "\n".join(output.splitlines()[1:-1])
    summaries = json.loads(output)
    expected = {item["id"] for item in evidence}
    if not isinstance(summaries, dict) or set(summaries) != expected:
        raise ValueError("Progress summary must include every inspected project")
    if any(not isinstance(value, str) or not value.strip() for value in summaries.values()):
        raise ValueError("Progress summaries must be nonempty text")
    return summaries


def run_progress_once(note_preview: str) -> None:
    """Python owns inspection, checkpoints, dates and writes; the LLM summarizes."""
    global _workspace_agent_active
    with _workspace_lock:
        _workspace_agent_active = True
    try:
        write_status("running", "正在检查项目的新提交…", lastNote=note_preview)
        checked_at = now_iso()
        data = read_workspace()
        checkpoints = json.loads(PROGRESS_STATE.read_text()) if PROGRESS_STATE.exists() else {}
        inspections = []
        projects = [p for p in data["projects"] if p.get("status", "active") == "active"]
        for project in projects:
            inspection = inspect_project(project, checkpoints.get(project["id"], {}), checked_at)
            if inspection is not None:
                inspections.append(inspection)
        summaries = summarize_progress(inspections)
        by_id = {item["id"]: item for item in inspections}
        results = []
        for project in projects:
            project["progress"] = clean_progress(project.get("progress", ""))
            item = by_id.get(project["id"])
            if item is None:
                results.append(f"{project['title']}：跳过（目录无效或没有 Git 提交）")
                continue
            summary = summaries.get(project["id"])
            if summary:
                project["progress"] = add_progress(project["progress"], checked_at[:10], summary)
                project["updated"] = checked_at
            checkpoints[project["id"]] = {
                "path": item["path"], "head": item["head"], "checkedAt": checked_at,
            }
            detail = summary or "无新改动"
            if item["dirty"]:
                detail += "；工作区有未提交修改"
            results.append(f"{project['title']}：{detail}")
        write_workspace(data)
        atomic_write(PROGRESS_STATE, json.dumps(checkpoints, indent=2, ensure_ascii=False) + "\n")
        write_status(
            "done", f"已检查 {len(inspections)} 个项目，更新 {len(summaries)} 条进度。",
            lastNote=note_preview, lastResult="\n".join(results),
        )
    except Exception as exc:  # noqa: BLE001
        write_status("error", f"Project progress failed: {exc}", lastNote=note_preview)
    finally:
        with _workspace_lock:
            _workspace_agent_active = False


def run_queued_job(job: tuple) -> None:
    if job[1] == PROGRESS_JOB:
        run_progress_once(job[0])
    else:
        if job[1] == AGENT_PROMPT:
            stage_pending_inbox()
        run_agent_once(*job)


def worker_loop() -> None:
    while True:
        item = _job_queue.get()
        if item is None:
            _job_queue.task_done()
            break
        try:
            # Coalesce queued jobs by prompt: inbox and progress jobs are both
            # idempotent, so only the latest of each kind needs to run.
            jobs: dict[str, tuple] = {item[1]: item}
            while True:
                try:
                    nxt = _job_queue.get_nowait()
                except queue.Empty:
                    break
                if nxt is None:
                    _job_queue.task_done()
                    for job in jobs.values():
                        run_queued_job(job)
                    return
                jobs[nxt[1]] = nxt
                _job_queue.task_done()
            for job in jobs.values():
                run_queued_job(job)
        finally:
            _job_queue.task_done()


def enqueue_process(
    note_preview: str,
    prompt: str = AGENT_PROMPT,
    running_msg: str = "Note saved. Starting my-agent…",
) -> dict:
    global _worker_started
    with _worker_start_lock:
        if not _worker_started:
            _worker_started = True
            t = threading.Thread(target=worker_loop, name="my-agent-worker", daemon=True)
            t.start()
    pending = _job_queue.qsize()
    state = read_status().get("state")
    if state in ("running", "transcribing"):
        status = write_status(
            "queued",
            "Note saved. Waiting for current work to finish…",
            lastNote=note_preview,
        )
    else:
        status = write_status(
            "queued",
            running_msg,
            lastNote=note_preview,
        )
    _job_queue.put((note_preview, prompt))
    status["queueDepth"] = pending + 1
    return status


PROGRESS_HOUR = int(os.environ.get("MY_PROGRESS_HOUR", "18"))
PROGRESS_MINUTE = int(os.environ.get("MY_PROGRESS_MINUTE", "0"))


def enqueue_progress() -> dict:
    """Enqueue a project-progress git inspection job (daily schedule or manual)."""
    return enqueue_process(
        "每日项目进度巡检",
        prompt=PROGRESS_JOB,
        running_msg="正在排队检查项目的新提交…",
    )


def progress_scheduler_loop() -> None:
    """Fire a progress job once per day at PROGRESS_HOUR:PROGRESS_MINUTE local time."""
    last_fired: str | None = None
    while True:
        now = datetime.now()
        today = now.date().isoformat()
        if (now.hour, now.minute) >= (PROGRESS_HOUR, PROGRESS_MINUTE) and last_fired != today:
            last_fired = today
            try:
                enqueue_progress()
            except Exception:  # noqa: BLE001
                traceback.print_exc()
        threading.Event().wait(30)


def inbox_cleared() -> bool:
    """True when inbox.md holds only the canonical header; not proof of a save."""
    try:
        text = INBOX.read_text(encoding="utf-8")
    except OSError:
        return False
    body = text.replace("# Inbox", "").replace(
        "Voice notes land here and are processed automatically.", ""
    )
    return body.strip() == ""


def append_inbox_and_process(text: str) -> dict:
    append_pending_inbox(text)
    preview = text if len(text) <= 120 else text[:117] + "…"
    return {
        "ok": True,
        "text": text,
        # Inbox completion verifies persisted records before archiving the input.
        "agent": enqueue_process(preview),
    }


def voice_worker_loop() -> None:
    global _voice_pending
    while True:
        job = _voice_queue.get()
        if job is None:
            _voice_queue.task_done()
            break
        path = job["path"]
        job_id = job["id"]
        try:
            write_status(
                "transcribing",
                f"Transcribing voice note… ({_voice_pending} in queue incl. current)",
                lastJobId=job_id,
            )
            text = transcribe_path(path)
            result = append_inbox_and_process(text)
            write_status(
                result["agent"].get("state", "queued"),
                f"Heard: {text[:80]}{'…' if len(text) > 80 else ''}",
                lastNote=text[:120],
                lastTranscript=text,
                lastJobId=job_id,
            )
        except Exception as exc:  # noqa: BLE001
            write_status(
                "error",
                f"Voice job failed: {exc}",
                lastJobId=job_id,
                lastResult=traceback.format_exc()[-1500:],
            )
        finally:
            with _status_lock:
                _voice_pending = max(0, _voice_pending - 1)
            try:
                os.unlink(path)
            except OSError:
                pass
            _voice_queue.task_done()


def enqueue_voice(raw: bytes, filename: str = "audio.webm") -> dict:
    global _voice_worker_started, _voice_pending, _job_seq
    if not raw:
        raise ValueError("empty audio body")
    suffix = Path(filename).suffix or ".webm"
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=suffix, dir=DATA / "tmp", prefix="voice-"
    ) as tmp:
        tmp.write(raw)
        tmp_path = tmp.name
    with _status_lock:
        _job_seq += 1
        job_id = f"v{_job_seq}"
        _voice_pending += 1
        pending = _voice_pending
    with _worker_start_lock:
        if not _voice_worker_started:
            _voice_worker_started = True
            t = threading.Thread(target=voice_worker_loop, name="my-voice-worker", daemon=True)
            t.start()
    _voice_queue.put({"id": job_id, "path": tmp_path, "filename": filename})
    status = write_status(
        "queued",
        f"Voice queued ({pending} pending). You can record again now.",
        lastJobId=job_id,
    )
    return {"ok": True, "jobId": job_id, "voicePending": pending, "status": status}


class Handler(BaseHTTPRequestHandler):
    server_version = "MyLocal/1.0"

    def log_message(self, fmt: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, code: int, payload: object) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send(code, raw, "application/json; charset=utf-8")

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        return self.rfile.read(length) if length else b""

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", ""):
            self.send_response(302)
            self.send_header("Location", "/app/index.html")
            self.end_headers()
            return

        if path in ("/api/todos", "/api/workspace"):
            try:
                self._send_json(200, read_workspace_snapshot())
            except WorkspaceDataError as exc:
                self._send_json(500, {"ok": False, "error": str(exc)})
            return

        if path == "/api/path":
            qs = parse_qs(urlparse(self.path).query)
            raw = (qs.get("path") or [""])[0]
            self._send_json(200, path_info(raw))
            return

        if path == "/api/inbox":
            self._send_json(200, {"text": read_visible_inbox()})
            return

        if path == "/api/agent":
            self._send_json(200, read_status())
            return

        if path == "/api/health":
            self._send_json(
                200,
                {
                    "ok": True,
                    "whisper": _mlx_ready or _whisper_model is not None,
                    "whisperBackend": WHISPER_BACKEND,
                    "whisperModel": WHISPER_MODEL,
                    "appleSilicon": _IS_APPLE_SILICON,
                    "agent": MY_AGENT_ENTRY.is_file(),
                    "voicePending": _voice_pending,
                },
            )
            return

        rel = path.lstrip("/")
        file_path = (ROOT / rel).resolve()
        if not str(file_path).startswith(str(ROOT)) or not file_path.is_file():
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return

        ctype = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in (
            "application/javascript",
            "application/json",
        ):
            ctype = f"{ctype}; charset=utf-8"
        self._send(200, file_path.read_bytes(), ctype)

    def do_POST(self) -> None:
        path = urlparse(self.path).path

        if path in ("/api/voice", "/api/transcribe"):
            # Async by default: save audio, return immediately, process in background.
            # ?sync=1 keeps the old blocking transcribe behavior for debugging.
            raw = self._read_body()
            if not raw:
                self._send_json(400, {"ok": False, "error": "empty audio body"})
                return
            filename = self.headers.get("X-Filename", "audio.webm")
            qs = urlparse(self.path).query
            sync = "sync=1" in qs or self.headers.get("X-Sync") == "1"
            if sync:
                process = self.headers.get("X-Process", "1") != "0"
                try:
                    text = transcribe_audio(raw, filename)
                except Exception as exc:  # noqa: BLE001
                    self._send_json(500, {"ok": False, "error": str(exc)})
                    return
                if process:
                    self._send_json(200, append_inbox_and_process(text))
                else:
                    self._send_json(200, {"ok": True, "text": text})
                return
            try:
                self._send_json(200, enqueue_voice(raw, filename))
            except Exception as exc:  # noqa: BLE001
                self._send_json(500, {"ok": False, "error": str(exc)})
            return

        if path == "/api/inbox":
            try:
                payload = self._read_json()
            except json.JSONDecodeError:
                self._send_json(400, {"ok": False, "error": "invalid JSON"})
                return
            text = (payload.get("text") or "").strip()
            if not text:
                self._send_json(400, {"ok": False, "error": "text required"})
                return
            process = payload.get("process", True)
            if process:
                self._send_json(200, append_inbox_and_process(text))
            else:
                append_pending_inbox(text)
                self._send_json(200, {"ok": True, "appended": text})
            return

        if path == "/api/progress":
            self._send_json(200, enqueue_progress())
            return

        self._send_json(404, {"ok": False, "error": "not found"})

    def do_PUT(self) -> None:
        path = urlparse(self.path).path
        if path in ("/api/todos", "/api/workspace"):
            try:
                payload = self._read_json()
            except json.JSONDecodeError:
                self._send_json(400, {"ok": False, "error": "invalid JSON"})
                return
            if not isinstance(payload, dict):
                self._send_json(400, {"ok": False, "error": "body must be an object"})
                return
            if not any(k in payload for k in ("tasks", "projects", "reminders")):
                self._send_json(
                    400,
                    {
                        "ok": False,
                        "error": "body must include projects, tasks, and/or reminders",
                    },
                )
                return
            try:
                _, version = update_workspace(payload, payload.get("_version"))
            except (WorkspaceConflict, WorkspaceBusy) as exc:
                self._send_json(409, {"ok": False, "error": str(exc)})
                return
            except WorkspaceDataError as exc:
                self._send_json(500, {"ok": False, "error": str(exc)})
                return
            except ValueError as exc:
                self._send_json(400, {"ok": False, "error": str(exc)})
                return
            self._send_json(200, {"ok": True, "_version": version})
            return

        self._send_json(404, {"ok": False, "error": "not found"})


def main() -> None:
    load_dotenv()
    ensure_data()
    # Warm ASR in background so the first voice note is faster.
    threading.Thread(target=warm_asr, name="asr-warmup", daemon=True).start()
    # Daily project-progress git inspection.
    threading.Thread(
        target=progress_scheduler_loop, name="progress-scheduler", daemon=True
    ).start()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"My is running at http://{HOST}:{PORT}")
    accel = "MLX/Metal GPU" if WHISPER_BACKEND == "mlx" else "CPU (faster-whisper)"
    print(
        f"Voice ASR: backend={WHISPER_BACKEND} model={WHISPER_MODEL} ({accel})"
    )
    print(
        f"Project progress check: daily at {PROGRESS_HOUR:02d}:{PROGRESS_MINUTE:02d} "
        "(override with MY_PROGRESS_HOUR/MY_PROGRESS_MINUTE)"
    )
    if MY_AGENT_ENTRY.is_file():
        print(f"Auto-process via: node {MY_AGENT_ENTRY}")
    else:
        print(
            "WARNING: my-agent not built — transcription will still work. "
            "Build it with `cd my-agent && npm install && npm run build`."
        )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


if __name__ == "__main__":
    main()
