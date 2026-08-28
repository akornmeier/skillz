# Update Plan

1. **Identify the plan and scope.** Locate the target HTML and determine the smallest requested content change.
2. **Validate the starting artifact.** Run the bundled validator. Stop and report unrelated structural failures before editing.
3. **Snapshot the previous artifact.** Copy it to a temporary file so append-only metadata can be checked after the edit.
4. **Apply the change surgically.** Preserve unaffected sections and the existing visual identity.
5. **Update history.** Append the current ISO timestamp, agent name, and session ID; add one Amendments entry describing what changed and why. Never replace prior metadata.
6. **Validate and repair.** Run:

   ```bash
   python3 <skill-directory>/scripts/validate_plan.py <plan.html> --previous <temporary-before.html>
   ```

   Fix every diagnostic and rerun until it passes. Remove the temporary copy afterward.
7. **Inspect affected visuals when supported.** Confirm changed content and figures render correctly; browser launch is optional.
8. **Report.** Summarize the scoped change, amendment, validation result, and visual checks actually completed.
