# Experiment status and source provenance

## Operating decision — 2026-10-07

Eddy accepted eight sources after six rounds and 80 blind comparisons between source-conditioned answers, and stopped reviewing due to fatigue. Use the existing approximately 5,000-token sample from each source for now. The combined load is approximately 40,000 original-text tokens plus prompt/context overhead. No further tournament or token-budget experiment is authorized by invoking this skill.

## Evidence and limits

The final pool contained 41 sources with retrievable material. Each answer used exactly one frozen source pack, GPT-6.1 Sol, medium reasoning, and no word limit. The 80 reviews contained 72 preferences, four ties and four cannot-judge responses. The eight selected sources stayed in the estimated top ten in the full-history ranking and two sensitivity checks: omitting the repetitive first round, and conservatively omitting eight comparisons containing the old list-numbering renderer failure pattern. This supports a practical shortlist, not exact ranks or proven superiority.

The numbering display bug was fixed during Round 6. Raw generated answers and votes were preserved. The conservative sensitivity check excluded even matching patterns that may have been viewed after the fix; it is not a reconstruction of actual bias.

The samples were mechanically extracted at fixed positions. They can contain code, partial passages, or topic-specific terminology. Preserve these samples rather than rewriting them into an idealized style guide: the reviewed behavior was conditioned on this exact material.

**Combined use is untested.** Independently helpful samples may interfere with one another or behave differently when combined. A tutorial's different learner profile, task, model or surrounding instructions can also change its behavior. No evidence establishes that loading all eight is better than, or as good as, one source.

**Token-budget experiments are unfinished and deferred.** If tutorials do not work well, propose source-token-budget testing as an improvement option; separately consider individual sources versus combinations. Avoid changing both variables in the same comparison. Do not restart review work without a new user request. The current samples and amounts are a provisional deployment choice.

## Frozen sample inventory

Each JSON file contains the original experiment pack: excerpt question/answer text, attribution, source URLs, license records, retrieval records and excerpt locations. The loader verifies file hashes against [manifest.json](manifest.json). Read the samples using the loader described in the skill entrypoint. No live downloads are needed.

- **Software Engineering at Google**: [google-swe.json](sources/google-swe.json), 5,000 source tokens, 4 excerpts. [Original source](https://abseil.io/resources/swe-book/html/ch03.html); [recorded terms](https://abseil.io/resources/swe-book) (CC BY-NC-ND 4.0).
- **Full Stack Open**: [fullstack-open.json](sources/fullstack-open.json), 5,000 source tokens, 4 excerpts. [Original source](https://fullstackopen.com/en/part1/component_state_event_handlers); [recorded terms](https://fullstackopen.com/en/about/) (CC BY-NC-SA 3.0).
- **CS50’s Introduction to Databases with SQL**: [cs50-sql.json](sources/cs50-sql.json), 5,000 source tokens, 4 excerpts. [Original source](https://cs50.harvard.edu/sql/2024/weeks/3/); [recorded terms](https://cs50.harvard.edu/sql/2024/license/) (CC BY-NC-SA 4.0).
- **Think Stats, 2nd edition**: [think-stats.json](sources/think-stats.json), 5,000 source tokens, 4 excerpts. [Original source](https://greenteapress.com/thinkstats2/html/index.html); [recorded terms](https://greenteapress.com/thinkstats2/html/index.html) (CC BY-NC-SA 3.0).
- **CS50’s Web Programming with Python and JavaScript**: [cs50-web.json](sources/cs50-web.json), 5,000 source tokens, 4 excerpts. [Original source](https://cs50.harvard.edu/web/2020/weeks/3/); [recorded terms](https://cs50.harvard.edu/web/2020/license/) (CC BY-NC-SA 4.0).
- **Automate the Boring Stuff with Python**: [automate-python.json](sources/automate-python.json), 5,000 source tokens, 4 excerpts. [Original source](https://automatetheboringstuff.com/2e/); [recorded terms](https://automatetheboringstuff.com/2e/) (CC BY-NC-SA 3.0).
- **Eloquent JavaScript, 4th edition**: [eloquent-js.json](sources/eloquent-js.json), 5,000 source tokens, 4 excerpts. [Original source](https://eloquentjavascript.net/05_higher_order.html); [recorded terms](https://eloquentjavascript.net/) (CC BY-NC 3.0).
- **The Missing Semester of Your CS Education**: [missing-semester.json](sources/missing-semester.json), 5,000 source tokens, 4 excerpts. [Original source](https://missing.csail.mit.edu/2020/shell-tools/); [recorded terms](https://missing.csail.mit.edu/) (CC BY-NC-SA 4.0).

## Local experiment record

- Experiment: `/Users/eddy/Documents/Codex/2026-10-03/h/outputs/explanation-lab`
- Reviewed rounds: `data/tournament/round-01.json` through `round-06.json` inside that experiment.
- Checkpoint analysis: `/Users/eddy/Documents/Codex/2026-10-03/h/work/round-six-checkpoint.json`
- Personal follow-ups: `Desktop/My/Mynote.md`.

These paths are provenance only. The deployed skill loads its own bundled copies and does not depend on the review server or the experiment's virtual environment. Do not publish or upload the bundled source excerpts as part of normal tutorial delivery; preserve their original attribution and terms when handling them.
