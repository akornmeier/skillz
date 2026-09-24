# Improve Skill

1. Locate — resolve the skill directory from the prompt. If none is named, list the skills on disk and confirm which one before touching anything.
2. Lint — run `python3 <base>/scripts/lint_skill.py <skill-dir>` before any edit. Record its findings and the forced tokens it prints for `SKILL.md` and for each route. These are the "before" numbers.
3. Grade — read `references/review-rubric.md` and record a verdict per dimension, copying the linter's verdicts for the dimensions it proves. This is the first move on every improve request, narrow ones included: "it never triggers" is one dimension failing, and the grade says whether it is the only one.
4. Subtract — instruction by instruction, would the model do this unprompted? If yes, cut it. Read *The subtraction test* in `references/authoring-guidelines.md` for the pairs and the list of what survives. Exact paths, output formats, validator loops, and the author's own opinions stay.
5. Redistribute — what survives but is not needed on every route moves behind a read-it-when row: output shapes to `templates/`, depth to `references/`, per-route steps to `workflows/`. Each idea lives in exactly one file.
6. Re-lint and regrade — apply each Fix and rerun the linter until it exits 0, then regrade every dimension. Loop until all pass or a failure is deliberately left with its reason.
7. Report — per-dimension verdicts before and after; forced tokens before and after, per trigger and per route; what was cut; what moved and where; any dimension still failing and why.
