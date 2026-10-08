---
name: explaination
description: Explain using ASD-STE100 writing guidance and Eddy's selected explanation samples. Use when explicitly invoked as $explaination or when the user asks for this explanation style.
---

# Explaination

Answer the user's question using these references:

- [ASD-STE100 official introduction](https://www.asd-ste100.org/about_STE.html) and [Issue 9 specification](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf): consult the writing rules and apply those relevant to the explanation. Applying selected rules does not establish full STE compliance.
- [Existing explanation-style skill](../explanation-style/SKILL.md): follow its loader to read the eight selected source samples. Preserve its provenance and experiment limitations. This loads approximately 40,000 source-text tokens; the samples remain in their existing location.

Keep this skill reference-based. If a reference cannot be loaded, state the limitation. Do not invent replacement rules or samples.

Writing preference: "Just tell me what it is, don't add a tail." Avoid the rhetorical "It's X, not Y" pattern.

This skill produces the requested explanation. Create tutorial files only when the user requests them.
