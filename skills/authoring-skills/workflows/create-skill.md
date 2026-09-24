# Create Skill

1. Scope — one capability, stated as what the skill produces. If the ask covers two unrelated jobs, say so and scope to one.
2. Locate — `~/.agents/skills/<name>/` for a global skill, `.claude/skills/<name>/` for a project one. Ask only if the prompt leaves it genuinely ambiguous. Confirm no directory of that name exists.
3. Evals first — copy `templates/evals.json` to `evals/evals.json` and fill three scenarios: the queries a user will type and the observable behaviours that mean it worked. Note the baseline: what the model does on those queries with no skill.
4. Description — third person, what it does, then "Use when …" with the phrases a user types. Read *Descriptions* in `references/authoring-guidelines.md` for the pair of good and bad shapes. Check it is more specific than any installed skill sharing a phrase.
5. Author `SKILL.md` — from `templates/SKILL.md`. For each decision (name, degree of freedom, what stays in the router, what goes behind a condition) read only the matching section named in the guidelines' Contents list.
6. Supporting files — only where a route needs one: a template for an output shape, a reference for depth, a script for what is better executed than described. Each gets a Files-table row with its read-it-when condition.
7. Lint — run `python3 <base>/scripts/lint_skill.py <new-skill-dir>`. Apply each Fix and rerun until it exits 0.
8. Grade — read `references/review-rubric.md` and record a verdict per dimension, copying the linter's verdicts for the dimensions it proves. Apply the edit each failure names and regrade until every dimension passes.
9. Run the evals — each scenario in a fresh session (`claude -p "<query>"` from a scratch directory). Record in `evals/evals.json`, as a top-level `results` block: date, whether it fired, files read, and a verdict per expected behaviour.
10. Report — the skill's path, forced tokens per trigger and per route from the linter, the rubric verdicts, and the eval results against the baseline.
