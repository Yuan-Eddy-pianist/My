# My

Local day-to-day workspace: tomato clock, **工作台** (long-term projects, short-term todos, reminders), and **voice-only** capture.

The live setup now keeps personal projects, to-dos and reminders in Firstmate’s automatically loaded context. The dashboard, voice flow and Firstmate share protected edits to that source; the old dashboard JSON is inactive after migration. See [ownership, setup and migration details](agent-workflow/docs/Dashboard%20connection.md). The server requires the Firstmate context binding; missing or invalid context fails closed instead of falling back to the legacy JSON.

## Run

```bash
cd /Users/eddy/Desktop/My
./start.sh
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765) in **Chrome or Edge** (not Cursor’s built-in browser).

### Weekday auto-start (9:00 local)

Install a macOS LaunchAgent that starts My and opens the workspace every weekday at 09:00:

```bash
./schedule/install-launchd.sh
```

Because this repo lives on the Desktop, macOS privacy (TCC) blocks LaunchAgents from reading it directly. The installer therefore:

1. Puts a tiny runner in `~/Library/Application Support/com.eddy.my/`
2. Has that runner ask **Terminal.app** to run `schedule/start-weekday.sh` (Terminal already has Desktop access)

A Terminal window may flash briefly at 09:00. To avoid that later, move this folder off Desktop (e.g. `~/My`) and re-run the installer.

Test immediately:

```bash
launchctl kickstart -k "gui/$(id -u)/com.eddy.my.weekday"
# or:
./schedule/start-weekday.sh
```

Logs: `~/Library/Logs/com.eddy.my/`.

Uninstall:

```bash
./schedule/uninstall-launchd.sh
```

### Personal agent skills (any machine)

This repo stores personally selected skills in `.agent/skills/`. Codex and Cursor supplied skills stay in their application-managed locations. See [personal skill layout](docs/personal-skills-layout.md). Inbox and todos are not in git, so a new machine only needs `git`:

```bash
git clone https://github.com/Yuan-Eddy-pianist/My.git ~/My
cd ~/My && ./install-skills.sh
```

That is the whole bootstrap. You get the app files too; they sit unused if you only want skills. Later: `cd ~/My && git pull && ./install-skills.sh`.

Consume-only (no clone, copies into each harness via the skills CLI):

```bash
npx skills add Yuan-Eddy-pianist/My/.agent/skills -g
```

That reads **GitHub**, not this folder. If you see `No skills found`, the remote is still empty — push first (`git push -u origin main`), then retry. Do not run the `-g` command on this Mac if you already use `./install-skills.sh` (it would replace the `~/.cursor/skills` symlink).

Use the clone if you will edit skills and push them back. Use `npx` if that machine only installs them.

**Already in this repo:**

```bash
./install-skills.sh            # ask which harnesses
./install-skills.sh cursor     # one
./install-skills.sh 1 3        # Cursor + Codex
./install-skills.sh all        # Cursor, Claude, Codex, OpenCode
```

| Choice | Harness | Path |
|--------|---------|------|
| `1` / `cursor` | Cursor | `~/.cursor/skills` |
| `2` / `claude` | Claude Code | `~/.claude/skills` |
| `3` / `codex` | Codex | `~/.agents/skills` and `~/.codex/skills/<skill>` |
| `4` / `opencode` | OpenCode | `~/.config/opencode/skills` |
| `a` / `all` | all of the above | |

Codex personal aliases leave system and plugin skills in place. Its `canvas` link points directly to Cursor's managed `~/.cursor/skills-cursor/canvas` package. Re-run the installer if you move the folder. Existing conflicting individual skill paths are preserved.

```bash
./uninstall-skills.sh          # ask which to remove
./uninstall-skills.sh cursor
./uninstall-skills.sh all
```

Keep one repo. A second “skills-only” GitHub repo would drift.


### Project-progress summarizer account / usage limit

The project-progress summarizer in `my-agent` uses whichever Cursor account authenticates it. Voice agenda requests go to Firstmate and use its existing provider configuration; local Whisper needs no account.

**Option A — API key for a specific account (recommended):**

1. On that account, open [Cursor Dashboard → Integrations](https://cursor.com/dashboard/integrations) and create a user API key.
2. In this folder:

```bash
cp .env.example .env
# put the key in .env as CURSOR_API_KEY=...
./start.sh
```

**Option B — switch CLI login:**

```bash
agent logout
agent login   # sign in with the other account
```

## Your loop (UI only)

1. Tap **Tap to talk** (allow mic if asked)
2. Speak — the green meter should bounce
3. Tap again to finish

Uses the **MacBook built-in microphone**. Notes are **queued**: record again without waiting.

On Apple Silicon, ASR uses **MLX Whisper medium** (`mlx-community/whisper-medium-mlx` on Metal GPU) — not CUDA. Falls back to `faster-whisper` CPU `medium` if MLX fails.

For **Pi terminal voice input** (editable chat draft, not an inbox note), see [`pi_voice/README.md`](pi_voice/README.md). Use `/voice` or `Ctrl+Shift+V` to start and stop; review the transcript before sending.

My saves the exact transcript in a durable local request and sends it to Firstmate through its existing inbox. Firstmate interprets and applies personal-agenda edits with the shared locked/versioned tools, then returns a concise outcome. Pending or received means the change is not yet confirmed. If Firstmate is offline, the request remains recoverable and retries with the same identity. See [voice agenda requests](docs/voice-agenda.md).

## 工作台

| Section | Purpose |
|--------|---------|
| 长期项目 | Longer-term work; each item links to an absolute project directory so the agent can read progress |
| 短期待办 | Near-term actionable tasks |
| 提醒 | Date-based nudges (birthdays, appointments) |

Add projects in the UI with a name + absolute path (e.g. `/Users/eddy/Documents/…`). Paths are validated before save. Voice requests can update the personal project record; directory inspection belongs to the separate daily project-progress check. Firstmate retains projects long-term, deletes only confirmed completed personal tasks / one-off reminders, and asks for clarification when recognition or the target is ambiguous.

## What is / isn’t automatic

| Piece | Automatic? |
|--------|------------|
| Speech → text | Yes (local Whisper) |
| Transcript → durable local request → Firstmate inbox | Yes (stable request identity) |
| Request → Firstmate personal context | Firstmate applies it and publishes the actual outcome |
| Weekday 9:00 launch | Yes (after `./schedule/install-launchd.sh`) |
| Inject into the open IDE chat | **No** — not supported by Cursor |

My does not launch an independent agenda-editing agent. Manual dashboard editors remain available with their existing concurrency protection. The separate music inspiration shortcut keeps its record-only notebook behavior.

## Data

```
data/
  todos.json         # inactive migration residue; not read or written by the server
  .agenda-requests/  # private durable voice requests, transcripts and outcomes
  .firstmate-context.json # private binding to the existing Firstmate home
  inbox.md           # preserved legacy notes; not the new voice delivery queue
  inbox-archive.md   # preserved historical voice archive
  .agent-status.json # separate project-progress job status
  daily/ weekly/     # summaries (optional later)
  tmp/               # voice temp + serve/launchd logs
schedule/
  start-weekday.sh   # start server + open workspace
  install-launchd.sh
  uninstall-launchd.sh
.agent/skills/           # canonical personal skill source
.cursor/personal-skills  # compatibility link to .agent/skills
```

## Notes

- Open in **Chrome or Edge** at `http://127.0.0.1:8765` (not Cursor Simple Browser).
- First Whisper load can take a few seconds.
- Pomodoro keeps counting across Focus ↔ 工作台.
- Use `./start.sh` so the venv with `faster-whisper` is used.
