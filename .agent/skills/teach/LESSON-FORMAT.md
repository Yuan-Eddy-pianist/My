# `.teach/lessons/*.html` format

A lesson is a short, self-contained HTML document built around one conceptual spine and one tangible codebase capability. Use sequential filenames such as `0001-trace-a-request.html`.

## Lesson grammar

Use the sections that serve the lesson; preserve their learning sequence rather than forcing empty headings.

1. **Why this matters here** — connect the concept to the mission and current system.
2. **Mental model** — explain the concept at the learner's level; use an ECE/ML analogy only when it clarifies rather than decorates.
3. **Trace through the code** — follow concrete files, symbols, data, and control boundaries.
4. **Engineering decision** — explain the design choice, constraints, alternatives, and trade-offs.
5. **Where it breaks** — show the tempting misconception or observable failure mode.
6. **Predict before running** — require retrieval or a prediction before revealing behavior.
7. **Try it in the repository** — give one bounded, authentic trace, change, test, explanation, or debugging task.
8. **Feedback path** — explain how correctness can be checked through tests, runtime behavior, state, or review.
9. **Evidence and sources** — cite repository evidence and relevant external primary sources.
10. **What this unlocks next** — link the lesson to the curriculum without expanding into another lesson.

## HTML requirements

- Produce valid standalone HTML with a descriptive `<title>`, semantic landmarks, and accessible heading order.
- Link the shared stylesheet from `../assets/` rather than duplicating styles. Create the stylesheet when the first lesson is written.
- Prefer readable typography, generous whitespace, restrained color, and useful diagrams over decorative UI. Ensure printing remains clean.
- Use repository-relative paths and symbol names. From `.teach/lessons/`, a source link normally begins with `../../`.
- Link related lessons and canonical reference pages with relative HTML anchors.
- Keep quoted source text brief. Explain code behavior in original language and cite the source location.
- Include the repository revision or working-tree state and verification date in a visible provenance block.
- Remind the learner that they can ask follow-up questions or submit the exercise result for feedback.

## Teaching requirements

- Teach why before how.
- Do not withhold the solution merely to create difficulty. Use prediction before reveal, then make the explanation complete.
- Keep one conceptual spine. Put required background in concise asides.
- Make the exercise difficult enough to require retrieval but small enough for a tight feedback loop.
- Do not reveal quiz answers through option length, grammar, ordering, or formatting. Exact character counts are unnecessary.
