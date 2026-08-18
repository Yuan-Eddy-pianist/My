const WORK_SECONDS = 35 * 60;
const BREAK_SECONDS = 5 * 60;
const POMODORO_KEY = "my.pomodoro.v2";
const POMODORO_CHANNEL = "my.pomodoro";

export function $(sel, root = document) {
  return root.querySelector(sel);
}

/* ---- Watchdog ("black box") ----
 * Zero-overhead diagnostic: counters + events flushed to localStorage every 5s.
 * If the page ever freezes, the log survives in localStorage and shows what
 * happened right before the freeze (stalls, broadcast storms, poll errors).
 */
const WD_KEY = "my.watchdog.v1";
const wdTabId =
  (sessionStorage.getItem("my.watchdog.tab") ||
    Math.random().toString(36).slice(2, 8));
try {
  sessionStorage.setItem("my.watchdog.tab", wdTabId);
} catch {
  /* ignore */
}

export function wdCount(name) {
  const wd = window.__myWatchdog;
  if (wd) wd.count(name);
}

export function wdEvent(type, data) {
  const wd = window.__myWatchdog;
  if (wd) wd.event(type, data);
}

export function setupWatchdog() {
  if (window.__myWatchdog) return;
  const counters = Object.create(null);
  let events = [];
  const wd = {
    count(name) {
      counters[name] = (counters[name] || 0) + 1;
    },
    event(type, data) {
      events.push({ t: Date.now(), type, data });
      if (events.length > 30) events.shift();
    },
  };
  window.__myWatchdog = wd;

  let lastBeat = performance.now();
  function flush() {
    const now = performance.now();
    const gap = Math.round(now - lastBeat);
    lastBeat = now;
    let log = [];
    try {
      log = JSON.parse(localStorage.getItem(WD_KEY) || "[]");
    } catch {
      log = [];
    }
    const entry = { t: Date.now(), tab: wdTabId, hb: gap, ...counters };
    if (gap > 7000) entry.stall = true;
    if (events.length) {
      entry.ev = events;
      events = [];
    }
    for (const k of Object.keys(counters)) counters[k] = 0;
    log.push(entry);
    if (log.length > 80) log.splice(0, log.length - 80);
    try {
      localStorage.setItem(WD_KEY, JSON.stringify(log));
    } catch {
      /* ignore */
    }
  }
  setInterval(flush, 5000);
  window.addEventListener("pagehide", flush);
}

export function formatTime(totalSeconds) {
  const secs = Math.max(0, Math.ceil(totalSeconds));
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export function todayKey() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export async function postInbox(text, { process = true } = {}) {
  const res = await fetch("/api/inbox", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, process }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || `inbox failed (${res.status})`);
  }
  return data;
}

export function emptyWorkspace() {
  return { projects: [], tasks: [], reminders: [] };
}

export function normalizeWorkspace(raw) {
  const base = emptyWorkspace();
  if (!raw || typeof raw !== "object") return base;
  return {
    projects: Array.isArray(raw.projects) ? raw.projects : [],
    tasks: Array.isArray(raw.tasks) ? raw.tasks : [],
    reminders: Array.isArray(raw.reminders) ? raw.reminders : [],
  };
}

export async function fetchWorkspace() {
  const res = await fetch("/api/workspace");
  if (!res.ok) throw new Error(`workspace failed (${res.status})`);
  return normalizeWorkspace(await res.json());
}

/** @deprecated use fetchWorkspace */
export async function fetchTodos() {
  return fetchWorkspace();
}

export async function saveWorkspace(payload) {
  const body = normalizeWorkspace(payload);
  const res = await fetch("/api/workspace", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `save failed (${res.status})`);
  return data;
}

/** @deprecated use saveWorkspace */
export async function saveTodos(payload) {
  return saveWorkspace(payload);
}

export async function checkPath(path) {
  const res = await fetch(`/api/path?path=${encodeURIComponent(path || "")}`);
  if (!res.ok) throw new Error(`path check failed (${res.status})`);
  return res.json();
}

export function newId(prefix = "item") {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
}

