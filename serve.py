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

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
INBOX = DATA / "inbox.md"
ARCHIVE = DATA / "inbox-archive.md"
WORKSPACE = DATA / "todos.json"  # projects + short-term todos + reminders
STATUS = DATA / ".agent-status.json"
ENV_FILE = ROOT / ".env"
HOST = "127.0.0.1"
PORT = 8765


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

Workspace file: data/todos.json with three arrays:
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
5. Merge; do not duplicate clearly identical open items. Preserve projects/tasks/reminders
   keys even if empty. Write pretty JSON (2-space indent).
6. Append the processed raw inbox content to data/inbox-archive.md under a ## timestamp heading
   (always archive, even when you create nothing).
7. Reset data/inbox.md to exactly:

# Inbox

Voice notes land here and are processed automatically.

8. Do not ask questions. Do not edit app/, serve.py, or schedule/.
9. Reply with one short line summarizing what you changed, or "No clear items; archived only."
"""

_job_queue: queue.Queue[str | None] = queue.Queue()
_voice_queue: queue.Queue[dict | None] = queue.Queue()
_status_lock = threading.Lock()
_worker_started = False
_voice_worker_started = False
_whisper_model = None
_whisper_lock = threading.Lock()
_voice_pending = 0
_job_seq = 0


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def empty_workspace() -> dict:
    return {"projects": [], "tasks": [], "reminders": []}


def normalize_workspace(payload: object) -> dict:
    """Accept legacy {tasks} or full workspace; always return the three arrays."""
    if not isinstance(payload, dict):
        return empty_workspace()
    projects = payload.get("projects")
    tasks = payload.get("tasks")
    reminders = payload.get("reminders")
    return {
        "projects": projects if isinstance(projects, list) else [],
        "tasks": tasks if isinstance(tasks, list) else [],
        "reminders": reminders if isinstance(reminders, list) else [],
    }


def read_workspace() -> dict:
    if not WORKSPACE.exists():
        return empty_workspace()
    try:
        return normalize_workspace(json.loads(WORKSPACE.read_text(encoding="utf-8")))
    except json.JSONDecodeError:
        return empty_workspace()


def write_workspace(payload: dict) -> dict:
    data = normalize_workspace(payload)
    WORKSPACE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return data


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
        INBOX.write_text(
            "# Inbox\n\nVoice notes land here and are processed automatically.\n",
            encoding="utf-8",
        )
    if not ARCHIVE.exists():
        ARCHIVE.write_text("# Inbox archive\n", encoding="utf-8")
    if not WORKSPACE.exists():
        write_workspace(empty_workspace())
    else:
        # Migrate legacy {tasks}-only files in place.
        write_workspace(read_workspace())
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


def run_agent_once(note_preview: str) -> None:
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

    write_status(
        "running",
        "my-agent is updating your workspace…",
        lastNote=note_preview,
    )
    cmd = [node, str(MY_AGENT_ENTRY), AGENT_PROMPT]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=300,
            env=os.environ.copy(),
        )
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        summary = out.splitlines()[-1] if out else (err.splitlines()[-1] if err else "")
        if proc.returncode != 0:
            write_status(
                "error",
                summary or f"Agent failed (exit {proc.returncode}).",
                lastNote=note_preview,
                lastResult=(out or err)[-2000:],
            )
            return
        write_status(
            "done",
            summary or "Workspace updated.",
            lastNote=note_preview,
            lastResult=out[-2000:] if out else "",
        )
    except subprocess.TimeoutExpired:
        write_status(
            "error",
            "Agent timed out after 5 minutes.",
            lastNote=note_preview,
        )
    except Exception as exc:  # noqa: BLE001
        write_status(
            "error",
            f"Agent launch failed: {exc}",
            lastNote=note_preview,
            lastResult=traceback.format_exc()[-2000:],
        )


def worker_loop() -> None:
    while True:
        note_preview = _job_queue.get()
        if note_preview is None:
            _job_queue.task_done()
            break
        try:
            latest = note_preview
            while True:
                try:
                    nxt = _job_queue.get_nowait()
                except queue.Empty:
                    break
                if nxt is None:
                    _job_queue.task_done()
                    return
                latest = nxt
                _job_queue.task_done()
            run_agent_once(latest)
        finally:
            _job_queue.task_done()


def enqueue_process(note_preview: str) -> dict:
    global _worker_started
    if not _worker_started:
        t = threading.Thread(target=worker_loop, name="my-agent-worker", daemon=True)
        t.start()
        _worker_started = True
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
            "Note saved. Starting my-agent…",
            lastNote=note_preview,
        )
    _job_queue.put(note_preview)
    status["queueDepth"] = pending + 1
    return status


def append_inbox_and_process(text: str) -> dict:
    block = f"\n## {now_iso()}\n\n{text}\n"
    with INBOX.open("a", encoding="utf-8") as f:
        f.write(block)
    preview = text if len(text) <= 120 else text[:117] + "…"
    return {
        "ok": True,
        "text": text,
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
    if not _voice_worker_started:
        t = threading.Thread(target=voice_worker_loop, name="my-voice-worker", daemon=True)
        t.start()
        _voice_worker_started = True
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
            self._send_json(200, read_workspace())
            return

        if path == "/api/path":
            qs = parse_qs(urlparse(self.path).query)
            raw = (qs.get("path") or [""])[0]
            self._send_json(200, path_info(raw))
            return

        if path == "/api/inbox":
            self._send_json(200, {"text": INBOX.read_text(encoding="utf-8")})
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
                block = f"\n## {now_iso()}\n\n{text}\n"
                with INBOX.open("a", encoding="utf-8") as f:
                    f.write(block)
                self._send_json(200, {"ok": True, "appended": text})
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
            # Merge with existing so a partial PUT (e.g. tasks-only) keeps other arrays.
            current = read_workspace()
            for key in ("projects", "tasks", "reminders"):
                if key in payload and isinstance(payload[key], list):
                    current[key] = payload[key]
            write_workspace(current)
            self._send_json(200, {"ok": True})
            return

        self._send_json(404, {"ok": False, "error": "not found"})


def main() -> None:
    load_dotenv()
    ensure_data()
    # Warm ASR in background so the first voice note is faster.
    threading.Thread(target=warm_asr, name="asr-warmup", daemon=True).start()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"My is running at http://{HOST}:{PORT}")
    accel = "MLX/Metal GPU" if WHISPER_BACKEND == "mlx" else "CPU (faster-whisper)"
    print(
        f"Voice ASR: backend={WHISPER_BACKEND} model={WHISPER_MODEL} ({accel})"
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
