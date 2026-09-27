/* Record into the Pi composer using My's existing local Whisper backend. Nothing is sent. */
import { spawn, type ChildProcess } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdir, mkdtemp, rm } from "node:fs/promises";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { Key } from "@earendil-works/pi-tui";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

const root = resolve(fileURLToPath(import.meta.url), "../../../");
const helper = join(root, "pi_voice", "transcribe.py");
const scratch = join(root, "data", "tmp");
const localPython = join(root, ".venv", "bin", "python");
const python = process.env.MY_PI_VOICE_PYTHON || (existsSync(localPython) ? localPython : "python3");
const device = process.env.MY_PI_VOICE_DEVICE || ":default";
const maxMs = 90_000;

type Recording = {
  proc: ChildProcess;
  directory: string;
  wav: string;
  closed: Promise<{ code: number | null; stderr: string }>;
  timer: ReturnType<typeof setTimeout>;
};

function run(command: string, args: string[], env: NodeJS.ProcessEnv): Promise<{ code: number | null; stdout: string; stderr: string }> {
  return new Promise((resolveResult, reject) => {
    const proc = spawn(command, args, { env, stdio: ["ignore", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    proc.stdout!.on("data", (chunk: Buffer) => { stdout += chunk.toString(); });
    proc.stderr!.on("data", (chunk: Buffer) => { stderr = (stderr + chunk.toString()).slice(-4096); });
    proc.once("error", reject);
    proc.once("close", (code) => resolveResult({ code, stdout, stderr }));
  });
}

function appendDraft(existing: string, transcript: string): string {
  return existing + (existing && !/\s$/.test(existing) ? " " : "") + transcript;
}

export default function (pi: ExtensionAPI) {
  let active: Recording | undefined;
  let busy = false;
  let disposed = false;

  const status = (ctx: ExtensionContext, value?: string) => ctx.ui.setStatus("my-voice", value);
  const errorText = (error: unknown) => error instanceof Error ? error.message : String(error);

  async function toggle(ctx: ExtensionContext) {
    if (disposed) return;
    if (ctx.mode !== "tui") {
      ctx.ui.notify("Voice input requires the interactive Pi terminal.", "error");
      return;
    }
    if (busy) {
      ctx.ui.notify("Voice is still starting or transcribing; please wait.", "warning");
      return;
    }
    busy = true;
    try {
      if (active) {
        const recording = active;
        active = undefined;
        clearTimeout(recording.timer);
        status(ctx, "Voice: transcribing locally…");
        try {
          if (recording.proc.exitCode === null) recording.proc.kill("SIGINT");
          const capture = await recording.closed;
          if (capture.code !== 0 && capture.code !== 255) throw new Error(capture.stderr.trim() || `ffmpeg exited ${capture.code}`);
          const result = await run(python, [helper, recording.wav], {
            ...process.env, PYTHONDONTWRITEBYTECODE: "1", HF_HUB_OFFLINE: "1", TRANSFORMERS_OFFLINE: "1",
          });
          if (result.code !== 0) throw new Error(result.stderr.trim().split("\n").at(-1) || `Whisper exited ${result.code}`);
          const text = result.stdout.trim();
          if (!text) throw new Error("No clear speech detected.");
          if (disposed) return;
          // Read at completion, not at start: edits made during recording are preserved.
          ctx.ui.setEditorText(appendDraft(ctx.ui.getEditorText(), text));
          ctx.ui.notify("Transcript appended to draft. Edit and press Enter to send.", "info");
        } finally {
          await rm(recording.directory, { recursive: true, force: true });
        }
      } else {
        await mkdir(scratch, { recursive: true });
        const directory = await mkdtemp(join(scratch, "pi-voice-"));
        const wav = join(directory, "recording.wav");
        try {
          const proc = spawn("ffmpeg", ["-nostdin", "-hide_banner", "-loglevel", "error", "-f", "avfoundation", "-i", device,
            "-t", "90", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", "-y", wav], { stdio: ["ignore", "ignore", "pipe"] });
          let stderr = "";
          const closed = new Promise<{ code: number | null; stderr: string }>((resolveClose) => {
            proc.stderr!.on("data", (chunk: Buffer) => { stderr = (stderr + chunk.toString()).slice(-4096); });
            proc.once("error", (err) => { stderr += err.message; });
            proc.once("close", (code) => resolveClose({ code, stderr }));
          });
          const timer = setTimeout(() => {
            if (active?.proc !== proc) return;
            active = undefined;
            proc.kill("SIGINT");
            void closed.then(() => rm(directory, { recursive: true, force: true }));
            status(ctx);
            ctx.ui.notify("Voice recording reached 90 seconds; discarded. Try a shorter recording.", "error");
          }, maxMs);
          active = { proc, directory, wav, closed, timer };
          status(ctx, "Voice: recording (Ctrl+Shift+V or /voice to stop)");
          ctx.ui.notify("Recording locally. Repeat /voice or Ctrl+Shift+V to stop.", "info");
          // If microphone access is denied, ffmpeg exits without another keypress.
          void closed.then(async ({ code, stderr: message }) => {
            if (active?.proc !== proc) return;
            active = undefined;
            clearTimeout(timer);
            await rm(directory, { recursive: true, force: true });
            status(ctx);
            ctx.ui.notify(`Microphone recording failed: ${message.trim() || `ffmpeg exited ${code}`}`, "error");
          });
        } catch (err) {
          await rm(directory, { recursive: true, force: true });
          throw err;
        }
      }
    } catch (err) {
      ctx.ui.notify(`Voice input failed; draft unchanged: ${errorText(err)}`, "error");
    } finally {
      status(ctx, active ? "Voice: recording (Ctrl+Shift+V or /voice to stop)" : undefined);
      busy = false;
    }
  }

  pi.registerCommand("voice", { description: "Start/stop local voice recording into the editable draft", handler: async (_args, ctx) => toggle(ctx) });
  pi.registerShortcut(Key.ctrlShift("v"), { description: "Start/stop local voice recording", handler: toggle });
  pi.on("session_shutdown", async () => {
    disposed = true;
    if (!active) return;
    const recording = active;
    active = undefined;
    clearTimeout(recording.timer);
    recording.proc.kill("SIGINT");
    await recording.closed;
    await rm(recording.directory, { recursive: true, force: true });
  });
}

export { appendDraft };
