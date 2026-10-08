# Native Codex compaction in Pi

Installed: `@ogulcancelik/pi-codex-compaction@0.1.5` with Pi 0.87.1.

## Everyday use

Continue using Firstmate normally. Pi still decides when automatic compaction is needed; the extension replaces its text-summary step with a native Codex checkpoint when using the `openai-codex` provider. You can also type `/compact` in Pi's input box. Do not type it at a shell prompt.

The existing Firstmate session was reloaded after installation. New Pi sessions load the extension automatically. No API key was added; the tested requests used the existing Codex provider sign-in.

The extension displays native-compaction progress in interactive Pi. If its native request fails, it cancels that compaction and preserves the previous history; it does not silently switch to Pi's text summarizer. Automatic compaction remains enabled with the existing/default token budgets.

## Model changes and recovery

A native checkpoint is tied to the Codex model that created it. Continue that session with the same model. Before switching models/providers, have Firstmate save its current work and decisions, start a fresh session, and then choose the new model. An opaque checkpoint cannot be treated as a portable plain-text summary.

Keep the extension installed when resuming sessions that contain its native checkpoints. Removing the extension would not convert those checkpoints into readable summaries. For rollback, use a fresh session rebuilt from Firstmate's durable records, or deliberately restore the pre-enable conversation snapshot after reconciling any work done since it was taken.

A copy of the primary conversation before enablement and the previous non-secret settings are in `archives/before-native-compaction-20260928-115416/`. Credentials were not copied.

## Portability

`Setup.command` installs the pinned extension. `config/pi-profile.json` records the package and automatic-compaction setting; the transfer helper now retains the compaction settings too. Reinstall and sign in on the destination as usual. The extension applies to Pi's Codex provider; other providers retain their normal behavior.

## Verification

The synthetic tests verified actual native encrypted checkpoints, recall of six facts originally supplied through a tool result, repeated compaction, and reopening the saved session. Separate automatic-compaction testing exercised the real Firstmate post-compaction hook with synthetic startup data in an isolated workspace, then verified delivery of a fresh operational digest and preservation of the approval rule.

The production supervisor and worker-control scripts were not invoked by these tests. The live conversation was reloaded to activate the extension, but was not deliberately compacted. These are functional integration checks, not a comparative benchmark of memory quality or a guarantee that all details survive every compaction.

GPT-6 Sol and GPT-6 Astra both passed the retention, repeated-compaction, and restart checks. The automatic-compaction and Firstmate-hook test used GPT-6 Sol. The detailed `native-compaction-*.json` reports are in the portable kit’s `docs/` folder.

Sources: [extension documentation](https://github.com/ogulcancelik/pi-extensions/tree/main/packages/pi-codex-compaction), [OpenAI compaction documentation](https://developers.openai.com/api/docs/guides/compaction).
