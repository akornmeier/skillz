# Audit Skills

Health check across every installed skill, ending in a report the user can act on.

1. Scan - Assign `SKILL_DIR` and run the scanner in the same Bash call, both statements in one block. A prefix assignment (`SKILL_DIR=... python3 "$SKILL_DIR/..."`) expands the variable before it is set, and shell state does not persist between calls.

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>"
python3 "$SKILL_DIR/scripts/scan.py"
```

   Takes directory arguments only if the user names specific ones. Returns three groups — BROKEN, FLAGGED, CLEAN. Its flags are evidence, not verdicts.
2. Handle BROKEN First - These do not load at all, so no grade applies. Report what each one is — dangling symlink, missing `SKILL.md`, unparseable frontmatter — and confirm repair or removal with the user before touching any of them.
3. Grade the FLAGGED - One grader per flagged skill, run in parallel. Each reads its skill and `references/skill-review-rubric.md`, and returns the rubric's own output shape: a verdict per dimension plus the specific edit for each failure. Above roughly ten, use a `Workflow` pipeline so grading and reporting overlap rather than waiting on a barrier.
4. Do Not Grade CLEAN - The mechanical pass only proves the absence of mechanical defects; dimensions 3, 5, and 7 are unproven for them. Say so in the report rather than implying a pass.
5. Write the Report - `specs/skill-health-<YYYY-MM-DD>.md`, worst first. One `- [ ]` checkbox per skill needing work, each with a one-line headline, its failing dimensions, and the edits the grader named. State the coverage the run actually had: how many were graded, how many only scanned.
6. Offer Plans - Present the worst four as a multi-select question, and say the report's checkboxes carry the rest. For each skill the user picks, invoke `planf3` to write one plan per skill, passing that skill's failing dimensions and the graders' proposed edits as the prompt.
