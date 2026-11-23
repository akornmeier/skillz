# Update Course

Change `specs/COURSE.md` without letting an agent rewrite settled direction. Read the acceptance rules in [../SKILL.md](../SKILL.md) first.

1. **Classify the change.**

   | Change | Approval |
   | --- | --- |
   | Milestone `Spec` or `Status` (`Planned \| Active \| Done \| Dropped`), Area & Verification Map paths, commands, or invariants that are plain facts | None: edit directly |
   | Accepting an inferred entry (removing `Inferred — needs developer review`) | Explicit developer approval |
   | Adding a decision with `Status: Accepted`, or superseding one | Explicit developer approval |
   | Editing the North Star, Non-Goals, Precedence, or Protected Boundaries | Explicit developer approval |
   | Applying or rejecting a `> PROPOSED` block | Explicit developer approval |
   | Acting on a Stale-Doc Triage item from `drift-audit` | Explicit developer approval, per file |

2. **Without approval, propose.** Append a block under Pending Proposals instead of editing accepted text:

   ```text
   > PROPOSED YYYY-MM-DD (agent): <change>. Reason: <why>.
   ```

3. **With approval, apply it narrowly.**
   - Accept an entry by removing its `Inferred` mark only; keep the developer's wording.
   - Add a decision as a new row with the next `D-NNN` ID and `Status: Accepted`. To supersede one, add the new row and change only the old row's status to `Superseded by D-NNN`; never rewrite or delete the old text. Link an existing `docs/decisions/` ADR from the row instead of copying it.
   - Apply an accepted proposal to its section and delete the `> PROPOSED` block; delete a rejected block and record the reason in the report.
   - For a Stale-Doc Triage item, do exactly the approved action: `update` the doc, stamp a one-line `> Superseded by <ref>` banner at line 1, or `delete` it and rely on git history. Never move files into a `docs/archive/` folder.
4. **Retiring a plan** is a `planf3` metadata change, not a course edit: append `; Retired: <reason>` or `; Superseded by <ref>` to the plan's `forward refs`, separating entries with `; `. Then set the milestone `Status` to `Dropped` or relink its `Spec`.
5. **Refresh and check.** When the whole course was re-checked against the code, update `Verified:` to today's date and the short `HEAD` commit. Run `python3 <skill-directory>/scripts/check_drift.py --repo-root .` and fix every `Certain` failure your edit caused.
6. **Report.** List each change with its approval (or the proposal written instead), and the drift check result.
