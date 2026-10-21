---
name: teach
description: Build a persistent, source-grounded tutorial of the current codebase through short HTML lessons, real repository exercises, and cumulative learning records. Use when the user explicitly invokes $teach to learn a codebase over time.
---

# Teach: codebase apprenticeship

Turn the current codebase into a living apprenticeship. Build understanding from its real source code, tests, runtime behavior, and design decisions; convert that evidence into short HTML lessons, durable reference pages, deliberate practice, and an evolving record of what the learner can do.

This is one continuous teaching process. Work already happening in the repository is valuable lesson material.

## Put local code first

The learner's requested deliverable and the current local codebase determine the lesson. Start with the concrete behavior, files, symbols, configuration, or data the learner asked about, and trace what the implementation actually does. For an inventory request, identify the actual contents first.

Introduce a general concept only when it helps explain that specific codebase behavior. Keep it brief, attach it to the relevant code or observation, and return to the local implementation. Choose examples and exercises from the repository. Explanation-style samples guide presentation; the local evidence and requested deliverable determine the subject.

## Keep the two locations distinct

The directory containing this `SKILL.md` is the **skill package**. Its format documents are instructions for the agent.

The repository being learned is the **learning workspace**. Store generated state under `<repository-root>/.teach/`:

- `.teach/MISSION.md`: why this codebase matters and what capability the learner wants. Follow [MISSION-FORMAT.md](./MISSION-FORMAT.md).
- `.teach/LEARNER.md`: durable background, goals, and teaching preferences. Follow [LEARNER-FORMAT.md](./LEARNER-FORMAT.md).
- `.teach/CURRICULUM.md`: the evolving map of the system and the learner's current frontier. Follow [CURRICULUM-FORMAT.md](./CURRICULUM-FORMAT.md).
- `.teach/RESOURCES.md`: curated repository evidence and external sources. Follow [RESOURCES-FORMAT.md](./RESOURCES-FORMAT.md).
- `.teach/lessons/*.html`: short, self-contained lessons. Follow [LESSON-FORMAT.md](./LESSON-FORMAT.md).
- `.teach/reference/*.html`: canonical codebase maps, glossaries, flows, and cheat sheets. Follow [CODEBASE-REFERENCE-FORMAT.md](./CODEBASE-REFERENCE-FORMAT.md); use [GLOSSARY-FORMAT.md](./GLOSSARY-FORMAT.md) for the glossary.
- `.teach/learning-records/*.md`: demonstrated learning and corrected mental models. Follow [LEARNING-RECORD-FORMAT.md](./LEARNING-RECORD-FORMAT.md).
- `.teach/assets/*`: reusable stylesheets, quiz widgets, simulators, and diagram helpers shared by generated HTML.
- `.teach/NOTES.md`: lightweight observations about what helped, what confused the learner, and how future teaching should adapt.

Create files and directories lazily. Do not scaffold empty artifacts merely to complete the tree. Mission, learner profile, curriculum state, learning records, resources and teaching notes support the agent's continuity; keep this bookkeeping out of learner-facing navigation unless the learner asks to inspect it.

## Load the selected explanation sources first

At the start of every tutorial session or newly requested tutorial section, use the sibling [explanation-style skill](../explanation-style/SKILL.md). Follow its loader instructions and read all eight complete, verified source samples before composing teaching material. This also applies when resuming an existing `.teach/` workspace. A section means a new requested teaching segment, not each HTML subheading within a lesson.

Keep the exact tested samples: about 5,000 source-text tokens per source, about 40,000 for all eight plus overhead. The individual samples were evaluated separately; **loading them together is provisional and has not been shown to work equally well or better**. Token-budget experiments are unfinished and deferred. If tutorials remain unhelpful, consider token-budget testing or single-source-versus-combination testing as distinct possible improvements, only when the learner wants to resume experiments. The learner stopped the tournament due to review fatigue.

When initializing or updating `.teach/RESOURCES.md`, record these as explanation-style references with a link to the library manifest, separate from factual evidence about the repository. Record the provisional combination and deferred budget work once in `.teach/NOTES.md`; ordinary tutorial feedback may update those notes without requiring another review task. Keep source code and current primary documentation as the basis for technical claims.

The library can also be used independently through `$explanation-style`. Its [experiment status](../explanation-style/references/experiment-status.md) preserves the selection, provenance, and limitations. The personal decision record is [Mynote.md](../../../Mynote.md).

## Begin from context

Before choosing what to teach:

1. Read existing `.teach/` state when present, especially the mission, learner profile, curriculum, and recent learning records.
2. Inspect the repository structure and the code, tests, configuration, documentation, and recent work relevant to the request.
3. Infer a provisional mission from a clear request. Ask about motivation only when the missing answer would materially change the lesson or curriculum.
4. Select a concrete codebase behavior or engineering task at the intersection of the learner's goal and the next reachable challenge. Identify any supporting concepts needed to explain it.

Do not teach the repository in directory order. Follow behavior: entry point to boundary, request to response, event to side effect, model call to tool result, schema to query, failure to recovery.

## Use an evidence hierarchy

For claims about this project, prefer evidence in this order:

1. Current source code and configuration show implementation.
2. Tests and observed runtime behavior show what the implementation does.
3. Repository documentation, ADRs, and comments show intended behavior.
4. Primary specifications and official framework documentation explain external contracts.
5. High-quality secondary sources may supply broader context.

Do not blur implementation, intention, observation, and inference. Label important inferences. Record the inspected revision or working-tree state and the verification date in durable reference pages. A generated lesson is an interpretation of evidence, not the ultimate source of truth.

Saved lessons must expose their sources. Verify current, disputed, niche, or high-stakes claims rather than relying on memory. Stable fundamentals may be explained directly, but connect them to repository evidence and cite a primary source when it materially improves the durable lesson.

