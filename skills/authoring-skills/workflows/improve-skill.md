# Improve Skill

A static pass, then an observed run. The route ends when the traces show the intended reads and the evals pass, not when the report is written.

1. Locate — look for `.claude/skills/<name>` under the working directory first, then `~/.agents/skills/<name>` and `~/.claude/skills/<name>`; a project copy wins. Never search the whole filesystem. If no skill is named, list those three roots and confirm which one before touching anything.
2. Lint — run `python3 <base>/scripts/lint_skill.py <skill-dir>` before any edit. Record its findings and the forced tokens it prints for `SKILL.md` and for each route. These are the "before" numbers.
3. Grade — read `references/review-rubric.md` and write all fourteen verdict lines in its Output shape before step 4, copying the linter's verdicts for the dimensions it proves. The step is not done until every line exists, even when the linter already names the defect. This is the first move on every improve request, narrow ones included: "it never triggers" is one dimension failing, and the grade says whether it is the only one.
4. Subtract — instruction by instruction, would the model do this unprompted? If yes, cut it. Read *The subtraction test* in `references/authoring-guidelines.md` for the pairs and the list of what survives. Exact paths, output formats, validator loops, and the author's own opinions stay.
5. Redistribute — what survives but is not needed on every route moves behind a read-it-when row: output shapes to `templates/`, depth to `references/`, per-route steps to `workflows/`. Each idea lives in exactly one file.
6. Re-lint and regrade — apply each Fix and rerun the linter until it exits 0, then regrade every dimension. Loop until all pass or a failure is deliberately left with its reason.
7. Observe — read *Capturing a run* in `references/tuning-diagnostics.md`, then run `python3 <base>/scripts/run_fresh_session.py <workdir> "<prompt>" --out <file> --model <model> --trace <skill-dir>` once per profile in the target's `requiredProfiles`, as one plain command; the target's own `evals/evals.json` prompts are the default source. Skip only when the script exits 2: write "observation skipped: <its message>" and grade dimension 14 as failing. Before interpreting the traces, read *Navigation signals* and *Symptom to edit* in the same file.
8. Diagnose — every failed expected behaviour and every navigation signal maps to one row of the Symptom-to-edit table. A symptom with no row is reported, not fixed.
9. Refine and retest — apply the edits, re-lint, rerun the same prompts in new fresh sessions, and compare the traces. Exit when the traces show the intended routes and the evals pass, or when a remaining failure is kept deliberately with its reason.
10. Report — ALWAYS open with this table, one row per observed symptom, or one row reading "none observed" with the trace lines that show the intended route:

    | Symptom | Evidence | Edit applied | Retest |
    | --- | --- | --- | --- |

    Evidence is a trace line or transcript excerpt, never a paraphrase; an empty Retest cell means the edit is unproven, and the report says so. Then the fourteen verdict lines before and after; forced tokens before and after, per trigger and per route; what was cut; what moved and where; any dimension still failing and why.

The narrow-ask rule still holds: "it never triggers" runs the whole route, and the observed run is the proof that the new description fires.
