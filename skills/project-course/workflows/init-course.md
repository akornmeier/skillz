# Init Course

Draft `specs/COURSE.md` from what the repository already shows. Change no code, and never overwrite an existing doc.

1. **Check for an existing course.** If `specs/COURSE.md` exists, stop here and follow [update-course.md](update-course.md).
2. **Inspect the repository, read-only.** Read `AGENTS.md`, `CLAUDE.md`, `README.md`, and `docs/` when present. Note ADRs under `docs/decisions/` and any `mental-model` expertise files to link rather than copy. List `specs/*.html` plans by title and `#acceptance` only. Find code entry points and the test, lint, and build commands the repo or its CI already runs.
3. **Ask only the gaps.** Use the interactive question tool for at most 1–3 questions the repository cannot answer: the project's goal, its non-goals, and the paths that must not change without asking. Skip any question the docs already settle. Without a question tool, leave those sections inferred.
4. **Draft the course.** Copy [../templates/COURSE.md](../templates/COURSE.md) to `specs/COURSE.md` and fill it in:
   - Answers the developer gave in step 3 are accepted; write them without the mark.
   - Everything inferred from code or docs keeps `Inferred — needs developer review`, row by row.
   - Map each existing active plan to a milestone in its `Spec` cell, and fill the Area & Verification Map with real paths and the commands found in step 2.
   - Link existing ADRs from Decision Log rows (marked inferred unless the ADR says `Status: Accepted`).
   - Set `Verified:` to today's date and the short `HEAD` commit.
   - Wrap every protected path in backticks and end directories with `/`.
5. **Check it.** Run `python3 <skill-directory>/scripts/check_drift.py --repo-root .` and fix every `Certain` failure in the draft, such as a mistyped path.
6. **Hand it to the developer.** Ask them to accept or edit the inferred sections; acceptance follows [update-course.md](update-course.md). Offer once to add this pointer to `AGENTS.md` or `CLAUDE.md`, and add it only if they agree:

   ```text
   Project course: `specs/COURSE.md` — read before planning, shipping, or touching protected paths.
   ```

7. **Report.** Give the course path, the sections still inferred, the questions asked and answered, the drift check result, and whether the pointer was added.
