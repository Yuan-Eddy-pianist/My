# Your portable agent workflow

This folder is the home for your Firstmate workflow. Keep it inside `My`; it can be copied to a different parent folder or username.

## Use it here

Run `firstmate` from any folder to open Firstmate in WezTerm. It starts Firstmate when needed and reattaches to the primary conversation, leaving worker panes alone. `firstmate --status` checks whether the primary is running without opening a window; `firstmate --help` lists the options. Setup installs this command in `~/.local/bin`; if your shell does not include that directory on PATH, run `~/.local/bin/firstmate`.

The command opens WezTerm with Herdr displaying your workspace. Closing that window detaches without stopping the agents. `firstmate --headless` starts or checks the primary without opening a window.

The setup lives here:

- `firstmate/`: the real upstream Firstmate checkout, your preferences, task records, and projects.
- `firstmate/projects/`: project repositories, including the tested `workflow-demo`.
- `sessions/primary/` and `sessions/crew/`: Firstmate and new worker conversations.
- `config/`: portable Pi preferences, terminal appearance, and the Herdr skill.
- `scripts/`, `installers/`, and `Setup.command`: restore and launch tools.
- `docs/`: the original setup guide, verification evidence, and installed versions.
- `archives/`: preserved session/runtime records and settings backups from migration.
- `.runtime/worktrees/`: future Treehouse working copies. Prepare transfer checks for them and never deletes them.
- `local/`: generated machine bindings and diagnostic logs; Setup rebuilds their paths.

Passwords, Pi OAuth credentials, Codex credentials, and GitHub's Keychain login remain in the operating system's normal account stores. They are not exported into this workflow folder.

## Copy to another device

1. Ask Firstmate to finish and clean up its workers.
2. Open **Prepare transfer.command**. It refuses active work, stops the idle primary session, checks for linked worktrees, and captures the current portable settings. If a project still has linked worktrees, it stops and asks you to have Firstmate inspect them. It never deletes working copies or discards unmerged work.
3. Copy your entire **My** folder, including hidden files and folders. Use a filesystem copy or archive that includes `.git`. A Git clone of My is not an equivalent backup: this private Firstmate checkout, its projects, and conversations are intentionally ignored by My's Git repository. Project symlinks outside My do not include those projects: copy those repositories separately and update their links on the destination.
4. On the destination open **Setup.command**, then sign in to Pi, GitHub, and Codex on that device.
5. Run `firstmate`. Setup rebinds project links into the old My tree to their locations inside the new copy, and refuses missing or unresolved external projects. Historical conversations remain available even when a fresh primary session is appropriate. Transfer and Setup archive copies of supervision state while keeping durable outcome records in place. Unprepared state blocks relocation; restarting Firstmate invalidates the transfer-ready marker.

You can continue using this computer afterward by running `firstmate` again. Avoid concurrently synchronizing the same live Git repositories or runtime state between two running machines; make a stopped snapshot, then choose which copy you are working in.

## Destination requirements

**Another Mac:** install Homebrew first from https://brew.sh if absent. Setup installs the CLI dependencies and WezTerm, restores configuration, and integrates Herdr with Pi/Codex. Apple may ask you to approve WezTerm through Privacy & Security. Google Chrome must be installed for the browser tool.

**Linux:** install WezTerm, a current Node.js (22.19+), npm, Python 3, Bash 5+, Git, GitHub CLI, jq, curl, fd and ripgrep using the supported installation method for your distribution. Then run `sh Setup.command`. The installer provisions the agent tools; `firstmate` requires WezTerm for its window. Install Chrome/Chromium and check the browser tool for that distribution.

**Windows:** this complete Firstmate distribution uses Unix shell scripts. Plan to run the Linux route inside WSL2; native Windows migration has not been implemented or tested here. Keep working repositories in WSL's Linux filesystem. GUI/browser integration needs a check on that particular machine.

Only this Mac's configure, relocation, launch, and transfer checks have been executed. The new-device installer is provided for rebuilding the environment; it has not been tested on hardware or operating systems you have not selected yet. It uses pinned npm versions and Firstmate's pinned Treehouse installer. Herdr and no-mistakes use their bundled official installers, which resolve a current release when those tools are absent.

## Sign in after restore

- Start `pi`, enter `/login openai-codex`, and complete the browser sign-in.
- Run `gh auth login` for GitHub.
- Run `codex login` for the alternate official CLI.

If setup changes machine paths or the folder moves again, rerun `Setup.command --configure-only` after checking that all workers have finished. Existing settings are backed up before replacement. The original My application, its files, and its existing changes are separate from this folder.

## What was verified before the move

Pi used the Codex subscription successfully. Firstmate delegated and completed a local task through Treehouse, tracked it, tested it, landed it, and cleaned up. Five tests passed. Browser control, Lavish feedback, web search, and quota reads passed. No production repository or project-specific remote CI pipeline was configured.

Source documentation: [Firstmate](https://github.com/kunchenguid/firstmate), [Herdr](https://herdr.dev/docs/), [Treehouse configuration](https://github.com/kunchenguid/treehouse/tree/v2.0.1), [Pi](https://github.com/earendil-works/pi).

## Native Codex compaction

Native compaction is installed for Pi’s `openai-codex` provider. Automatic compaction stays enabled, and `/compact` uses the native checkpoint mechanism. Continue checkpointed sessions with the same model. See [Native compaction](docs/Native%20compaction.md) for verification, recovery, and restore details.

## Model defaults

Firstmate defaults to **GPT-6 Astra** (`openai-codex/gpt-6-astra`). Workers default to **GPT-6.1 Sol** (`openai-codex/gpt-6.1-sol`). Both use high reasoning.

To override a worker for one task, say: “Use GPT-6 Astra for this task’s worker.” An explicit task override takes priority over routing rules and the default.

The Firstmate default is stored in Pi’s user settings and `config/pi-profile.json` for restoration. This is also the default for standalone Pi sessions. The worker default is stored separately in `firstmate/config/crew-dispatch.json`.

Defaults apply to new sessions and newly dispatched workers. Reattaching or resuming a conversation preserves its selected model. For a conversation that has not undergone native compaction, `/model openai-codex/gpt-6-astra` switches the current session. Keep a native-compacted conversation on its original model; use a fresh conversation to switch models.
