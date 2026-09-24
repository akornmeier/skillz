---
name: meta-skill
description: Creates, improves, and reviews Claude Code Agent Skills. Use when the user wants to author a new skill, package a workflow or domain expertise into one, rightsize a skill that has grown too long, work out why a skill never fires, or health-check the whole skills directory to find which ones need work. Triggers on "create a skill", "make a skill for", "turn this into a skill", "improve this skill", "review my skill", "this skill never triggers", "why isn't my skill firing", "skills health check", "audit my skills", "which skills need work".
---

# meta-skill

A skill is a directory holding a `SKILL.md` and whatever it needs beside it. The frontmatter is
always in context, the body loads when the description matches, and the bundled files load only
when something reads them. Writing a skill is deciding what belongs at which of those levels.

## Contracts

The rules you cannot derive from the files themselves. Everything else is your judgment.

- Frontmatter is required. `name` is lowercase-hyphen and matches the directory the skill lives in.
- Personal skills live in `~/.claude/skills/`, project skills in `.claude/skills/` where git
  shares them with the team.
- One skill is one capability. Two unrelated jobs are two skills.
- `SKILL.md` is the only file loaded on every trigger. Every other path carries a condition for
  opening it, and no instruction anywhere says to read one unconditionally.
- A bundled file that no route reads should not exist.
- Grade against `references/skill-review-rubric.md` before calling a skill done.

## Workflow

Select the single best-matching workflow and read its file for step-by-step instructions
before acting.

| Workflow | When to call it | File to read |
| --- | --- | --- |
| Create Skill | The prompt asks for a new skill, or to package a workflow or expertise into one | `workflows/create-skill.md` |
| Improve Skill | The prompt asks to fix, shrink, review, or debug the triggering of a skill that already exists | `workflows/improve-skill.md` |
| Audit Skills | The prompt asks about the skills directory as a whole — a health check, which skills need work, what is broken | `workflows/audit-skills.md` |

## Files

Paths below are relative to this skill's own directory — Claude Code announces it as
"Base directory for this skill" when the skill loads — not to the working directory.

| Path | What it is | Read it when |
| --- | --- | --- |
| `templates/SKILL.md` | Frontmatter and section skeleton for a new skill | Authoring a `SKILL.md`, on either route |
| `references/context-engineering-claude5.md` | The Claude 5 rules for what to put in a skill and what to cut | Deciding what belongs in a skill, or running the subtraction test on a draft |
| `references/skill-review-rubric.md` | Gradeable pass conditions, one per dimension | Grading a skill — last step of create, first step of improve |
| `scripts/scan.py` | Mechanical pre-pass over every installed skill: what loads, what has a provable defect | Never — the Audit route executes it |
| `docs/claude_code_agent_skills.md` | Upstream Claude Code skills guide | A Claude Code-specific format detail is genuinely in question |
| `docs/claude_code_agent_skills_overview.md` | Upstream architecture doc, including cross-surface limits | A limit, or a surface other than Claude Code, is in question |
| `docs/blog_equipping_agents_with_skills.md` | Anthropic's Skills launch post | The original progressive-disclosure argument is wanted in its own words |
