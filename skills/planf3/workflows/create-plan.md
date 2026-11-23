# Create Plan

1. **Analyze the request.** Identify the desired outcome, scope, constraints, and whether `--questionable` was supplied.
2. **Inspect the repository.** Follow existing architecture and conventions. Read `AI_DOCS/` or `APP_DOCS/` only when present and relevant. If `specs/COURSE.md` exists, read it, then read in full only the sibling `specs/*.html` plans that it or the request names; for any other sibling plan, check its title and `#acceptance` only. Treat accepted course decisions (`Status: Accepted`), non-goals, and protected boundaries as inherited constraints.
3. **Close material gaps.** Ask only when a material ambiguity or a conflict with the accepted course would change the plan: 1–4 targeted questions through the interactive question tool. Skip this when the request is clear. Without a question tool, write the questions under Open decisions and mark the plan **not build-ready**.
4. **Design the approach.** Define observable acceptance criteria, non-goals, constraints, phases, concrete tasks, affected files, and dependencies. Map each criterion to implementing tasks and verification; supporting tasks map to the criteria they enable. Never silently override the accepted course: put a conflict under Open decisions, or append a `> PROPOSED YYYY-MM-DD (agent): <change>. Reason: <why>.` block to `specs/COURSE.md`.
5. **Author from the template.** Read `templates/plan.html` in full, fill every placeholder, duplicate required repeat blocks, and remove all template markers. Use stable, globally unique `ac-*`, `task-*`, and `verify-*` IDs with fragment links in the coverage table. Give every task concrete verification cases, a command or explicit manual procedure, expected outcomes, and evidence initially set to `Not run.`. Keep interface blocks only for meaningful cross-task contracts.
6. **Create useful figures.** Follow `workflows/image-generation.md`. Use its inline-SVG default unless the user explicitly approves potentially paid image generation.
7. **Handle questionables.** Include the section only when `QUESTIONABLE` is true; otherwise remove it completely.
8. **Save the plan and link its milestone.** Use one descriptive kebab-case HTML filename under `specs/` and keep any local image sidecars beneath `specs/<plan-name>/`. When the plan serves a milestone in `specs/COURSE.md`, record `specs/COURSE.md` and the milestone ID in `back refs`, and add the plan path to that milestone's `Spec` cell (comma-separated), setting its `Status` from `Planned` to `Active`. This bookkeeping needs no approval.
9. **Validate and repair.** Run:

   ```bash
   python3 <skill-directory>/scripts/validate_plan.py <plan.html> --repo-root .
   ```

   Fix every diagnostic and rerun until it passes. Do not open or deliver a structurally invalid plan.
10. **Review semantics and repair.** Read `references/engineering-review.md`, run its gates, and record the result in Notes. Repair findings, rerun structural validation, and repeat affected gates until clear. Unresolved blockers require a not-build-ready handoff, not implementation.
11. **Inspect visually when supported.** Open the validated absolute file URL in the available default browser, for example:

   ```bash
   python3 -m webbrowser -t "file:///absolute/path/to/specs/plan.html"
   ```

   Browser launch is optional and does not replace structural validation. Check figure legibility, clipping, hierarchy, and narrow layouts when visual inspection is available.
12. **Report.** Provide the plan path, structural validation command/result, semantic review result, visual checks actually completed, the linked milestone (if any), and remaining assumptions or blockers. Do not report planned task checks as executed.
