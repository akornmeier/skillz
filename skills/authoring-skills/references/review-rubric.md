# Skill review rubric

Grade a skill against every dimension. Each is pass/fail against a stated condition, not a score. A failure is reported only with the edit that fixes it.

The **Proved by** column says who does the work. *Linter* dimensions are settled by running `scripts/lint_skill.py`: copy its verdict, do not re-check by hand. *Judgment* dimensions need a reader.

| # | Dimension | Passes when | Proved by |
| --- | --- | --- | --- |
| 1 | Description triggers | Third person; states what the skill does and when to fire; names the phrases a user actually types. A stranger reading only the frontmatter can answer "should this fire?" for a given prompt. | Linter (person, trigger clause, length) + judgment (specific enough to win against overlapping skills) |
| 2 | Forced context | `SKILL.md` is under 500 lines and no instruction in it requires reading another file unconditionally. | Linter (line count, unprompted phrases) + judgment (unconditional reads) |
| 3 | Progressive disclosure | Every bundled path has a stated condition for opening it, and depth lives behind that condition rather than in the router. Workflows are numbered steps, and quality-critical steps sit inside a validator loop that proceeds only on pass. | Judgment |
| 4 | Judgment over rules | No instruction survives that the model would follow unprompted (the subtraction test in `references/authoring-guidelines.md`). Commands inside a validator loop are exempt. | Judgment |
| 5 | Single source of truth | No idea is stated in two files. Where two would overlap, one owns it and the other links. | Judgment |
| 6 | Reachability | Every referenced path exists, is one level from `SKILL.md`, and is reached by at least one route. Reference files over 100 lines have a Contents list. Files no route reads are deleted or deliberately unlinked (evals). | Linter |
| 7 | Scope | One skill, one capability. Two unrelated jobs fail; so does a skill that only routes to another skill. | Judgment |
| 8 | Consistent terminology | One term per concept throughout the skill and its bundled files. | Judgment |
| 9 | Concrete over abstract | Output shapes ship as templates; style-dependent outputs ship as input/output pairs; one default with an escape hatch, never a menu of equivalent options; no "make sure it is good" where a gradeable condition could stand. | Judgment |
| 10 | No time-bound content | No rule that becomes wrong on a date. Old methods sit under an "Old patterns" block. | Linter (router and workflows) + judgment (references) |
| 11 | Scripts solve, don't defer | Scripts handle their own error cases, every constant carries a reason, validators report the specific problem and the valid alternatives, execute-versus-read intent is stated at each reference, required packages are listed, MCP tools are named `Server:tool`. | Linter (intent, script-constants) + judgment (the rest) |
| 12 | Evals exist | `evals/evals.json` holds at least three cases, each with a prompt and at least two observable expected and two forbidden behaviours, written before the body was extended. | Linter (presence) + judgment (observable, written first) |
| 13 | Token budget | `SKILL.md` is under 150 lines and, in a skill with more than one route, every route loads less than half of the bundled bytes, as the linter reports. | Linter |
| 14 | Observed behaviour | A fresh session per required profile has used the skill on a real prompt since its last edit, and the trace shows `SKILL.md` read first, every reference the task needed opened in full, no bundled file read on every run, and no bundled file unread across all runs without a stated reason. | Trace script (fired, reads, order, partial reads, unread) + judgment (whether the files read were the right ones) |

## Output

One line per dimension, in order. A pass needs no justification beyond the verdict. A fail names the edit:

```
2 · forced context — FAIL: SKILL.md is 437 lines and its Prerequisites section
    requires three docs (43 KB) before step 1.
    Fix: replace Prerequisites with a Files table whose last column is "read it when".
```

A fail without a specific edit is not a finding, it is a complaint.
