# Drift Audit

Find where the project has drifted from its course. Strictly read-only: edit zero files, change no code, and leave every fix to [update-course.md](update-course.md) or `planf3`.

1. **Certain findings.** Run:

   ```bash
   python3 <skill-directory>/scripts/check_drift.py --repo-root .
   ```

   Its failures and warnings are the `Certain` tier: mechanical facts such as a milestone linking a missing spec, an area path that no longer exists, a duplicate decision ID, a milestone status that disagrees with its tasks, or a plan that fails validation. It runs without `specs/COURSE.md` too, auditing only the plans.
2. **Evidence findings.** Compare the repository with the accepted course (see the acceptance rules in [../SKILL.md](../SKILL.md)). Check current code, overlapping active plans, and docs outside `specs/` (for example `docs/*.md` and design docs) against `Status: Accepted` decisions, the Non-Goals, the Protected Boundaries, and major areas missing from the Area & Verification Map. Each finding cites a `file:line` or a command you ran. On a large repository, split the check by area across subagents when they are available.
   - **Stale-Doc Triage.** List docs outside `specs/` that are clearly stale or contradict accepted text, one line each, with a recommended action: `update` it, stamp a one-line `> Superseded by <ref>` banner at line 1, or `delete` it and rely on git history. Never recommend moving files into a `docs/archive/` folder, where code search still finds them.
3. **Inference findings.** Read the `Verified:` date and commit in the course. For each area, run `git log -n 5 --oneline <commit>..HEAD -- <area paths>` (or `--since=<date>` without a commit) and note areas changed since the course was last verified. Without git history or a `Verified:` stamp, report `Not run: no git history / no Verified stamp`.
4. **Report.** One report with three separate tiers, never averaged or blended into a score:

   | Tier | Meaning | Source |
   | --- | --- | --- |
   | Certain | Mechanically true | `check_drift.py` |
   | Evidence | Shown by code or docs | `file:line` or a command |
   | Inference | Likely, from history | `git log` since `Verified:` |

   Follow it with the Stale-Doc Triage list and the next steps for each finding (which workflow or skill fixes it). Do not apply any of them.
