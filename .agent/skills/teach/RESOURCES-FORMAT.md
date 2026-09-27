# `.teach/RESOURCES.md` format

`RESOURCES.md` is the curated evidence index for the codebase tutorial. It should make it easy to return to the sources that support lessons and canonical reference pages.

## Template

```md
# {Codebase} resources

## Repository evidence

- [`src/server/router.ts`](../src/server/router.ts)
  Implements request dispatch. Use for: tracing how routes reach handlers. Verified: {date}, {revision or working tree}.
- [`tests/router.test.ts`](../tests/router.test.ts)
  Demonstrates routing behavior and failure cases. Use for: distinguishing intended behavior from assumptions.

## Runtime evidence

- `{command, trace, log, or experiment}`
  Observed: {brief result}. Environment: {relevant conditions}. Verified: {date}.

## Primary external sources

- [Official framework documentation](https://example.com)
  Defines {external contract}. Use for: {specific questions}.

## Broader context

- [High-quality secondary source](https://example.com)
  Explains {trade-off or history}. Use for: {specific context not established by primary sources}.

## Practice and community

- {Optional repository, project, forum, review practice, or community}
  Use for: {kind of experience or feedback it can provide}.

## Gaps

- {An unresolved question or area without adequate evidence}
```

## Rules

- Treat code and configuration as implementation evidence; tests and runtime observations as behavioral evidence; repository docs as intent; external primary sources as dependency contracts.
- Annotate every entry with what it establishes and when to use it.
- Prefer repository-relative links so the learning workspace remains portable.
- Record the revision or working-tree state for evidence likely to change.
- Label unresolved contradictions instead of silently choosing the most convenient source.
- Keep the list curated. Remove or replace sources that proved stale, shallow, or off-mission.
- Practice and community resources are optional, not prerequisites.
