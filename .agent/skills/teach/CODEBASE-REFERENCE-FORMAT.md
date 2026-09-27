# `.teach/reference/*.html` format

Reference pages are the maintained source maps of the tutorial: architecture diagrams, request flows, data models, API maps, debugging guides, and other compressed knowledge. Unlike lessons, update them in place as the codebase changes.

## Required provenance

Every page should visibly record:

- Last verified date
- Commit or revision, or `working tree` when uncommitted changes were inspected
- Relevant source and configuration files
- Relevant tests or runtime observations
- External specifications or official documentation, when applicable

Distinguish claims with clear language:

- **Implemented:** established by current code or configuration.
- **Observed:** established by a test, trace, log, or safe experiment.
- **Intended:** stated by repository documentation, ADRs, comments, or product requirements.
- **Inferred:** a reasoned interpretation not directly established by another source.

## Suggested structure

```html
<main>
  <header>
    <p class="eyebrow">Codebase reference</p>
    <h1>{Reference topic}</h1>
    <p>{What this page helps the learner find, predict, or decide quickly.}</p>
  </header>

  <aside class="provenance">
    <h2>Evidence</h2>
    <!-- verification date, revision, source files, tests, observations, external docs -->
  </aside>

  <section>
    <h2>{Map, flow, invariant, or decision}</h2>
    <!-- compressed explanation, diagram, trace, or lookup material -->
  </section>

  <section>
    <h2>Failure signatures</h2>
    <!-- symptoms, likely boundaries, and evidence-gathering steps -->
  </section>

  <nav aria-label="Related learning material">
    <!-- lessons and other reference pages -->
  </nav>
</main>
```

## Rules

- Optimize for quick return visits and print use, not linear instruction.
- Prefer diagrams, maps, compact examples, and decision-oriented lookup structures where they clarify relationships.
- Link to code and tests rather than copying large passages that will drift.
- When implementation and documentation disagree, expose the disagreement and its evidence.
- Update stale claims and their verification metadata together.
- Use the shared `.teach/assets/` components so references and lessons feel like one coherent body of work.
