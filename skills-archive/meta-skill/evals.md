# meta-skill evaluations

Two scenarios, one per load path, plus the measurement that both feed. Run each in a
**fresh session** from `~/.claude` — description-driven discovery only shows up
when the skill has to fire on its own.

Deliberately not linked from `SKILL.md`: an unreferenced file costs nothing at runtime.

**Baseline, recorded 2026-07-25 immediately before the Claude 5 context-engineering
rewrite**: `SKILL.md` 437 lines / 12 KB forced on every trigger, plus a Required Reading
block making all three `docs/` files (43 KB) mandatory before step 1 — roughly 56 KB, about
14k tokens, paid before the first design decision. After the rewrite: `SKILL.md` 47 lines
/ 4 KB forced, everything else conditional.

## Scenario A — create

**Query**, typed without a slash command: *"make me a skill that runs our smoke tests"*

**Load path**: `SKILL.md` → `workflows/create-skill.md` → `templates/SKILL.md`, then
`references/skill-review-rubric.md` for the final grade.

**Expected**
- Fires from the description alone, with no slash command.
- Reads `workflows/create-skill.md` and `templates/SKILL.md`.
- Writes the description before the body, and it carries both what and when.
- Produces a skill directory whose `name` is lowercase-hyphen and matches the directory.
- Grades the result against the rubric and reports per-dimension verdicts.
- Opens no file in `docs/`.

## Scenario B — improve

**Query**: *"this skill never triggers, fix it"* (with a skill named or on screen)

**Load path**: `SKILL.md` → `workflows/improve-skill.md` → `references/skill-review-rubric.md`,
then `references/context-engineering-claude5.md` for the subtraction test. Should **not**
read `templates/SKILL.md` — nothing is being authored from scratch.

**Expected**
- Reports a verdict per rubric dimension, before and after.
- Every failing dimension comes with the specific edit that fixes it, not a complaint.
- Reports forced line count before and after.
- Opens no file in `docs/` unless a format detail is genuinely in question.

**Result, 2026-07-25** (4 runs against a deliberately broken throwaway skill): PARTIAL, and
the one known weakness in this skill.

- *Firing*: 2 of 4 runs. On the other two the model diagnosed and patched the frontmatter
  directly without loading the skill. Adding "this skill never triggers" to the description's
  trigger list did not make it deterministic. A narrow, easy repair sits inside the model's
  unaided competence, so it does not always reach for a skill — the failure mode is a tie,
  not a miss, and little is lost when the skill loses it.
- *Rubric*: 0 of 3 firing runs opened `references/skill-review-rubric.md`. Moving the grade to
  step 2 and saying "read it, don't grade from memory" did not change this. On a 45-line
  target with a one-line ask, a seven-dimension grade reads as disproportionate.
- *Output quality*: every run named the exact edit — both frontmatter defects, the correct
  patch, and why triggering depends on frontmatter alone.

Re-measure on a realistic target (a 200+ line skill, an open-ended "improve this") before
concluding the rubric is unreachable. If it stays at 0 there, the criteria belong inline in
the workflow and the separate file should go.

**Result, 2026-07-25** (1 run, `claude -p` from `/Users/tk/.claude`): PASS. Fired from the
description with no slash command. Read `workflows/create-skill.md` → `templates/SKILL.md` →
`references/skill-review-rubric.md`, and graded before reporting. Zero `docs/` reads.
Produced a 31-line skill with a lowercase-hyphen `name` matching its directory.

## Scenario C — the measurement

Not a separate query. On each run above, record from the transcript which files were
actually read. The absence of the `docs/` reads is the result being measured; a `docs/`
read on either route means an instruction somewhere still implies one is required.

Secondary check: forced bytes per route. Scenario A should load `SKILL.md` plus at most
three files; Scenario B, `SKILL.md` plus two. Anything more means the router is routing to
too much.
