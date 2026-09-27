# Teach

`teach` turns a codebase into a persistent, source-grounded apprenticeship. It follows real control flow, data flow, tests, failures, and engineering decisions; then turns that evidence into short HTML lessons, canonical reference pages, authentic exercises, and learning records.

Invoke it explicitly with `$teach`. Example:

> Use $teach to help me understand how requests move through this service. Start from the entry point and give me something real to trace.

The generated learning workspace lives under `.teach/` in the repository being studied. It preserves the mission, learner profile, curriculum, sources, lessons, references, exercises, and demonstrated learning across sessions.

The teaching is calibrated for a learner with strong ECE, mathematics, signal processing, computer vision, and machine-learning foundations who is building toward software engineering, networks, backend systems, databases, and full-stack AI-agent engineering.

The skill was originally based on Matt Pocock's `teach` workflow and now incorporates selected teaching principles from GitHub's `mentoring-juniors` skill plus a personalized mentor profile.

Upstream inspiration:

- https://github.com/mattpocock/skills/blob/main/docs/productivity/teach.md
- https://github.com/github/awesome-copilot/tree/main/skills/mentoring-juniors