export function nowIsoLocal() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  const off = -d.getTimezoneOffset();
  const sign = off >= 0 ? "+" : "-";
  const oh = pad(Math.floor(Math.abs(off) / 60));
  const om = pad(Math.abs(off) % 60);
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
    `T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}` +
    `${sign}${oh}:${om}`
  );
}

export async function fetchAgentStatus() {
  const res = await fetch("/api/agent");
  if (!res.ok) throw new Error(`agent status failed (${res.status})`);
  return res.json();
}

export async function waitForAgent({ onUpdate } = {}) {
  const started = Date.now();
  let sawActive = false;
  while (Date.now() - started < 5 * 60 * 1000) {
    const status = await fetchAgentStatus();
    if (onUpdate) onUpdate(status);
    const state = status.state || "idle";
    if (state === "queued" || state === "running") {
      sawActive = true;
    }
    if (state === "done" || state === "error") {
      return status;
    }
    if (sawActive && state === "idle") {
      return status;
    }
    await new Promise((r) => setTimeout(r, 700));
  }
  return {
    state: "error",
    message: "Timed out waiting for the agent.",
  };
}

function defaultPomodoroState() {
  return {
    mode: "work",
    running: false,
    endsAt: null,
    remainingMs: WORK_SECONDS * 1000,
    sessionsToday: 0,
    date: todayKey(),
  };
}

function loadPomodoroState() {
  const raw = JSON.parse(localStorage.getItem(POMODORO_KEY) || "null");
  if (!raw) {
    // migrate v1 if present
    const v1 = JSON.parse(localStorage.getItem("my.pomodoro.v1") || "null");
    if (v1) {
      return {
        ...defaultPomodoroState(),
        mode: v1.mode === "break" ? "break" : "work",
        remainingMs: Number.isFinite(v1.remaining)
          ? v1.remaining * 1000
          : WORK_SECONDS * 1000,
        sessionsToday: v1.date === todayKey() ? v1.sessionsToday || 0 : 0,
        date: todayKey(),
        running: false,
        endsAt: null,
      };
    }
    return defaultPomodoroState();
  }
  const state = { ...defaultPomodoroState(), ...raw };
  if (state.date !== todayKey()) {
    state.sessionsToday = 0;
    state.date = todayKey();
  }
  return state;
}

let lastSavedStateJson = "";

function savePomodoroState(state, { broadcast = true } = {}) {
  const json = JSON.stringify(state);
  if (json === lastSavedStateJson) return;
  lastSavedStateJson = json;
  localStorage.setItem(POMODORO_KEY, json);
  wdCount("pomoSave");
  if (!broadcast) return;
  try {
    const bc = new BroadcastChannel(POMODORO_CHANNEL);
    bc.postMessage({ type: "sync", state });
    bc.close();
    wdCount("bcOut");
  } catch {
    /* ignore */
  }
}

function remainingMsOf(state, now = Date.now()) {
  if (state.running && state.endsAt) {
    return Math.max(0, state.endsAt - now);
  }
  return Math.max(0, state.remainingMs || 0);
}

function advanceIfNeeded(state, now = Date.now()) {
  let changed = false;
  let guard = 0;
  while (state.running && state.endsAt && state.endsAt <= now && guard < 8) {
    guard += 1;
    changed = true;
    if (state.mode === "work") {
      state.sessionsToday += 1;
      state.mode = "break";
      state.endsAt = now + BREAK_SECONDS * 1000;
      state.remainingMs = BREAK_SECONDS * 1000;
      if (typeof Notification !== "undefined" && Notification.permission === "granted") {
        new Notification("Break time");
      }
    } else {
      // Break over: switch back to focus, but wait for a MANUAL start.
      state.mode = "work";
      state.running = false;
      state.endsAt = null;
      state.remainingMs = WORK_SECONDS * 1000;
      if (typeof Notification !== "undefined" && Notification.permission === "granted") {
        new Notification("Back to focus");
      }
    }
  }
  if (!state.running) {
    state.endsAt = null;
  }
  return changed;
}

/**
 * Wall-clock pomodoro: keeps counting across page navigations via endsAt in localStorage.
 */
