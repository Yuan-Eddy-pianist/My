# `.teach/reference/glossary.html` format

The glossary is the canonical language of the codebase tutorial. It is a maintained, printable HTML reference page linked by lessons and other reference documents.

Each entry should contain:

- The preferred project term
- A one- or two-sentence definition
- Where the concept appears in the repository
- Avoided aliases when inconsistent language would cause confusion
- A note when the project uses a common term in a narrower or unusual way

Example body fragment:

```html
<section class="glossary-group" id="agent-runtime">
  <h2>Agent runtime</h2>

  <article class="term" id="tool-dispatch">
    <h3>Tool dispatch</h3>
    <p>Selection and execution of a tool call emitted by the model, including argument validation and result routing.</p>
    <p><strong>In this codebase:</strong> <code>src/agent/dispatch.ts</code></p>
    <p><strong>Avoid:</strong> “plugin execution” when referring specifically to runtime tool calls.</p>
  </article>
</section>
```

## Rules

- Add a term only after the learner can use it correctly. The glossary records compressed understanding; it is not where a concept is first taught.
- Prefer vocabulary already used consistently by the codebase. When repository language is inconsistent, choose a canonical term and document the aliases.
- Use existing glossary terms in later definitions so the vocabulary becomes compositional.
- Update definitions as the code or learner's understanding changes; do not preserve stale wording for historical reasons.
- Link each term to relevant lessons and codebase reference pages when useful.
- Use the shared stylesheet in `.teach/assets/` and preserve clean print behavior.
