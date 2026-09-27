---
name: autonomous-task
description: Run long tasks with dedicated generator and adversarial discriminator agents, human-agreed standards, critical challenge and revision, durable checkpoints, and supported automatic continuation. Use for sustained work that must survive independent scrutiny before automatic completion.
---

# Autonomous Task

Agree on success with the human, then pursue a defensible result through generation, adversarial challenge, revision, and recovery. The discriminator's job is to expose why a plausible solution may be wrong, weak, or inferior within the agreed objective. Checklist verification is necessary but is not sufficient for completion.

This skill defines a workflow; it does not supply a scheduler, persistent process, or additional permissions. Creating or editing the skill does not start a task. A delegated worker follows its assigned role and does not recursively launch this entire workflow.

## 1. Reach shared understanding through the real grill-me interview

Inspect the task, files, available tools, and existing decisions before asking about facts. Reuse approved decisions and authorization on follow-up or resume; do not restart the interview.

**Load and follow the actual grill-me skill, not an approximation.** In this shared skill collection, read [grill-me](../grill-me/SKILL.md). It invokes `/grilling`, so also read and follow the actual [grilling instructions](../grilling/SKILL.md). If installed elsewhere, resolve those skills through the host's skill catalog rather than assuming this machine's absolute paths. If they cannot be found, report the missing interview skill; do not label an improvised questionnaire as grill-me.

Apply that interview as a conversation:

- Ask **one decision question per turn**, give your recommended answer and a short reason, then wait. A question containing several unrelated choices still counts as several questions; do not bundle them.
- Follow the user's answer down the relevant decision branch. Look up discoverable facts instead of asking the human to supply them. Ask the human about consequential goals, preferences, tradeoffs, and limits; choose routine execution details yourself.
- Keep each interview message brief: acknowledge the relevant answer if useful, then the next question and recommendation. Do not append a contract, a requirements matrix, or a preview questionnaire between questions.
- Clarify what would make the result useful and what a disappointing result would look like in the user's own terms. Where helpful, show one concrete example. Let the agents translate this into technical checks, failure probes, and alternative comparisons; do not ask the user to design the evaluation machinery.
- Resolve material scope, constraints, and any user-requested time/spending limits. Explain actual runtime limitations only when relevant. Do not make the interview a checklist of every internal workflow setting.

### Show a readable agreement, not the agents' contract

Once the meaningful decisions are resolved, briefly summarize the shared understanding in ordinary language. This is the user-facing approval surface:

- Start with one sentence saying what the user will get.
- Use about 3–5 short, flat bullets for what it must do, how the user will recognize success, and important boundaries or limits. Aim for about 150 words or fewer; use more only when needed to preserve a material condition. Never hide a consequential tradeoff or permission request to satisfy a word count.
- Describe autonomous follow-through in one plain sentence: one agent builds, another challenges the result, and they keep improving it until the agreed outcome is met or a real blocker/limit is reached.
- End with one natural shared-understanding question, such as "Does that capture what you want?" If the user already explicitly confirmed this same understanding and authorized starting, do not seek ceremonial approval again; proceed.

Use the user's vocabulary. Keep criterion IDs, evidence matrices, evaluator assignments, hashes, run states, and review verdict codes out of this summary unless the user asks for the technical detail. Important task-specific numbers or technical requirements the user cares about still belong in it. Do not require the user to open or approve `contract.md` or a long linked document before starting. Offer detail progressively when requested, not as mandatory reading. Do not present unresolved choices as an agreed plan.

### Keep the rigorous working record for the agents

After confirmation, capture the approved readable agreement and translate it into the internal `contract.md` described in [checkpoint.md](references/checkpoint.md), then start execution. Draft notes may be kept during the interview; they are not approval. Each internal criterion needs an ID, pass condition, and evidence method traceable to the approved outcome. Include relevant decision quality, consequential failure modes, and the challenge-and-response completion gate; preserve agreed limits and allowed actions. A requested work period funds useful investigation, experiments, and alternatives, never idle padding. An unspecified cap is not unlimited spending authority.

