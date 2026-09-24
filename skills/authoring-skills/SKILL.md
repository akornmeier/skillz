---
name: authoring-skills
description: Creates new Agent Skills and improves existing ones for reliable triggering, better outcomes, and lower token cost, with a linter that measures the tokens a skill forces on every trigger. Use when the user wants to author, package, review, shrink, or debug a skill, or health-check a skills directory, or says "create a skill", "make a skill for", "turn this into a skill", "improve this skill", "make this skill token efficient", "review my skill", "this skill never triggers", "why isn't my skill firing", "audit my skills", "skills health check", "which skills need work".
---

# authoring-skills

A skill is a directory holding a `SKILL.md` and whatever it needs beside it. Three tiers load at three moments: the frontmatter is always in context and decides firing; the `SKILL.md` body loads when the description matches and is paid on every trigger; bundled files load only when a route reads them, and scripts run without being read at all. Writing a skill is deciding what belongs at which tier, and pushing as much as possible rightward.

## Contracts

The rules that cannot be derived from the files themselves. Everything else is judgment.

- Frontmatter is required and `name` equals the directory name. Both are checked by the linter.
- Global skills live in `~/.agents/skills/`, the cross-agent directory; Claude Code reads them through its `~/.claude/skills` symlink. Project skills live in `.claude/skills/`, where git shares them with the team.
- One skill is one capability. Two unrelated jobs are two skills.
- `SKILL.md` is the only file loaded on every trigger. Every other path carries a read-it-when condition, and no instruction anywhere says to read a file unconditionally.
- Every skill ships `evals/evals.json`, written before its body: three cases, each with a prompt and observable expected and forbidden behaviours.
- A skill is not done until a run of `scripts/lint_skill.py` exits 0 and every dimension of `references/review-rubric.md` passes.
- Skills stay cross-agent: no Claude Code-only syntax in any `SKILL.md`.

## Workflow

Select the single best-matching workflow and read its file before acting.

| Workflow | When to call it | File to read |
| --- | --- | --- |
| Create | The prompt asks for a new skill, or to package a workflow, procedure, or expertise into one | `workflows/create-skill.md` |
| Improve | The prompt asks to fix, shrink, review, make token efficient, or debug the triggering of a skill that already exists | `workflows/improve-skill.md` |
| Audit | The prompt asks about a skills directory as a whole: a health check, which skills need work, what is broken | `workflows/audit-skills.md` |

## Files

Paths are relative to this skill's own directory (announced as the base directory when the skill loads), not the working directory.

| Path | What it is | Read it when |
| --- | --- | --- |
| `references/authoring-guidelines.md` | The official authoring rules, condensed; its Contents list names ten sections | Deciding a name, description, structure, script, or cut. Read the section for the decision at hand, not the file |
| `references/review-rubric.md` | Thirteen pass/fail dimensions, each with who proves it and the edit that fixes a failure | Grading a skill: last step of Create, first step of Improve, per flagged skill in Audit |
| `templates/SKILL.md` | Frontmatter and section skeleton for a new skill | Authoring a `SKILL.md` from scratch |
| `templates/evals.json` | Eval suite skeleton with three case stubs | Writing a new skill's evals |
| `scripts/lint_skill.py` | Reports every mechanically provable defect with its fix, and the tokens each route forces | Never. Run it: `python3 <base>/scripts/lint_skill.py <skill-dir>`; no argument scans every installed skill |
