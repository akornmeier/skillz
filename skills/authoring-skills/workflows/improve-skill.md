# Improve Skill

A static pass, then an observed run. The route ends when the traces show the intended reads and the evals pass, not when the report is written.

1. Locate — resolve the skill directory from the prompt. If none is named, list the skills on disk and confirm which one before touching anything.
2. Lint — run `python3 <base>/scripts/lint_skill.py <skill-dir>` before any edit. Record its findings and the forced tokens it prints for `SKILL.md` and for each route. These are the "before" numbers.
3. Grade — read `references/review-rubric.md` and record a verdict per dimension, copying the linter's verdicts for the dimensions it proves. This is the first move on every improve request, narrow ones included: "it never triggers" is one dimension failing, and the grade says whether it is the only one.
4. Subtract — instruction by instruction, would the model do this unprompted? If yes, cut it. Read *The subtraction test* in `references/authoring-guidelines.md` for the pairs and the list of what survives. Exact paths, output formats, validator loops, and the author's own opinions stay.
5. Redistribute — what survives but is not needed on every route moves behind a read-it-when row: output shapes to `templates/`, depth to `references/`, per-route steps to `workflows/`. Each idea lives in exactly one file.
6. Re-lint and regrade — apply each Fix and rerun the linter until it exits 0, then regrade every dimension. Loop until all pass or a failure is deliberately left with its reason.
7. Observe — capture one fresh-session run per profile in the target's `requiredProfiles` on a real prompt; the target's own `evals/evals.json` prompts are the default source. Save the transcript and run `python3 <base>/scripts/trace_skill_use.py <skill-dir> <transcript>`. Then read *Navigation signals* and *Symptom to edit* in `references/tuning-diagnostics.md` before interpreting the trace. If no session can be run, write "observation skipped: <reason>" and grade dimension 14 as failing with it.
8. Diagnose — every failed expected behaviour and every navigation signal maps to one row of the Symptom-to-edit table. A symptom with no row is reported, not fixed.
9. Refine and retest — apply the edits, re-lint, rerun the same prompts in new fresh sessions, and compare the traces. Exit when the traces show the intended routes and the evals pass, or when a remaining failure is kept deliberately with its reason.
10. Report — first the observation table from *Report shape* in `references/tuning-diagnostics.md`, one row per observed symptom with its evidence, edit, and retest result; then per-dimension verdicts before and after; forced tokens before and after, per trigger and per route; what was cut; what moved and where; any dimension still failing and why.

The narrow-ask rule still holds: "it never triggers" runs the whole route, and the observed run is the proof that the new description fires.
