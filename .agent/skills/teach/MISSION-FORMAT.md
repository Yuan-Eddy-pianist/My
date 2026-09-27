# `.teach/MISSION.md` format

`MISSION.md` captures why the learner wants to understand this codebase. Every curriculum decision, lesson, reference page, and exercise should trace back to it.

## Template

```md
# Mission: {Codebase or capability}

## Why
{The concrete real-world outcome. What changes in the learner's work when they can understand and operate this system?}

## Success looks like
- {An observable capability, such as tracing a request end to end}
- {An observable capability, such as safely changing and testing a subsystem}
- {An observable capability, such as deploying or debugging the system}

## Current project context
- Repository: {name or path}
- Relevant product or users: {brief context}
- Starting point: {what the learner is currently working on}

## Constraints
- {Time, access, environment, learning preferences, or project boundaries}

## Out of scope
- {Adjacent systems or topics intentionally deferred}
```

## Rules

- Keep one coherent mission per `.teach/` workspace. A mission may contain several related competencies needed to operate the same system.
- Prefer observable capabilities over goals such as “understand the backend.”
- Infer a provisional mission when the user's request is clear; ask only when ambiguity would materially change the teaching direction.
- Confirm before replacing the mission with a materially different one.
- Keep it short enough to remain a compass rather than a project plan.
