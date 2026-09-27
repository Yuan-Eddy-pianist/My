# `.teach/CURRICULUM.md` format

`CURRICULUM.md` is a living map between the codebase and the capabilities required to understand, change, debug, and operate it. It is not a fixed syllabus.

## Template

```md
# {Codebase} curriculum

## System map

- {User-visible or external boundary}
  - {Entry point}
  - {Major control or data path}
  - {Stateful dependency}
  - {Observable outcome}

## Current frontier

- Current concept: {one concept worth learning next}
- Why now: {connection to mission, current work, or prerequisite graph}
- Relevant code: {repository-relative paths and symbols}
- Practice target: {what the learner should be able to predict, trace, change, debug, or explain}

## Concept graph

- {Concept}
  - Status: mapped | introduced | practiced | demonstrated | revisit
  - Why it matters here: {codebase-specific role}
  - Depends on: {prerequisites, if any}
  - Evidence: {lesson or learning-record links}
  - Leads to: {useful next concepts}

## Open questions

- {A codebase question whose answer would change the curriculum}

## Revisit queue

- {Concept}: revisit after {date or milestone} through {retrieval task}
```

## Rules

- Organize around behavior and boundaries rather than directory order.
- Prefer the smallest concept that unlocks authentic work in the repository.
- Let current engineering tasks reveal useful curriculum nodes, but periodically inspect for important gaps that incidental work has missed.
- Promote a status to `demonstrated` only when supported by a learning record.
- Keep one current frontier. The rest of the graph is orientation, not a commitment to teach everything.
