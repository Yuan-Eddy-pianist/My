# Learning record format

Learning records live in `.teach/learning-records/` and use sequential names such as `0001-request-lifecycle.md`. Create the directory lazily.

They are the teaching equivalent of architectural decision records: compact evidence that changes what future lessons may safely assume.

## Template

```md
# {Capability or mental model established}

{What the learner can now explain, predict, debug, or change, and why it matters for future work.}

## Evidence
{The answer, prediction, implementation, debugging result, or prior experience that supports this conclusion.}

## Implication
{What this unlocks, what no longer needs introductory treatment, or what should be revisited next.}
```

Optional frontmatter:

```yaml
---
status: active
revisit-after: YYYY-MM-DD
---
```

Use `status: superseded-by-0007` when a later record corrects or deepens the earlier model.

## Write a record when

- The learner demonstrates non-trivial understanding through use, prediction, or explanation.
- The learner discloses relevant prior knowledge, including its depth.
- A misconception is corrected and the corrected model is supported by evidence.
- The mission or learning direction changes because of new understanding.

Do not record material merely because it appeared in a lesson. Exposure and fluent recognition are not evidence of durable learning. Do not turn records into session logs.

Scan the directory for the highest existing sequence number and increment it. Keep each record short enough that future agents can use it quickly.
