---
name: score-dsl
description: Edit MusicXML scores through the `score_dsl` Python DSL by translating natural-language editing instructions into `find` queries and `EditSession`/`EditOp` sequences. Use when the user asks to load, query, or modify a MusicXML file via this codebase or requests musical changes such as transposition, dynamics, slurs, pedaling, rhythm, or score-format edits.
---

# score-dsl: MusicXML editing

`score_dsl` imports MusicXML into a queryable score model and applies lossless
XML-text edits. Use one supported workflow:

```python
from score_dsl import find, load_musicxml, score_facts
from score_dsl.editing import EditSession, ChangePitch

score = load_musicxml("piece.xml")
print(score_facts(score))
session = EditSession(score)

match = find(session.score, {
    "type": "note",
    "in_range": "P1:m1",
    "limit": 1,
}).matches[0]
diff = session.apply(ChangePitch(target=match.address, new_pitch="Eb4"))
```

The flow is always:

1. Classify the request: melody, rhythm, annotation, or format.
2. Locate targets with `find(session.score, query)`.
3. Reuse the canonical addresses returned by `find`; do not invent addresses.
4. Build an `EditOp` from `score_dsl.editing`.
5. Apply it with `session.apply(op)`.
6. Inspect the `SemanticDiff`, then re-query `session.score`.
7. Save `session.score.xml_document.source_text`, or call `session.undo()`.

## Imports and discovery

The root package is read-only. Editing symbols come only from the editing
facade:

```python
from score_dsl import find, load_musicxml, score_facts
from score_dsl.editing import (
    EditSession, EditError,
    ChangePitch, SetNoteValue, AddSlur,
    Batch, Expectation, verify_diff,
    describe,
)
```

Use `describe()` or `describe("AddOctaveShift")` from `score_dsl.editing` to
inspect available operations and signatures. The CLI equivalent is
`python -m score_dsl ops [name]`.

## Addresses

Treat addresses as opaque canonical identifiers returned by `find`. The normal
shape looks like:

```text
P1:m3:v1:b5/4:s1#note
```

Use only addresses actually returned by the current `session.score`. Do not
construct alternate positional or time-based forms. After every successful
edit, the session reloads a fresh score model, so cached targets may be stale.
Re-query after insertions, removals, duration changes, measure changes, or
rebarring.

For value-only changes where positions cannot move, applying captured addresses
in reverse document order is safe. Otherwise, re-run `find` before each edit.

## Querying with `find`

```python
# Printed right-hand notes in mm. 4–8
notes = find(session.score, {
    "type": "note",
    "in_range": "P1:m4..m8",
    "filters": {"staff": 1, "visible": True},
    "limit": 1000,
})

# Dynamics
dynamics = find(session.score, {
    "type": "direction",
    "filters": {"direction_kind": "dynamics"},
})
```

Check `result.total`, `result.matches`, and `result.truncated`. Each match has a
canonical `.address` and an `.entity.details` dictionary. Filter rather than
guessing staff, voice, pitch, visibility, or notation.

## Edit categories

### Melody

- `ChangePitch`, `SetNoteField`, `ReplacePitch`, `RemoveAccidentals`
- `AddNote`, `RemoveNote`, `AddChord`, `EditChord`, `DeleteChord`
- `AddInterval`, `Harmonize`, `AddTriad`, `AddSeventhChord`
- `Arpeggiate`, `FillScale`, `Transpose`

### Rhythm

- `SetNoteValue`, `SetNoteBeams`
- `AddRest`, `RemoveRest`
- `AddBackup`, `AddForward`, `RemoveBackup`, `SetBackupDuration`

### Annotation

- `AddDynamic`, `ChangeDynamic`, `RemoveDirection`, `AddTempo`
- `AddWedge`, `RemoveWedges`
- `AddSlur`, `RemoveSlur`, `RemoveSlurMarker`, `AddTie`
- `AddArticulation`, `RemoveArticulation`, `RemoveNotation`
- `AddArpeggiate`, `AddPedal`, `AddPedalDirection`, `RemovePedal`
- `AddOctaveShift`

### Format

- `SetKeySignature`, `SetTimeSignature`, `SetClef`, `RemoveClef`
- `SetDivisions`, `SetTitle`
- `AddMeasure`, `RemoveMeasure`, `AddEmptyStaff`

## Applying operations

Single edit:

```python
from score_dsl.editing import ChangePitch

target = find(session.score, {
    "type": "note", "in_range": "P1:m1", "limit": 1
}).matches[0].address
diff = session.apply(ChangePitch(target=target, new_pitch="Eb4"))
```

Multiple independent edits:

```python
from score_dsl.editing import AddArticulation

addresses = [
    match.address
    for match in find(session.score, {
        "type": "note",
        "in_range": "P1:m1..m4",
        "filters": {"note_type": "eighth", "staff": 1},
        "limit": 1000,
    }).matches
]
for address in reversed(addresses):
    session.apply(AddArticulation(
        target=address,
        articulation="staccato",
    ))
```

Use `Batch` or `session.run_batch(ops)` only when all operations must succeed or
roll back atomically:

```python
from score_dsl.editing import Batch

result = Batch(ops=ops).apply(session)
```

## Important operation rules

- `ChangePitch.new_pitch` must include step, accidental if needed, and octave.
- `AddSlur` and `AddTie` require compatible part, voice, and staff; ties also
  require matching pitch.
- `find` reports durations in quarter-note units. Raw `duration=` fields on
  write operations use MusicXML divisions. Prefer `note_type` plus `dot_count`
  and omit raw duration when the operation can derive it.
- Hidden notes and rests (`printed=False`) are playback content. Use
  `visible=True` for edits referring to what the performer sees.
- Measure insertion/removal and timing edits invalidate later addresses.
- `undo()` is single-level. Use an atomic batch for multi-operation rollback.

## Reading and verifying the diff

Every successful operation returns a `SemanticDiff`:

```python
diff.operation
diff.target
diff.modified
diff.added
diff.removed
diff.annotations
diff.new_diagnostics
```

Report new diagnostics. Verify the requested musical result by querying the
fresh `session.score`, not by assuming that a successful call produced the
intended effect.

## Saving

```python
from pathlib import Path

Path("edited.xml").write_text(
    session.score.xml_document.source_text,
    encoding="utf-8",
)
```

Use `session.undo()` before saving if the semantic diff or verification is
wrong.
