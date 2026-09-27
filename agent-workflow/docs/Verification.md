# Firstmate workflow smoke — 2026-09-27

## Original task: recovered
- Session start locked cleanly; no initial wakes. Created only `projects/workflow-demo` (`git init -b main`, initial commit `8e21a91f6c4f6a5b839554009dc53bf38fa6a96d`), registered `local-only off`, no remote.
- Task `normalize-title-smoke-s7`: filed with `bin/fm-tasks-axi.sh add`, scaffolded with `bin/fm-brief.sh ... --mode local-only`, and attempted `bin/fm-spawn.sh normalize-title-smoke-s7 projects/workflow-demo --mode local-only --yolo off --harness pi --model openai-codex/gpt-6-sol --effort high`. The macOS Bash 3.2 `BASHPID: unbound variable` backlog-transition failure removed the task metadata after allocation. Orphan endpoint `firstmate:w2:p2`, Treehouse copy `/Users/eddy/.treehouse/workflow-demo-535c99/1/workflow-demo`. The worker nevertheless committed `fa7fa28598ee31a05821147090ee8a14fef1892c` on `fm/normalize-title-smoke-s7`.
- Before landing, the copy was clean; `(cd /Users/eddy/.treehouse/workflow-demo-535c99/1/workflow-demo && node --test)` passed 3/3; `git -C projects/workflow-demo merge-base --is-ancestor main fa7fa28598ee31a05821147090ee8a14fef1892c` returned success, and main was clean with no remote. With the specific recovery approval, `git -C projects/workflow-demo merge --ff-only fa7fa28598ee31a05821147090ee8a14fef1892c` advanced main exactly to that commit.
- `herdr agent get w2:p2` identified the original Pi session; `herdr agent prompt w2:p2 '/quit'` exited only that process, verified by its shell prompt and absence from `ps`. After proving the copy clean and its commit landed, `treehouse return /Users/eddy/.treehouse/workflow-demo-535c99/1/workflow-demo` returned it without force (`available` in Treehouse). `bin/fm-tasks-axi.sh done normalize-title-smoke-s7 --note ...` and a corrected archived body recorded the manual recovery honestly; original guarded teardown was unavailable because metadata had been removed. No tracked Firstmate code or BASHPID value was changed.

## Second tracked task: normal lifecycle completed
- Homebrew Bash `/opt/homebrew/bin/bash` is 5.3.20 and first on PATH; Pi's shellPath was persisted during setup. Task `title-edge-tests-v2`: `bin/fm-tasks-axi.sh add ... --kind ship --repo workflow-demo`; `bin/fm-brief.sh title-edge-tests-v2 workflow-demo --mode local-only`; resolver returned `off`.
- `PATH="/opt/homebrew/bin:$PATH" bin/fm-spawn.sh title-edge-tests-v2 projects/workflow-demo --mode local-only --yolo off --harness pi --model openai-codex/gpt-6-sol --effort high` succeeded: Pi worker `firstmate:w3:p2` in isolated Treehouse copy `/Users/eddy/.treehouse/workflow-demo-535c99/1/workflow-demo`; backlog automatically In flight. `bin/fm-crew-state.sh` and `bin/fm-peek.sh` confirmed isolation, active implementation, then `done: ready in branch fm/title-edge-tests-v2` at commit `a6c120c594fbe5dbc68fa4561a752142a5f64024`.
- `(cd /Users/eddy/.treehouse/workflow-demo-535c99/1/workflow-demo && node --test)` passed 5/5, including empty, all-whitespace, and Unicode whitespace input; `git merge-base --is-ancestor main fm/title-edge-tests-v2` succeeded and main was clean. `bin/fm-lease.sh claim title-edge-tests-v2`; `PATH="/opt/homebrew/bin:$PATH" bin/fm-merge-local.sh title-edge-tests-v2` guarded fast-forwarded main `fa7fa28 -> a6c120c`. `PATH="/opt/homebrew/bin:$PATH" bin/fm-teardown.sh title-edge-tests-v2` completed, reaped the worker's lingering copy-local processes, returned the Treehouse slot, removed its task metadata, and automatically marked the backlog Done; lease released. No `--force` or discard was used.
- Final check: `node --test` on local main passed 5/5; main clean at `a6c120c594fbe5dbc68fa4561a752142a5f64024`, no remote; Treehouse slot available; both tasks Done, `bin/fm-tasks-axi.sh ready` found 0 queued tasks. No other project was changed.

## Other integration checks
- Pi 0.87.1: OpenAI Codex OAuth readiness returned ready; a live subscription request succeeded using gpt-6-sol.
- GitHub CLI: authenticated as Yuan-Eddy-pianist; Firstmate dependency detection passed after login.
- Herdr 0.9.1/protocol 22: dedicated firstmate session running; Pi integration v9 and Codex integration v8 installed.
- WezTerm 20240203-110809-5046fc22: official release checksum verified, installed through Homebrew, approved by the user through macOS, settings parsed, and the Firstmate window launched successfully.
- Lavish 0.1.79 and chrome-devtools-axi 0.1.35: isolated Chrome opened the local review page, clicked its test button, and submitted a synthetic message using Send & End; lavish-axi poll received the exact message and confirmed session closure. Isolated browser stopped afterward.
- Pi web-access 0.32.0: live search returned https://herdr.dev/docs/ using the OpenAI provider.
- quota-axi 0.1.55: live Codex quota read succeeded.
- no-mistakes 1.79.0: daemon running; doctor passed its core system and agent checks. No project-specific remote pipeline was initialized.
- GNHF 0.1.50: installed, configured for Pi with the Codex provider, and command interface verified; an unattended iterative run was not started.
- Firstmate source checkout remains unchanged at 5a9880b42f2556ac63b8371455241c0262ad8ffc. Private settings and demo state are gitignored.

## Scope limits
No production project has been selected. GitHub push, PR creation, remote CI, and a project's no-mistakes pipeline were not exercised. Both demo tasks stayed local; the successful second task is the evidence for normal delegation, isolation, tracking, testing, landing, and cleanup.

## Final workspace tidy
The original empty test workspace was closed after verifying that its process had stopped, its commit was landed, and its Treehouse slot was available. The primary Firstmate Pi session remains running and idle in WezTerm.

## Standalone Codex CLI
Codex CLI 0.157.1 was repaired after npm silently omitted its optional Mac binary on a timed-out download. The replacement package passed the official npm SHA-512 integrity check; installation completed from the local cache. `codex --version` returned 0.157.1 and `codex login status` returned Logged in using ChatGPT.
