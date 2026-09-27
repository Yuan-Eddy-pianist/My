# Local voice input for Pi

This is **not** My's `/api/voice` note inbox. It records in the Pi terminal with
`ffmpeg`/AVFoundation, calls `serve.transcribe_path` from My's existing local
Whisper backend, and appends its output to the **current editable Pi draft**.
It never submits a message. My's browser voice notes are unchanged.

## Use

- On macOS, install `ffmpeg`; install My's Python requirements in `My/.venv`
  (`./start.sh` normally sets this up). The existing local Whisper weights must
  be cached. The helper sets Hugging Face offline mode when launched by Pi.
- In a trusted Pi session started in `My`, `.pi/extensions/my-voice.ts` loads
  automatically. Repeat `/voice` or `Ctrl+Shift+V` to start and stop recording.
  Pi shows recording/transcription status. Edit the appended draft, then send
  manually. Stop after speaking (max 90 seconds). Silence or errors preserve
  the draft. Temporary WAV files live only in `My/data/tmp/` and are removed.
- The default AVFoundation input is `:default`. Override
  `MY_PI_VOICE_DEVICE=:2` (audio index from
  `ffmpeg -f avfoundation -list_devices true -i ''`) when the system default
  is not the desired microphone. Mic permission belongs to the Pi/terminal
  process's OS identity; grant it in macOS Privacy & Security if requested.
- For a Pi session in **another** project, Firstmate can activate this file
  without changing that project's code: add its *absolute* path to the user
  Pi agent `settings.json` `extensions` resource array, then run `/reload` in
  the existing Pi terminal (or start a new Pi with `--extension <absolute path>`).
  Do not copy the file without its sibling `pi_voice/transcribe.py` and
  `serve.py`: paths are resolved relative to this project. After merge, point
  the setting at the stable checkout path, not a disposable worktree.
- In an isolated worktree with no `.venv`, set `MY_PI_VOICE_PYTHON` to the
  existing My virtualenv's `bin/python` **when launching Pi**. In the regular
  My checkout, the extension uses its `.venv/bin/python` automatically.
  A running Pi process does not inherit environment changes made later in
  another shell. If needed, set `MY_PI_VOICE_PYTHON` in the Pi launcher before
  restarting that Pi process. No path/settings changes outside this worktree
  are performed by this integration.

The local Silero VAD shipped with My's `faster-whisper` dependency rejects
ambient noise before MLX Whisper, which can otherwise hallucinate text from
non-speech recordings. Neither audio nor transcript goes to a cloud STT API.
