# My project notes

**Canonical workspace path:** `/Users/eddy/Desktop/My`

## 2026-10-07 — Tutorial explanation samples and deferred experiments

The explanation-style tournament stops after six rounds / 80 comparisons. Eddy is exhausted by reviewing and wants to use the selected samples now. Do not start more rounds or token-budget experiments without a new request.

The tutorial skill is [teach](.agent/skills/teach/SKILL.md). It loads the reusable [explanation-style](.agent/skills/explanation-style/SKILL.md) library at the start of every tutorial session or newly requested tutorial section. The same explanation-style skill can be invoked independently.

Selected sources:

- Software Engineering at Google
- Full Stack Open
- CS50's Introduction to Databases with SQL
- Think Stats, 2nd edition
- CS50's Web Programming with Python and JavaScript
- Automate the Boring Stuff with Python
- Eloquent JavaScript, 4th edition
- The Missing Semester of Your CS Education

Retain each source's exact tested sample of about 5,000 tokens. Loading all eight is about 40,000 source-text tokens, plus surrounding instructions and task context. Counts use the experiment's `o200k_base` proxy, not a verified model-specific tokenizer. Tutorial answers have no experiment-imposed word limit.

**Token-budget experiments are unfinished.** The existing amount is a temporary operating choice, not an optimized budget. If the tutorial skill does not work well, revisit source-token amounts as a possible improvement method.

**The sources were tested independently.** Each tournament answer received one source sample. The eight-source combination has not been tested, and it may perform worse, better, or differently than its individual members. Do not infer that good individual results prove a good blend. Comparing individual sources with combinations is a separate possible improvement experiment; changing both the mix and token budget at once would make the cause of any change hard to interpret.

Use ordinary tutorial feedback first. Neither future experiment is scheduled or required before teaching. Keep original results intact; do not treat this provisional deployment as fresh experimental evidence.

The full source provenance and frozen-sample hashes are in [the library manifest](.agent/skills/explanation-style/references/manifest.json). The local experiment and saved reviews remain at `/Users/eddy/Documents/Codex/2026-10-03/h/outputs/explanation-lab`; the checkpoint analysis is at `/Users/eddy/Documents/Codex/2026-10-03/h/work/round-six-checkpoint.json`.
