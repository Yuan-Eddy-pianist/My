---
name: mentoring-juniors
description: >-
  User-enabled tutorial closer. When attached, do the requested work, then
  append one tutorial section about a decision from this turn. Do not apply
  unless the user has attached this skill.
disable-model-invocation: true
license: MIT
---

# Mentoring juniors (trial)


Do the work as usual. After any turn that made a real decision or change, append one **Tutorial** section. Skip acknowledgements, status checks, and one-line lookups. Skip if the user says `no tutorial` or `skip mentor`.

Do not withhold solutions. Do not use a persona, signature phrases, or pep talk.

## Tutorial (required closer)

One concept from **this** turn. Cite a file or decision. If nothing new was decided, omit the section.

```markdown
## Tutorial

**Concept:** {name the idea}

{Why this approach, the trade-off, a mental model. Tie it to something already known if that helps. 1–2 short paragraphs.}

**Watch for:** {the mistake this turn would have caused if done the lazy way}

**Try:** {one small follow-up in this repo or a scratch file}

**Read:** {one primary source, or omit}
```

## How to write that section

- Teach the **why** before restating the how.
- One concept. Prefer something this turn actually touched (architecture, async, debug, tests, security, performance, git).
- If the turn was high-urgency shipping, use the same closer as a debrief: what was generated, what is now clear, what is still opaque.
- PEAR is for the reader, not a speech: plan before generate, read every line, rewrite in their own terms if they want it to stick.

Adapted from [github/awesome-copilot mentoring-juniors](https://github.com/github/awesome-copilot/tree/main/skills/mentoring-juniors).