export function setupPomodoro({
  displayEl,
  modeEl,
  startBtn,
  resetBtn,
  skipBtn,
  sessionEl,
  badgeEl,
  progressEl,
  handEl,
  faceEl,
} = {}) {
  let state = loadPomodoroState();
  advanceIfNeeded(state);
  savePomodoroState(state);

  const textCache = new Map();
  function setText(el, text) {
    if (el && textCache.get(el) !== text) {
      textCache.set(el, text);
      el.textContent = text;
    }
  }

  let lastPersistAt = 0;

  function render(remote = false) {
    state = loadPomodoroState();
    const modeBefore = state.mode;
    const transitioned = advanceIfNeeded(state);
    if (transitioned && state.mode !== modeBefore) {
      // Focus→break: soft ascending; break→focus: gentle descending.
      playChime(state.mode === "break" ? [523, 659, 784] : [784, 659]);
    }
    const remMs = remainingMsOf(state);
    if (state.running) {
      state.remainingMs = remMs;
    }
    if (!remote) {
      // Countdown persists at most once per second; actions save immediately.
      const now = Date.now();
      if (!state.running || now - lastPersistAt >= 1000) {
        savePomodoroState(state);
        lastPersistAt = now;
      }
    }

    const label = state.mode === "work" ? "Focus" : "Break";
    const clock = formatTime(remMs / 1000);

    const totalMs =
      (state.mode === "work" ? WORK_SECONDS : BREAK_SECONDS) * 1000;
    const frac = Math.min(1, Math.max(0, remMs / totalMs));
    if (progressEl) {
      const C = 2 * Math.PI * 132;
      progressEl.style.strokeDasharray = `${C}`;
      // Negative offset: colored arc = remaining time, ending at the hand.
      progressEl.style.strokeDashoffset = `${C * (frac - 1)}`;
    }
    if (handEl) {
      // Clockwise like a real clock hand: 0 at full, sweeps as time elapses.
      handEl.setAttribute("transform", `rotate(${(1 - frac) * 360} 150 150)`);
    }
    if (faceEl) {
      faceEl.classList.toggle("break", state.mode === "break");
    }
    if (document.body) {
      document.body.classList.toggle("break-mode", state.mode === "break");
    }

    setText(displayEl, clock);
    setText(modeEl, state.mode === "work" ? "专注" : "休息");
    setText(sessionEl, `今日 ${state.sessionsToday} 次专注`);
    setText(startBtn, state.running ? "暂停" : "开始");
    if (badgeEl) {
      setText(badgeEl, `${label} ${clock}`);
      const running = state.running ? "1" : "0";
      if (badgeEl.dataset.running !== running) {
        badgeEl.dataset.running = running;
      }
    }
  }

  function start() {
    // Unlock WebAudio inside the gesture so transition chimes can play later.
    unlockChime();
    state = loadPomodoroState();
    advanceIfNeeded(state);
    if (state.running) return;
    const rem = remainingMsOf(state) || (state.mode === "work" ? WORK_SECONDS : BREAK_SECONDS) * 1000;
    state.running = true;
    state.endsAt = Date.now() + rem;
    state.remainingMs = rem;
    savePomodoroState(state);
    if (typeof Notification !== "undefined" && Notification.permission === "default") {
      Notification.requestPermission().catch(() => {});
    }
    render();
  }

  function pause() {
    state = loadPomodoroState();
    advanceIfNeeded(state);
    if (!state.running) return;
    state.remainingMs = remainingMsOf(state);
    state.running = false;
    state.endsAt = null;
    savePomodoroState(state);
    render();
  }

  function reset() {
    state = loadPomodoroState();
    state.running = false;
    state.endsAt = null;
    state.remainingMs =
      (state.mode === "work" ? WORK_SECONDS : BREAK_SECONDS) * 1000;
    savePomodoroState(state);
    render();
  }

  function skip() {
    state = loadPomodoroState();
    const now = Date.now();
    if (state.mode === "work") {
      state.sessionsToday += 1;
      state.mode = "break";
      state.remainingMs = BREAK_SECONDS * 1000;
      if (state.running) {
        state.endsAt = now + state.remainingMs;
      } else {
        state.endsAt = null;
      }
    } else {
      // Skip break → focus, but stay paused (manual start).
      state.mode = "work";
      state.running = false;
      state.endsAt = null;
      state.remainingMs = WORK_SECONDS * 1000;
    }
    savePomodoroState(state);
    render();
  }

  if (startBtn) {
    startBtn.addEventListener("click", () => {
      state = loadPomodoroState();
      if (state.running) pause();
      else start();
    });
  }
  if (resetBtn) resetBtn.addEventListener("click", reset);
  if (skipBtn) skipBtn.addEventListener("click", skip);
  if (badgeEl) {
    badgeEl.title = "Pomodoro (keeps running across pages)";
    badgeEl.addEventListener("click", () => {
      state = loadPomodoroState();
      if (state.running) pause();
      else start();
    });
  }

  try {
    const bc = new BroadcastChannel(POMODORO_CHANNEL);
    // Remote sync: re-render from localStorage, never echo back.
    bc.onmessage = () => {
      wdCount("bcIn");
      render(true);
    };
  } catch {
    /* ignore */
  }

  window.addEventListener("storage", (e) => {
    if (e.key === POMODORO_KEY) {
      wdCount("storageEv");
      render(true);
    }
  });

  render();
  const timerId = setInterval(render, 250);
  return () => clearInterval(timerId);
}

