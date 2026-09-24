# Create Skill

1. Scope — one capability, stated as what the skill produces. If the ask covers two unrelated jobs, say so and scope to one.
2. Locate — `~/.agents/skills/<name>/` for a global skill, `.claude/skills/<name>/` for a project one. Ask only if the prompt leaves it genuinely ambiguous. Confirm no directory of that name exists.
3. Evals first — copy `templates/evals.json` to `evals/evals.json` and fill its three cases: the prompts a user will type, the setup each needs, and the observable behaviours that mean it worked and that mean it failed. Note the baseline: what the model does on those prompts with no skill.
4. Description — third person, what it does, then "Use when …" with the phrases a user types. Read *Descriptions* in `references/authoring-guidelines.md` for the pair of good and bad shapes. Check it is more specific than any installed skill sharing a phrase.
5. Author `SKILL.md` — from `templates/SKILL.md`. For each decision (name, degree of freedom, what stays in the router, what goes behind a condition) read only the matching section named in the guidelines' Contents list.
6. Supporting files — only where a route needs one: a template for an output shape, a reference for depth, a script for what is better executed than described. Each gets a Files-table row with its read-it-when condition.
7. Lint — run `python3 <base>/scripts/lint_skill.py <new-skill-dir>`. Apply each Fix and rerun until it exits 0.
8. Grade — read `references/review-rubric.md` and record a verdict per dimension, copying the linter's verdicts for the dimensions it proves. Apply the edit each failure names and regrade until every dimension passes.
9. Run the evals — each case once per profile in `requiredProfiles`, each run in a fresh isolated session, grading every expected and forbidden behaviour from the transcript. When the skill's repo has a `<repo>/evals/README.md`, follow its contract: validate the definitions with `node evals/scripts/validate-cases.mjs` from the repo root, then save one run record per case and profile at `<repo>/evals/runs/<case-id>/<profile>.json`, conforming to `<repo>/evals/run-record.schema.json`.
10. Report — the skill's path, forced tokens per trigger and per route from the linter, the rubric verdicts, and the eval results against the baseline.
