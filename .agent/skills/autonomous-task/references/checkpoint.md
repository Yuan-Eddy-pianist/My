# Durable run record

Create a task-specific folder such as `.autonomous-task/runs/<unique-run-id>/` in the approved workspace. Resolve its absolute path for scheduling. Choose a different writable project location if needed; keep it outside the installed skill folder. The coordinator owns shared records, with writes completed atomically where supported.

Use these small files; do not repeatedly copy the conversation:

## contract.md — internal working record

This file is for the agents. Do not paste its schema into chat or make the human read it to approve the work. Use the real grill-me conversation and the short readable agreement in `SKILL.md` for user-facing alignment. Internal rigor must not become a dense approval document.

Start the file with **Approved agreement**: preserve the exact short summary the human confirmed, plus any subsequent clarifications. Then maintain **Agent verification details** using the fields below. Each criterion must map to a promise, constraint, or necessary implication of that visible agreement. Translation cannot silently add scope, permissions, or user obligations. Record the actual confirmation; a draft or an unanswered question is not approval.

- Run ID, objective, audience, deliverables and their locations.
- Required scope, explicit exclusions, and relevant source material.
- Contract version, user approval evidence for the readable agreement (message reference or faithful excerpt), and approval time. Do not seek a second approval solely for this internal translation.
- One entry per required criterion: stable ID, pass condition, evidence method, and evaluator. Use observable thresholds or a calibrated rubric. Record human evaluation only when explicitly reserved.
- Task-specific scrutiny standard: what a superficially compliant failure would look like, pivotal assumptions, meaningful alternative/tradeoff, and consequential failure modes.
- Optional improvements listed separately.
- Allowed actions, resource limits and their accounting method, plus known runtime limitations.
- Completion rule: every required criterion verified on the final candidate, substantive approach and candidate challenges, resolved material objections, and a fresh final discriminator verdict, plus any explicitly reserved human judgment.
- Changes to the contract with user decision and affected evidence.

## state.md

- Run and workspace identity; status: `interviewing`, `running`, `waiting`, `blocked`, `budget_exhausted`, `paused`, `cancelled`, or `complete`.
- Last update, owning coordinator identity, ownership/liveness information, and current contract version.
- Current round, strategy, last meaningful progress, and consecutive rounds without progress.
- Candidate identity and evidence/review locations; outstanding criterion IDs.
- Actual tool-returned worker/job identities, delegation call/result receipts, role briefs used, output/review references, writable areas, and liveness. Track generator, primary discriminator, and fresh final discriminator separately; invented role names do not prove delegation.
- Review phase: approach challenge, candidate stress test, generator response/retest, or final independent review; open challenge IDs and responses still awaiting independent closure.
- Continuation mechanism, returned scheduler/goal IDs, verified active state, interval, availability limitations, and cleanup still required.
- Cumulative resource usage across all agents, rounds, and resumes; measurement availability and estimates clearly distinguished. Track agreed limits conservatively; if a hard cost cap cannot be measured or enforced, resolve that before starting work that could exceed it.
- Last completed step, exact next useful action, and current blocker/resume condition if any.

## rounds/<round-id>.md

- Contract version and stable candidate revision or hashes. For uncommitted files use content hashes or an immutable copy rather than just a branch name.
- Generator handoff: approach/alternative and key assumptions, changed artifacts, addressed criteria/challenges, checks/evidence, and known uncertainties. Record concise decision rationale, not private internal reasoning.
- Discriminator identity and returned report; challenge hypotheses and why they matter to the approved outcome, independent probes attempted and observed results, and the credible alternative/tradeoff examined.
- Verdict per criterion: `PASS`, `FAIL`, or `UNVERIFIED`, supporting evidence, and concrete defect or missing proof. Keep suggestions separate.
- Challenge verdict (`REVISE`, `READY`, or `BLOCKED`), separate from criterion statuses.
- Challenge ledger: stable ID, threatened criterion/outcome, failure mechanism/evidence, material impact, resolution test, generator response (revise/investigate/rebut), and discriminator retest/closure. Carry open challenges across rounds.
- Remaining material uncertainty and why review is or is not sufficient; strongest attempted challenge and residual limitation.
- Disputes and how evidence resolved them; next changes and whether the round made meaningful progress.

Evidence may include command output, authoritative source references, rendered artifacts, or observed behavior. Record enough to locate and reproduce a check without storing unnecessary private data.

## operations.md

For consequential external operations, record intention before execution and confirmed outcome afterward: operation ID, action/target, scope authorization, candidate/contract version, supported idempotency key or lookup method, and returned external identifier. Never store credentials. On resume reconcile uncertain operations against actual state before repeating them.

At completion, retain the final criterion evidence, substantive challenge and response history, actual worker receipts, fresh final review, and deliverable identity. Compact stale narrative if needed, but preserve decisions, remaining work, resource totals, and information required for safe recovery.