function pickRecorderMime() {
  const candidates = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/mp4",
    "audio/ogg;codecs=opus",
  ];
  for (const type of candidates) {
    if (window.MediaRecorder?.isTypeSupported?.(type)) return type;
  }
  return "";
}

function isLikelyEmbeddedBrowser() {
  const ua = navigator.userAgent || "";
  return /Electron/i.test(ua) && !/Edg\//.test(ua);
}

function isMacBookBuiltInMic(label) {
  const l = (label || "").toLowerCase();
  if (!l) return false;
  if (/iphone|ipad|continuity|blackhole|virtual|zoom|teams|hdmi|display/.test(l)) {
    return false;
  }
  return (
    /macbook/.test(l) ||
    /built-?in\s+microphone/.test(l) ||
    /internal\s+microphone/.test(l) ||
    (/macintosh|mac\s*book/.test(l) && /microphone/.test(l))
  );
}

function rawAudioConstraints(deviceId) {
  const audio = {
    echoCancellation: false,
    noiseSuppression: false,
    autoGainControl: true,
    channelCount: 1,
  };
  if (deviceId) audio.deviceId = { exact: deviceId };
  return { audio };
}

/** Shared chime context. Must be unlocked inside a user-gesture handler. */
let chimeCtx = null;

function unlockChime() {
  try {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    if (!chimeCtx || chimeCtx.state === "closed") chimeCtx = new AC();
    if (chimeCtx.state === "suspended") chimeCtx.resume().catch(() => {});
  } catch {
    /* chime is optional */
  }
}

/** Short chime: ascending on record start, descending on stop. */
export async function playChime(freqs, { dur = 0.15, gap = 0.08, volume = 0.35 } = {}) {
  try {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    if (!chimeCtx || chimeCtx.state === "closed") chimeCtx = new AC();
    if (chimeCtx.state === "suspended") {
      await chimeCtx.resume().catch(() => {});
    }
    if (chimeCtx.state !== "running") return;
    let t = chimeCtx.currentTime + 0.03;
    for (const f of freqs) {
      const osc = chimeCtx.createOscillator();
      const gain = chimeCtx.createGain();
      osc.type = "sine";
      osc.frequency.value = f;
      gain.gain.setValueAtTime(0.0001, t);
      gain.gain.exponentialRampToValueAtTime(volume, t + 0.03);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      osc.connect(gain).connect(chimeCtx.destination);
      osc.start(t);
      osc.stop(t + dur + 0.03);
      t += dur + gap;
    }
  } catch {
    /* chime is optional */
  }
}

/** Prefer MacBook built-in mic so Chrome doesn’t grab a silent virtual device. */
async function resolveBuiltInMicId() {
  let warm = null;
  try {
    warm = await navigator.mediaDevices.getUserMedia(rawAudioConstraints());
  } catch {
    return "";
  }
  warm.getTracks().forEach((t) => t.stop());

  const inputs = (await navigator.mediaDevices.enumerateDevices()).filter(
    (d) => d.kind === "audioinput" && d.deviceId,
  );
  const builtIn = inputs.find((d) => isMacBookBuiltInMic(d.label));
  return builtIn?.deviceId || "";
}

