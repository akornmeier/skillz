# Update Plan

1. **Identify the plan and scope.** Locate the target HTML and determine the smallest requested content change.
2. **Validate the starting artifact.** Run the bundled validator. Stop and report unrelated structural failures before editing. Older plans missing the engineering fields need an explicitly scoped format upgrade; do not silently rewrite them.
3. **Snapshot the previous artifact.** Copy it to a temporary file so append-only metadata can be checked after the edit.
4. **Apply the change surgically.** Preserve unaffected sections, the existing visual identity, and stable criterion/task/verification IDs. Update affected coverage links, interface consumers, verification cases, and expected outcomes together. Mark prior evidence stale and reset affected completion markers when their code, contract, or check changes. For an explicitly requested format upgrade only, read `templates/plan.html` to add the missing engineering structure without replacing unrelated content.
5. **Update history.** Append the current ISO timestamp, agent name, and session ID; add one Amendments entry describing what changed and why. Never replace prior metadata.
6. **Validate and repair.** Run:

   ```bash
   python3 <skill-directory>/scripts/validate_plan.py <plan.html> --previous <temporary-before.html>
   ```

   Fix every diagnostic and rerun until it passes.
7. **Review semantics and repair.** Read `references/engineering-review.md`. Check full criterion coverage and follow changed contracts through affected consumers and checks. Record the result in Notes, repair findings, rerun validation with `--previous`, and repeat affected review gates until clear. Remove the snapshot only after the loop passes. Label unresolved blockers not build-ready.
8. **Inspect affected visuals when supported.** Confirm changed content and figures render correctly; browser launch is optional.
9. **Report.** Summarize the scoped change, amendment, structural validation result, semantic review result, remaining blockers, and visual checks actually completed.
