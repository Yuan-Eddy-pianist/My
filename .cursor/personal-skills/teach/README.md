## What it does

`teach` turns the directory you run it in into a standing teaching workspace and teaches you one topic across many sessions, in short self-contained HTML lessons.

It does not teach from what the model already knows. Parametric knowledge is treated as untrusted: before it teaches, it goes and finds high-trust resources, records them in `RESOURCES.md`, and cites them inside every lesson. The other structural fact is that it is stateful — the mission, the resources, the lessons and the record of what you have learned all live in the directory as files, so the next session picks up from those files rather than from whatever is left of the last conversation.

## When to reach for it

You invoke this by typing `/teach` — the agent won't reach for it on its own.

Reach for it when the learning is the project: a language, a framework, a codebase you have just joined, yoga, shaders, a certification. It is not the tool for one explanation in passing.

| What you want | What to reach for |
| --- | --- |
| To learn a topic over weeks, with sessions that accumulate | `teach` |
| One idea explained inside the session you are already in | Just ask, in that session |
| The agent's last message re-pitched because it didn't land | wait-what |
| To sharpen thinking you already have, rather than acquire new material | grill-me |
| A background agent to read primary sources and leave you a cited document | research |
| To learn something that came up mid-grilling, without derailing the grilling | handoff out to a teaching workspace, then `teach` there |

Upstream docs: https://github.com/mattpocock/skills/blob/main/docs/productivity/teach.md
