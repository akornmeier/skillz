# Create Plan

1. **Analyze the request.** Identify the desired outcome, scope, constraints, and whether `--questionable` was supplied.
2. **Inspect the repository.** Follow existing architecture and conventions. Read `AI_DOCS/` or `APP_DOCS/` only when present and relevant.
3. **Design the approach.** Define phases, concrete tasks, affected files, dependencies, and executable validation commands.
4. **Author from the template.** Read `templates/plan.html` in full, fill every placeholder, duplicate required repeat blocks, and remove all template markers.
5. **Create useful figures.** Follow `workflows/image-generation.md`. Use its inline-SVG default unless the user explicitly approves potentially paid image generation.
6. **Handle questionables.** Include the section only when `QUESTIONABLE` is true; otherwise remove it completely.
7. **Save the plan.** Use one descriptive kebab-case HTML filename under `specs/` and keep any local image sidecars beneath `specs/<plan-name>/`.
8. **Validate and repair.** Run:

   ```bash
   python3 <skill-directory>/scripts/validate_plan.py <plan.html>
   ```

   Fix every diagnostic and rerun until it passes. Do not open or deliver a structurally invalid plan.
9. **Inspect visually when supported.** Open the validated absolute file URL in the available default browser, for example:

   ```bash
   python3 -m webbrowser -t "file:///absolute/path/to/specs/plan.html"
   ```

   Browser launch is optional and does not replace structural validation. Check figure legibility, clipping, hierarchy, and narrow layouts when visual inspection is available.
10. **Report.** Provide the plan path, validation command run, visual checks actually completed, and unresolved content risks.