/**
 * Record mic → queue on server (non-blocking). You can record again immediately.
 */
export function setupVoice({
  transcriptEl,
  statusEl,
  micBtn,
  meterEl,
  onProcessed,
}) {
  let listening = false;
  let mediaStream = null;
  let recorder = null;
  let chunks = [];
  let audioCtx = null;
  let analyser = null;
  let meterRaf = 0;
  let lastMeterPct = -1;
  let preferredDeviceId = "";
  let pollTimer = 0;
  let lastSeenTranscript = "";
  let clientQueued = 0;
  let statusClearTimer = 0;

  function clearStatus() {
    if (statusClearTimer) {
      window.clearTimeout(statusClearTimer);
      statusClearTimer = 0;
    }
    statusEl.textContent = "";
    statusEl.className = "status";
  }

  function setStatus(msg, kind = "") {
    if (statusClearTimer) {
      window.clearTimeout(statusClearTimer);
      statusClearTimer = 0;
    }
    statusEl.textContent = msg;
    statusEl.className = `status${kind ? ` ${kind}` : ""}`;
    // Only post-stop confirmation is ephemeral; "开始录音" stays until stop.
    if (msg === "结束录音") {
      statusClearTimer = window.setTimeout(clearStatus, 1000);
    }
  }

  function setDraft(text) {
    transcriptEl.textContent = text;
  }

  function stopMeter() {
    if (meterRaf) cancelAnimationFrame(meterRaf);
    meterRaf = 0;
    lastMeterPct = -1;
    if (meterEl) meterEl.style.setProperty("--level", "0%");
    if (audioCtx) {
      audioCtx.close().catch(() => {});
      audioCtx = null;
    }
    analyser = null;
  }

  function startMeter(stream) {
    if (!meterEl) return;
    try {
      audioCtx = new AudioContext();
      if (audioCtx.state === "suspended") audioCtx.resume().catch(() => {});
      const source = audioCtx.createMediaStreamSource(stream);
      analyser = audioCtx.createAnalyser();
      analyser.fftSize = 2048;
      source.connect(analyser);
      const data = new Uint8Array(analyser.fftSize);
      const tick = () => {
        analyser.getByteTimeDomainData(data);
        let sum = 0;
        for (let i = 0; i < data.length; i += 1) {
          const v = (data[i] - 128) / 128;
          sum += v * v;
        }
        const rms = Math.sqrt(sum / data.length);
        const pct = Math.min(100, Math.round(rms * 500));
        if (pct !== lastMeterPct) {
          lastMeterPct = pct;
          meterEl.style.setProperty("--level", `${pct}%`);
        }
        meterRaf = requestAnimationFrame(tick);
      };
      tick();
    } catch {
      /* meter is optional */
    }
  }

  function stopTracks() {
    if (mediaStream) {
      mediaStream.getTracks().forEach((t) => t.stop());
      mediaStream = null;
    }
    stopMeter();
  }

  function refreshStatusLine(s) {
    if (listening) return;
    const state = s.state || "idle";
    if (s.lastTranscript && s.lastTranscript !== lastSeenTranscript) {
      lastSeenTranscript = s.lastTranscript;
      setDraft(s.lastTranscript);
      if (onProcessed) onProcessed(s);
    }
    if (state === "error") {
      setStatus(s.message || "出错了", "error");
    }
  }

  function stopPolling() {
    if (pollTimer) {
      window.clearInterval(pollTimer);
      pollTimer = 0;
    }
  }

  function ensurePolling() {
    if (pollTimer) return;
    const startedAt = Date.now();
    let errors = 0;
    pollTimer = window.setInterval(async () => {
      // Absolute cap: never poll longer than 5 minutes.
      if (Date.now() - startedAt > 5 * 60 * 1000) {
        stopPolling();
        return;
      }
      try {
        const s = await fetchAgentStatus();
        errors = 0;
        wdCount("poll");
        refreshStatusLine(s);
        const idle =
          (s.voicePending || 0) === 0 &&
          (s.agentPending || 0) === 0 &&
          (s.state === "idle" || s.state === "done" || s.state === "error");
        if (idle && clientQueued === 0 && !listening) {
          stopPolling();
        }
      } catch {
        // Server unreachable: back off and give up after ~10 failures.
        errors += 1;
        wdCount("pollErr");
        if (errors >= 10) {
          stopPolling();
          if (!listening) {
            setStatus("服务未响应，请确认 serve.py 在运行", "error");
          }
        }
      }
    }, 900);
  }

  async function enqueueBlob(blob, mime) {
    clientQueued += 1;
    ensurePolling();
    try {
      const res = await fetch("/api/voice", {
        method: "POST",
        headers: {
          "Content-Type": mime,
          "X-Filename": mime.includes("mp4") ? "audio.m4a" : "audio.webm",
        },
        body: blob,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.error || `上传失败 (${res.status})`);
      }
    } catch (err) {
      setStatus(err.message || String(err), "error");
    } finally {
      clientQueued = Math.max(0, clientQueued - 1);
    }
  }

  async function finishRecording() {
    if (!recorder) return;
    const mime = recorder.mimeType || "audio/webm";
    const blob = await new Promise((resolve) => {
      recorder.onstop = () => resolve(new Blob(chunks, { type: mime }));
      try {
        recorder.stop();
      } catch {
        resolve(new Blob(chunks, { type: mime }));
      }
    });
    recorder = null;
    chunks = [];
    stopTracks();
    micBtn.classList.remove("listening");
    wdEvent("rec", "stop");
    setStatus("结束录音");

    if (!blob.size) {
      setStatus("录音为空，请重试", "error");
      return;
    }

    // Do not await full pipeline — mic is free immediately.
    enqueueBlob(blob, mime);
  }

  if (!window.isSecureContext) {
    setStatus("请用 Chrome/Edge 打开 http://127.0.0.1:8765", "error");
  } else if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    setStatus("此浏览器不支持录音", "error");
    micBtn.disabled = true;
  }
  // Mic device resolution happens lazily on first record click.

  micBtn.addEventListener("click", async () => {
    // Unlock WebAudio synchronously inside the gesture, before any await.
    unlockChime();
    if (listening) {
      listening = false;
      micBtn.classList.remove("listening");
      playChime([880, 520]);
      await finishRecording();
      return;
    }

    try {
      if (!preferredDeviceId) {
        preferredDeviceId = await resolveBuiltInMicId();
      }
      try {
        mediaStream = await navigator.mediaDevices.getUserMedia(
          rawAudioConstraints(preferredDeviceId || undefined),
        );
      } catch (err) {
        if (preferredDeviceId && err?.name === "OverconstrainedError") {
          preferredDeviceId = "";
          mediaStream = await navigator.mediaDevices.getUserMedia(
            rawAudioConstraints(),
          );
        } else {
          throw err;
        }
      }
      const track = mediaStream.getAudioTracks()[0];
      startMeter(mediaStream);

      const mime = pickRecorderMime();
      recorder = mime
        ? new MediaRecorder(mediaStream, { mimeType: mime })
        : new MediaRecorder(mediaStream);
      chunks = [];
      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size) chunks.push(e.data);
      };
      recorder.start(250);

      listening = true;
      micBtn.classList.add("listening");
      wdEvent("rec", "start");
      playChime([660, 880]);
      setStatus("开始录音");
    } catch (err) {
      listening = false;
      stopTracks();
      micBtn.classList.remove("listening");
      wdEvent("recErr", err?.name || String(err));
      const name = err?.name || "";
      if (name === "NotAllowedError" || name === "PermissionDeniedError") {
        setStatus("麦克风被拦截，请允许麦克风权限", "error");
      } else if (name === "NotFoundError") {
        setStatus("未检测到麦克风", "error");
      } else {
        setStatus(err.message || String(err), "error");
      }
    }
  });
}

export function dueMeta(due) {
  if (!due) return { text: "无截止日期", kind: "" };
  const today = todayKey();
  if (due < today) return { text: `已逾期 · ${due}`, kind: "overdue" };
  if (due === today) return { text: `今日截止 · ${due}`, kind: "soon" };
  return { text: `截止 ${due}`, kind: "" };
}