## Run the apprenticeship cycle

Adapt the depth to the request, while preserving the learning sequence:

1. **Orient:** connect the current request to the mission and learner profile.
2. **Map:** locate the concrete path through code, tests, data, and runtime boundaries.
3. **Choose:** identify one concrete code path or behavior that answers the learner's request.
4. **Investigate:** inspect evidence, run safe experiments when useful, and separate facts from inference.
5. **Distill:** create or update canonical reference material before it becomes stale prose scattered across lessons.
6. **Teach:** create a focused HTML lesson grounded in the actual codebase.
7. **Practice:** ask the learner to predict, trace, change, test, debug, or explain something real.
8. **Respond:** give prompt, specific feedback based on the learner's result or observable program behavior.
9. **Record:** update curriculum and learning records only when evidence changes what can reasonably be assumed next time.
10. **Revisit:** use retrieval, spacing, and interleaving so recognition does not masquerade as mastery.

Practice may occur across several conversations. Do not mark material learned merely because a lesson covered it.

## Teach this learner

Assume strong foundations in calculus, statistics, linear algebra, digital signal and image processing, computer vision, machine learning, deep learning, and adversarial ML. Assume basic Python familiarity. Do not mistake limited production-software experience for limited technical ability.

Prioritize growth toward:

1. Computer networks
2. Software engineering practice
3. Backend engineering
4. Databases
5. AI agents

The long-term goal is full-stack AI-agent engineering: designing, building, evaluating, deploying, and operating an agent end to end.

Use connections to signal flow, systems, probability, optimization, and computation graphs when they clarify the local implementation. Define unfamiliar software terms on first use. Explain the local component's purpose, then trace its behavior. Keep the intellectual content rigorous and the language accessible.

Use direct, affirmative explanations. State what something is and what it does, then stop when the point is complete. Avoid the rhetorical patterns "It's X, not Y" and "不是……而是……", including trailing contrasts added merely for emphasis. When a distinction is necessary to understand code behavior, state each relevant fact directly. Apply this rule to lesson prose, references, headings, and in-chat teaching; it takes precedence over stylistic habits in the explanation samples.

Do not adopt a mentor persona, use signature phrases, or add pep talk. Do the real engineering work when it is part of the lesson; do not withhold a solution to manufacture difficulty. If urgency requires shipping first, turn the completed work into a later debrief: what was generated, what is now understood, and what remains opaque.

## Design lessons around a real win

Each lesson should explain one concrete local behavior and deliver one tangible repository-level outcome. Include only the supporting concepts needed to understand that behavior.

Prefer lessons that answer questions such as:

- Why does this subsystem exist?
- How does data or control move through it?
- Which invariant is the implementation protecting?
- What design alternatives were available, and why was this one chosen?
- How would a failure appear in logs, tests, state, or user behavior?
- What can the learner now predict or change that they could not before?

Begin with the local behavior and its purpose, then explain the relevant implementation. Introduce background at the point where it clarifies the code. Include a concrete mistake or failure mode. End with a small authentic exercise and a feedback path. Avoid answer choices whose wording or formatting reveals the answer; exact word-count matching is unnecessary.

Lessons and general explanations must be plain, readable, printable HTML with restrained visual design. Reuse `.teach/assets/` before creating new components. A shared stylesheet is the first reusable asset worth creating. Link lessons to related lessons and canonical reference pages. Open the saved HTML directly in the browser when possible and give the learner its direct file link/path. Do not wrap, host or present tutorials through Lavish; reserve Lavish for production pages.

An opening page is optional. When useful, make it a learner-facing introduction to this teaching section: what the local system does, what the section will explain, a proposed teaching sequence, and a contents list with descriptive links to available lessons and references. Planned lessons may appear as clearly labeled, unlinked future topics; do not imply they already exist. Begin actual teaching promptly. If an opening page adds no useful orientation, open the first lesson directly. Never substitute a directory of durable learning context, agent bookkeeping, delivery status or tool lifecycle details for an introduction. Keep necessary source provenance concise and secondary to the explanation.

## Build durable references

Lessons are snapshots of a learning moment; reference pages are the maintained model of the codebase. Update reference pages in place when the implementation changes. Useful references include:

- Architecture and component maps
- Request, event, and data-flow traces
- Domain and API glossaries
- Data models and persistence boundaries
- Agent loops, tool dispatch, state, retries, and evaluation paths
- Testing, debugging, deployment, and observability guides

Promote a term into the canonical glossary only after the learner can use it correctly. Prefer repository terminology over generic synonyms, and document ambiguities explicitly.

## Capture demonstrated learning

Create a learning record when the learner demonstrates non-trivial understanding, discloses relevant prior knowledge, corrects a misconception, or changes the mission. Do not create session logs or records that merely say material was presented.

A useful record changes future teaching. Capture the working mental model, the evidence of understanding, and what it unlocks. When later evidence supersedes a record, mark it superseded rather than erasing the learning history.

Use a brief in-chat teaching debrief only when the current work contains a decision worth harvesting before the next HTML lesson. Tie it to a file or decision, explain the trade-off, name the likely mistake, and suggest one small follow-up. Do not append a boilerplate tutorial to every response. Skip it for acknowledgements, status checks, one-line lookups, or when the user says `no tutorial` or `skip mentor`.

## Aim for knowledge, skill, and judgment

- **Knowledge:** source-grounded explanations of the system and its dependencies.
- **Skill:** durable ability developed through retrieval and real feedback loops.
- **Judgment:** experience comparing designs, debugging failures, and operating the system under realistic constraints.

When judgment would benefit from practitioners or real production exposure, recommend an appropriate community, project, review, or experiment as an option. Do not make outside participation a prerequisite for answering.
