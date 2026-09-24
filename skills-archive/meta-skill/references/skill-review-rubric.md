# Skill review rubric

Grade a skill against every dimension. Each is pass/fail against a stated condition — not a
score out of five. A failure is only reported with the edit that would fix it.

| # | Dimension | Passes when |
| --- | --- | --- |
| 1 | Description triggers | `description` states both what the skill does and when to fire, and names the phrasing a user actually types. A stranger reading only the frontmatter can say yes or no to "should this fire?" for a given prompt. |
| 2 | Forced context | `SKILL.md` is under 500 lines and no instruction in it requires reading another file unconditionally. Everything the skill always pays for is in that one file. |
| 3 | Progressive disclosure | Every task the skill supports loads less than half of the bundled bytes. Each bundled path has a stated condition for opening it. |
| 4 | Judgment over rules | No instruction survives that Claude would follow unprompted — see the subtraction test in `context-engineering-claude5.md`. Commands inside a validator loop are exempt. |
| 5 | Single source of truth | No idea is stated in two files. Where two would overlap, one owns it and the other links. |
| 6 | Reachability | Every path named in the skill resolves to a file that exists, is at most one hop from `SKILL.md`, and is reached by at least one route. Files no route reads are deleted or deliberately unlinked (evals). |
| 7 | Scope | One skill, one capability. Two unrelated jobs in one skill fail this; so does a skill that only routes to another skill. |

## Output

One line per dimension:

```
2 · forced context — FAIL: SKILL.md is 437 lines and its Prerequisites section
    requires three docs (43 KB) before step 1.
    Fix: replace Prerequisites with a Files table whose last column is "read it when".
```

A pass needs no justification beyond the verdict. A fail without a specific edit is not a
finding, it is a complaint.