The readable agreement and internal criteria express the same scope. Internal bookkeeping cannot introduce a new deliverable, hidden restriction, spending authorization, or human approval gate. If the translation exposes a missing consequential decision, ask that one question; otherwise the user need not review the translation.

Freeze the approved meaning and contract version. Agents cannot lower standards, drop requirements, or add deliverables. The discriminator may strengthen tests and expose flaws that threaten the agreed outcome even when the initial checklist omitted them. A new preference or expanded outcome requires a short, concrete proposed change for the human; keep unrelated work moving. Record user steering and re-evaluate affected evidence.

## 2. Launch the actual workers

Read [runtime.md](references/runtime.md) and [adversarial-review.md](references/adversarial-review.md). Set up the run record and supported continuation, then act immediately.

**The parent is the coordinator. It MUST invoke the host's real agent-delegation tool twice: once to launch a generator worker and once to launch a discriminator worker in distinct contexts.** If `collaboration.spawn_agent` is available, make two separate calls; otherwise use the host's actual equivalent and documented schema. Do not invent tool names. Do not substitute the coordinator for either worker, alternate role labels in one context, or present two written personas as two agents.

Record the tool-returned agent/job identifiers and launch receipts in `state.md`, then give the user a brief update identifying which worker generates and which discriminates. If a host returns no persistent ID, retain the actual delegation call/result reference; a made-up name is not evidence of a launch. If either required launch fails, quiesce any worker already launched, report that requirement as blocked, and preserve preparation work. Never silently fall back to self-review or claim a two-agent run occurred.

Give the workers the role briefs in the review reference. Launch the independent discriminator and fresh final reviewer without inherited conversation history: with `collaboration.spawn_agent`, explicitly set `fork_turns: "none"`; elsewhere use the documented equivalent. Supply curated task material explicitly. A new worker that inherits earlier conclusions is not a blind independent review. If clean context isolation is unavailable, report that limitation and do not count a contaminated review toward the fresh-review gate. The discriminator first receives the objective, contract, constraints, and raw source material so it can identify risks and a competing approach independently; then give it the candidate and necessary rationale. Do not ask it to endorse the generator's preferred answer.

The first generator assignment ends at the approach handoff. The coordinator routes the discriminator’s approach challenge and generator response, then explicitly releases major implementation. Reversible investigation may continue while waiting.

The coordinator owns the contract, state, scheduling, and routing. The generator owns deliverable edits. The discriminator owns its challenges and independent tests; it may create isolated test artifacts but cannot edit the deliverable or standard. Use stable candidate snapshots or suspend candidate edits during review. Route substantive objections to the generator rather than answering for it.

## 3. Challenge the approach, then the candidate

Follow the full protocol in [adversarial-review.md](references/adversarial-review.md). Two review opportunities are required: challenge the proposed approach before major investment, and stress-test the actual candidate. These are distinct investigations, not an arbitrary quota of revisions.

1. **Propose and challenge:** the generator outlines the approach, consequential assumptions, and a credible alternative. Independently, the discriminator identifies the most damaging plausible objection, proposes a discriminating experiment, and challenges tradeoffs. The generator responds before expensive or hard-to-reverse implementation; useful reversible investigation can proceed alongside this exchange.
2. **Generate:** produce a candidate against the contract and open challenges. Record its revision or hashes, evidence locations, uncertainties, and a concise decision rationale.
3. **Discriminate:** try to falsify the central claims and reveal material weaknesses using raw evidence, counterexamples, realistic edge cases, and alternative comparison. Then audit required criteria. Report both criterion status (`PASS`, `FAIL`, `UNVERIFIED`) and the independent challenge verdict (`REVISE`, `READY`, `BLOCKED`). All criteria can read `PASS` while a substantiated challenge still requires `REVISE`.
4. **Respond and revise:** the generator answers every material challenge by changing the artifact, producing new evidence, or rebutting the objection with evidence. Acknowledgment, confident prose, and cosmetic edits do not close a substantive issue. The discriminator retests the response and closes or reopens the challenge with reasons. The coordinator cannot waive it merely to finish.
5. **Checkpoint and continue:** record the full challenge/response outcome, progress, and next valuable investigation. A green test suite, a finished round, or a persuasive summary is not a stopping rule.

