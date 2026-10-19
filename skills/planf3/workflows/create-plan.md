# Create Plan

1. **Analyze the request.** Identify the desired outcome, scope, constraints, and whether `--questionable` was supplied.
2. **Inspect the repository.** Follow existing architecture and conventions. Read `AI_DOCS/` or `APP_DOCS/` only when present and relevant.
3. **Design the approach.** Define observable acceptance criteria, non-goals, constraints, phases, concrete tasks, affected files, and dependencies. Map each criterion to implementing tasks and verification; supporting tasks map to the criteria they enable.
4. **Author from the template.** Read `templates/plan.html` in full, fill every placeholder, duplicate required repeat blocks, and remove all template markers. Use stable, globally unique `ac-*`, `task-*`, and `verify-*` IDs with fragment links in the coverage table. Give every task concrete verification cases, a command or explicit manual procedure, expected outcomes, and evidence initially set to `Not run.`. Keep interface blocks only for meaningful cross-task contracts.
5. **Create useful figures.** Follow `workflows/image-generation.md`. Use its inline-SVG default unless the user explicitly approves potentially paid image generation.
6. **Handle questionables.** Include the section only when `QUESTIONABLE` is true; otherwise remove it completely.
7. **Save the plan.** Use one descriptive kebab-case HTML filename under `specs/` and keep any local image sidecars beneath `specs/<plan-name>/`.
8. **Validate and repair.** Run:

   ```bash
   python3 <skill-directory>/scripts/validate_plan.py <plan.html>
   ```

   Fix every diagnostic and rerun until it passes. Do not open or deliver a structurally invalid plan.
9. **Review semantics and repair.** Read `references/engineering-review.md`, run its gates, and record the result in Notes. Repair findings, rerun structural validation, and repeat affected gates until clear. Unresolved blockers require a not-build-ready handoff, not implementation.
10. **Inspect visually when supported.** Open the validated absolute file URL in the available default browser, for example:

   ```bash
   python3 -m webbrowser -t "file:///absolute/path/to/specs/plan.html"
   ```

   Browser launch is optional and does not replace structural validation. Check figure legibility, clipping, hierarchy, and narrow layouts when visual inspection is available.
11. **Report.** Provide the plan path, structural validation command/result, semantic review result, visual checks actually completed, and remaining assumptions or blockers. Do not report planned task checks as executed.
