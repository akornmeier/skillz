# Audit Skills

Health check across a skills directory, ending in a report the user can act on.

1. Lint everything in one call — `python3 <base>/scripts/lint_skill.py` with no argument scans `~/.agents/skills` and `./.claude/skills`; pass directories only if the user names specific ones. One skill with a FAIL is BROKEN if it does not load at all (no `SKILL.md`, no frontmatter, dangling symlink), FLAGGED if it loads but has a FAIL or WARN, CLEAN otherwise. Findings are evidence, not verdicts.
2. BROKEN first — no grade applies to a skill that cannot load. Report what each one is and confirm repair or removal with the user before touching any of them.
3. Grade the FLAGGED — one grader per flagged skill, run in parallel. Each reads its skill and `references/review-rubric.md` and returns the rubric's output shape: a verdict per dimension plus the edit for each failure, copying the linter's verdicts for the dimensions it proves.
4. Do not grade CLEAN — the linter proves only the absence of mechanical defects; the judgment dimensions are unproven for them. Say so in the report rather than implying a pass.
5. Write the report — `specs/skill-health-<YYYY-MM-DD>.md`, worst first. One `- [ ]` checkbox per skill needing work with a one-line headline, its failing dimensions, forced tokens per trigger, and the edits named. State the coverage: how many skills were graded, how many only scanned.
6. Offer the worst four as candidates for the Improve route; the report's checkboxes carry the rest.
