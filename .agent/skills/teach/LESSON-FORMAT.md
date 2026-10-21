# `.teach/lessons/*.html` format

A lesson is a short, self-contained HTML document built around one concrete local behavior and one tangible codebase capability. Use sequential filenames such as `0001-trace-a-request.html`.

## Lesson grammar

Use the sections that serve the lesson; preserve their learning sequence rather than forcing empty headings.

1. **Local behavior and purpose** — answer the learner's concrete question using the current implementation or observed behavior.
2. **Trace through the code** — follow concrete files, symbols, configuration, data, and control boundaries.
3. **Supporting explanation, when needed** — introduce a general concept or ECE/ML analogy only where it clarifies this trace; connect it directly to the local code and return to the behavior.
4. **Engineering decision** — explain the design choice, constraints, alternatives, and trade-offs.
5. **Where it breaks** — show the tempting misconception or observable failure mode.
6. **Predict before running** — require retrieval or a prediction before revealing behavior.
7. **Try it in the repository** — give one bounded, authentic trace, change, test, explanation, or debugging task.
8. **Feedback path** — explain how correctness can be checked through tests, runtime behavior, state, or review.
9. **Evidence and sources** — cite repository evidence and relevant external primary sources.
10. **What this unlocks next** — link the lesson to the curriculum without expanding into another lesson.

## HTML requirements

- Produce valid standalone plain HTML with a descriptive `<title>`, semantic landmarks, and accessible heading order. Follow SKILL.md's presentation and optional opening-page contract; deliver the saved HTML directly, without a Lavish wrapper.
- Link the shared stylesheet from `../assets/` rather than duplicating styles. Create the stylesheet when the first lesson is written.
- Prefer readable typography, generous whitespace, restrained color, and useful diagrams over decorative UI. Ensure printing remains clean.
- Use repository-relative paths and symbol names. From `.teach/lessons/`, a source link normally begins with `../../`.
- Link related lessons and canonical reference pages with relative HTML anchors.
- Keep quoted source text brief. Explain code behavior in original language and cite the source location.
- Include the repository revision or working-tree state and verification date in a visible provenance block.
- Remind the learner that they can ask follow-up questions or submit the exercise result for feedback.

## Teaching requirements

- Lead with local codebase behavior and its purpose; introduce background where it helps explain the implementation.
- Use the direct writing style defined in SKILL.md: affirmative statements with a complete point, free of decorative trailing contrasts.
- Do not withhold the solution merely to create difficulty. Use prediction before reveal, then make the explanation complete.
- Keep one concrete local behavior as the lesson's focus. Put necessary background in concise, code-linked asides.
- Make the exercise difficult enough to require retrieval but small enough for a tight feedback loop.
- Do not reveal quiz answers through option length, grammar, ordering, or formatting. Exact character counts are unnecessary.
