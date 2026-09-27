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
  return { projects: [], tasks: [], reminders: [], _version: null };
}

export function normalizeWorkspace(raw) {
  const base = emptyWorkspace();
  if (!raw || typeof raw !== "object") return base;
  return {
    projects: Array.isArray(raw.projects) ? raw.projects : [],
    tasks: Array.isArray(raw.tasks) ? raw.tasks : [],
    reminders: Array.isArray(raw.reminders) ? raw.reminders : [],
    _version: typeof raw._version === "string" ? raw._version : null,
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
  if (!res.ok) {
    const error = new Error(data.error || `save failed (${res.status})`);
    error.status = res.status;
    throw error;
  }
  if (payload && typeof payload === "object" && typeof data._version === "string") {
    payload._version = data._version;
  }
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

    const label = state.mode === "work" ? "专注" : "休息";
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
    const action = state.running ? "暂停" : remMs < totalMs ? "继续" : "开始";
    setText(startBtn, `${action}${label}`);
    if (startBtn) startBtn.setAttribute("aria-pressed", String(state.running));
    if (badgeEl) {
      setText(badgeEl, `${label} ${clock}`);
      badgeEl.title = `${state.running ? "暂停" : "开始"}${label}计时 · 切换页面后继续计时`;
      badgeEl.setAttribute("aria-label", `${label}剩余 ${clock}，点击${state.running ? "暂停" : "开始"}`);
      badgeEl.setAttribute("aria-pressed", String(state.running));
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
  // Give macOS a beat to release the audio unit before we reacquire the
  // same device — reacquiring too fast can yield a permanently muted track
  // (MediaRecorder then records zero bytes).
  await new Promise((r) => setTimeout(r, 150));

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
  micBtn,
  statusEl,
  faceEl,
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
  let flashTimer = 0;
  let wasBusy = false;
  let prevState = "";

  function feedback(text, state = "idle") {
    if (statusEl) {
      if (statusEl.textContent !== text) statusEl.textContent = text;
      statusEl.dataset.state = state;
    }
    micBtn.setAttribute("aria-label", listening ? "结束语音记录" : "开始语音记录");
    micBtn.setAttribute("aria-pressed", String(listening));
  }
  feedback("随时说一句，记下想做的事");

  function stopMeter() {
    if (meterRaf) cancelAnimationFrame(meterRaf);
    meterRaf = 0;
    lastMeterPct = -1;
    micBtn.style.transform = "";
    if (audioCtx) {
      audioCtx.close().catch(() => {});
      audioCtx = null;
    }
    analyser = null;
  }

  /** Loudness-reactive button: the mic button itself scales with your voice. */
  function startMeter(stream) {
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
          if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
            micBtn.style.transform = `scale(${(1 + (pct / 100) * 0.2).toFixed(3)})`;
          }
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

  /** Brief icon morph (✓ / :() on the mic button, then back to the mic. */
  function flashIcon(cls, ms, message) {
    micBtn.classList.remove("done-flash", "error-flash");
    micBtn.classList.add(cls);
    feedback(message || (cls === "done-flash" ? "语音处理完成" : "语音记录失败，请重试"), cls === "done-flash" ? "done" : "error");
    if (flashTimer) window.clearTimeout(flashTimer);
    flashTimer = window.setTimeout(() => micBtn.classList.remove(cls), ms);
  }

  function setThinking(on) {
    micBtn.classList.toggle("thinking", on);
    if (on) micBtn.classList.remove("done-flash", "error-flash");
    if (faceEl) faceEl.classList.toggle("breathing", on);
    if (on && !listening) feedback("正在整理语音…也可以继续记录", "processing");
  }

  function refreshStatusLine(s) {
    if (listening) return;
    const state = s.state || "idle";
    if (s.lastTranscript && s.lastTranscript !== lastSeenTranscript) {
      lastSeenTranscript = s.lastTranscript;
      if (onProcessed) onProcessed(s);
    }

    // Keep the text status and icon feedback in sync with the voice pipeline.
    const busy =
      clientQueued > 0 ||
      (s.voicePending || 0) > 0 ||
      state === "transcribing" ||
      state === "queued" ||
      state === "running";
    setThinking(busy);

    if (!busy && state === "error") {
      // Only react to a fresh error transition, never a stale one on page load.
      if (wasBusy || (prevState && prevState !== "error")) {
        flashIcon("error-flash", 3200);
      }
    } else if (!busy && wasBusy && state === "done") {
      flashIcon("done-flash", 1800);
      playChime([784, 988], { volume: 0.22 });
      if (onProcessed) onProcessed(s);
    }
    prevState = state;
    wasBusy = busy;
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
            flashIcon("error-flash", 3200);
          }
        }
      }
    }, 900);
  }

  async function enqueueBlob(blob, mime) {
    clientQueued += 1;
    // Instant feedback on send — don't wait for the first poll tick.
    setThinking(true);
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
      wdEvent("recErr", "upload: " + (err?.message || String(err)));
      setThinking(false);
      flashIcon("error-flash", 3200, "发送失败，请检查连接后重试");
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
    wdEvent("rec", "stop bytes=" + blob.size);

    if (!blob.size) {
      // Dead take (e.g. muted track from the warm-stop-reacquire race):
      // silently return to the normal mic, and force a fresh device
      // resolution on the next click.
      preferredDeviceId = "";
      feedback("没有录到声音，请再试一次", "error");
      return;
    }

    // Do not await full pipeline — mic is free immediately.
    enqueueBlob(blob, mime);
  }

  if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    micBtn.disabled = true;
    feedback("当前浏览器无法录音，请使用 Chrome 或 Edge", "error");
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
      feedback("正在连接麦克风…", "connecting");
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
      if (track && track.muted) {
        // Acquired a dead track (macOS warm→stop→reacquire race): drop it
        // and take a fresh default-device stream once.
        wdEvent("rec", "muted-track");
        mediaStream.getTracks().forEach((t) => t.stop());
        await new Promise((r) => setTimeout(r, 150));
        mediaStream = await navigator.mediaDevices.getUserMedia(
          rawAudioConstraints(),
        );
      }
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
      feedback("正在聆听…再次点击麦克风结束", "recording");
      wdEvent("rec", "start");
      playChime([660, 880]);
    } catch (err) {
      listening = false;
      stopTracks();
      micBtn.classList.remove("listening");
      wdEvent("recErr", err?.name || String(err));
      flashIcon("error-flash", 3200, err?.name === "NotAllowedError"
        ? "未获得麦克风权限，请在浏览器中允许后重试"
        : "无法连接麦克风，请检查设备后重试");
    }
  });

  // Re-sync on page load: if the pipeline is already working (e.g. the user
  // switched between 专注/工作台 mid-run), resume the spinner feedback and
  // polling so the indicator survives page switches. Stale errors stay silent.
  fetchAgentStatus()
    .then((s) => {
      refreshStatusLine(s);
      const state = s.state || "idle";
      const busy =
        (s.voicePending || 0) > 0 ||
        (s.agentPending || 0) > 0 ||
        state === "transcribing" ||
        state === "queued" ||
        state === "running";
      if (busy) ensurePolling();
    })
    .catch(() => {});
}

export function dueMeta(due) {
  if (!due) return { text: "无截止日期", kind: "" };
  const today = todayKey();
  if (due < today) return { text: `已逾期 · ${due}`, kind: "overdue" };
  if (due === today) return { text: `今日截止 · ${due}`, kind: "soon" };
  return { text: `截止 ${due}`, kind: "" };
}