Use targeted checks tied to the task; do not add a generic exhaustive audit. Rerun checks affected by revisions and required final checks. Treat missing access or evidence as unverified. Preserve evidence only while the relevant candidate and dependencies remain unchanged. Address unsupported objections with a focused check; do not manufacture defects or let speculation create unlimited work.

Measure progress by better-supported decisions, newly proven criteria, resolved defects, reduced uncertainty, or evidence ruling out a plausible approach. After three consecutive rounds without meaningful progress, diagnose and change strategy, decomposition, experiment, or tools. This is a strategy trigger, not automatic termination. Continue while a material uncertainty or actionable in-scope weakness remains and resources permit it.

Effort must track the difficulty and stakes of the objective. Use available time to pursue the strongest remaining challenge and improve the solution, not to pad runtime or repeat checks. A fast run is defensible only when the recorded adversarial work supports it. Give milestone updates describing the strongest current objection, the generator's response, and the remaining uncertainty.

## 4. Recover and stop truthfully

- **Transient failure:** checkpoint and retry with bounded backoff. Inspect external state before repeating a possibly successful mutation; continue independent work meanwhile.
- **Hard blocker:** after diagnosis and reasonable alternatives, record exactly what unavailable access, decision, or external change prevents progress. Notify once. Retain only useful supported checks for an observable resume condition; do not repeatedly ask an unanswered question or rerun the same failed action.
- **Agreed resource limit:** checkpoint and pause, reporting unfinished criteria and open challenges. Do not reset the allowance on resume or declare incomplete work successful. Host limits also apply.
- **User pause/cancel:** interrupt workers and disable the appropriate wakeups. Preserve state; do not reactivate against the user's instruction.
- **Interruption:** reconstruct actual state under the approved contract. Reconnect or relaunch both real workers, including open challenges and untested responses. Resume automatically only through verified host support.

Follow native goal tools' own status rules. Do not mark a native goal complete to escape its continuation loop.

## 5. Earn automatic completion

Before declaring completion, all of the following must be true:

- Actual generator and discriminator launches and returned work are recorded.
- The approach challenge and candidate stress test contain substantive, task-specific evidence; an empty review or "looks good" verdict does not count.
- Every required criterion passes on the identifiable final candidate.
- Every material challenge is resolved by revision and retest, or a documented evidence-based rebuttal. Required proof that remains unavailable cannot be reclassified as an acceptable uncertainty.
- A **fresh discriminator context**, given the contract, raw sources, and final candidate but no earlier verdicts initially, independently attempts to defeat the result. After that first assessment, give it prior challenges to check closure and regressions. Its own report must justify `READY`; if it finds a material issue, return to the generator and retest the repair. Reuse this final reviewer for repairs; do not keep recruiting reviewers until one agrees.
- The final reviewer identifies the strongest surviving limitation, explains why no material in-scope weakness remains unresolved, and states why the chosen approach is defensible against the credible alternative. No outstanding human judgment explicitly reserved in the contract remains.

Complete automatically when these gates hold. Otherwise continue or report the specific blocker/limit. Do not impose a minimum elapsed time, require fabricated defects, or force a revision to a sound result merely to look rigorous.

Save final evidence and challenge dispositions, mark the run complete, stop workers and continuation, and complete an associated native goal using its real tool. If cleanup fails, retain completed state so future wakeups only retry cleanup. Deliver the artifact with a short account of what the discriminator challenged, what changed or survived scrutiny, and remaining limitations; this is a decision/evidence summary, not private internal reasoning.
