> Current location and transfer instructions: see ../README.md.

# Your Firstmate workspace

## Open it

Run `firstmate` from any folder to open Firstmate in WezTerm. Use `firstmate --status` to check the primary session without starting it or opening a window. If the command is not on PATH, use `~/.local/bin/firstmate`. Herdr displays the workspace inside WezTerm.

WezTerm's first launch was approved through macOS Privacy & Security. If that warning appears again after an update, review the app there and use the app-specific **Open Anyway** option when you choose to trust that installation. [Apple explains this approval](https://support.apple.com/en-gb/102445).

Talk to the **Firstmate** Pi session. Tell it what you want to achieve, provide the project location, and describe how you will judge success. Firstmate handles task records, worker sessions, isolated working copies, and progress checks.

Try this first:

> Show me the workflow-demo project and explain what the setup test did. Then help me choose a small first task for my own project.

For a real project:

> Add my existing project at [local path or GitHub URL]. Inspect it, explain the proposed work, then implement [one small change] and verify it. Keep the finished changes ready for my review.

The setup uses the real [Firstmate distribution](https://github.com/kunchenguid/firstmate), with current supported integrations. It is adapted from Kun Chen's workflow rather than a new imitation of Firstmate inside the Codex desktop app.

## What each part does

- **WezTerm:** the terminal window you open.
- **Herdr:** keeps the workspace and agent processes running, and shows their state.
- **Pi:** the agent interface used by Firstmate and its workers. It is signed into the OpenAI Codex provider using your subscription.
- **Firstmate:** the supervisor instructions, task lifecycle, and coordination tools.
- **Treehouse:** gives workers separate Git working copies.
- **Lavish:** opens visual artifacts for annotation and returns your feedback to the agent.
- **chrome-devtools-axi:** lets an agent test browser behavior.
- **gh-axi and GitHub CLI:** GitHub operations using your completed login.
- **tasks-axi:** durable task records.
- **quota-axi:** reads provider quota information.
- **no-mistakes:** validation service for projects using its delivery pipeline.
- **GNHF:** an optional iteration runner, configured to use Pi with your Codex provider. Ask for a concrete objective and an iteration or token limit before starting it.
- **Official Codex CLI:** an alternative standalone agent; it is separate from Pi.

New Firstmate sessions default to `openai-codex/gpt-6-astra`; newly dispatched workers default to `openai-codex/gpt-6.1-sol`. Both keep high reasoning. You can override a worker for a particular task by telling Firstmate the model to use. Resumed conversations preserve their selected model; see the model defaults section in ../README.md. This provider successfully answered a test request through subscription authentication. A separate API key was not configured. Your desktop app remains available alongside this terminal workflow.

Pi's web-access extension is installed. The Codex fast-mode extension is installed but off by default; its supported model list is narrower than Pi's model catalog. Firstmate's Calm display and supervision extensions are loaded from its own checkout. Older compaction customizations were not copied into the current setup.

## Everyday controls

Use the mouse to select Herdr workspaces, tabs, and agent panes. Start with that rather than memorizing shortcuts.

- **Return after closing the window:** run `firstmate` again. Closing a terminal window detaches; it does not stop the agents.
- **Detach deliberately:** press Ctrl+B, release, then Q.
- **Herdr shortcuts:** Ctrl+B, release, then ?.
- **Interrupt Pi's current response:** Escape.
- **Pi commands:** type `/` to browse them.
- **Change Pi's model:** `/model`.
- **Make the display less compact:** `/calm` toggles Firstmate's Calm display.
- **Recover a conversation:** if you are at a shell prompt in the Firstmate directory, run `pi -a --continue`. If choosing among conversations, use `pi -a --resume`.
- **Ask Firstmate to stop work:** state that explicitly. Closing WezTerm does not cancel a task.

The launcher reattaches to the primary conversation using its session identity. If only its shell remains, it resumes Pi there; if the server has no panes, it creates the workspace and resumes Pi automatically. Worker panes in the same folder do not count as primary sessions. The `-a` flag authorizes the trusted checkout's project extensions for that launch.

## Visual review

Ask Firstmate to show a plan, comparison, or result in Lavish when a visual page will help. Annotate the page or write feedback, then choose **Send to Agent**. Use **Send & End** when finished reviewing. Firstmate must have an active feedback poll to receive your comments; the page indicates whether it is listening.

The setup tested browser interaction and a synthetic feedback round trip. The temporary test review was ended afterward.

## Your files and settings

- Firstmate checkout and private working state: `/Users/eddy/Desktop/My/agent-workflow/firstmate`
- Firstmate projects: `/Users/eddy/Desktop/My/agent-workflow/firstmate/projects`
- Your workflow preferences: `/Users/eddy/Desktop/My/agent-workflow/firstmate/data/captain.md`
- Backend, worker routing, and display settings: `/Users/eddy/Desktop/My/agent-workflow/firstmate/config`
- Pi settings: `/Users/eddy/.pi/agent/settings.json`
- Pi settings backup from before this configuration: `/Users/eddy/.pi/agent/settings.before-firstmate.json`
- Herdr settings: `/Users/eddy/.config/herdr/config.toml`
- WezTerm settings: `/Users/eddy/.config/wezterm/wezterm.lua`
- Terminal launcher: `/Users/eddy/.local/bin/firstmate`
- GNHF defaults: `/Users/eddy/.gnhf/config.yml`

Pi uses Homebrew Bash explicitly. This matters because macOS's built-in Bash 3.2 failed one of Firstmate's task-tracking operations during the setup test. The installed Bash 5 resolves that compatibility issue without changing Firstmate's source files.

Your only demo project is local. No GitHub repository was created, no project was published, and standing automatic merge authority is off. A real project's no-mistakes pipeline must be initialized against that project's own tests and remote when you add it. GNHF is installed; no unattended long-running task was started.

## Updates

Ask Firstmate to update itself with `/updatefirstmate`; it has its own recovery-aware update procedure. For the surrounding tools, ask an agent to check versions and perform a controlled update, followed by a quick launch and worker test. Keeping a working version set is more useful than updating everything during active work.

## References

- [Kun Chen's workflow video](https://www.youtube.com/watch?v=iQyg-KypKAA)
- [Kun Chen's full-stack demonstration](https://www.youtube.com/watch?v=kPN564Kol14)
- [Firstmate setup and documentation](https://github.com/kunchenguid/firstmate)
- [Herdr documentation](https://herdr.dev/docs/)
- [Pi](https://github.com/earendil-works/pi)

The videos were the starting references; current upstream documentation and local checks determined the installed configuration. This is not a claim that every historical version or optional customization shown on screen has been reproduced exactly.
