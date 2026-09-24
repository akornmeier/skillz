<!-- TEMPLATE, not a skill. Copy to the new skill's directory as SKILL.md, then delete
     this comment first — frontmatter must be the file's first line. Delete any section
     the skill has no use for; an empty heading is worse than a missing one. -->
---
name: skill-name
description: What it does, in one clause. Use when <situation>, or when the user says "<phrase a user actually types>", "<another phrase>".
---

# Skill Name

One paragraph: what this skill is for and what it produces. Not why it exists, not its history.

## Contracts

The rules you cannot derive from the files themselves. Everything else is your judgment.

- <an exact path, filename, or output format>
- <an opinion that is yours, not the model's default>
- <a boundary worth stating because getting it wrong is expensive>

## Workflow

<!-- Use this table when the skill has more than one route. Delete the Steps section. -->

Select the single best-matching workflow and read its file before acting.

| Workflow | When to call it | File to read |
| --- | --- | --- |
| <Name> | <the condition in the prompt that selects this route> | `workflows/<name>.md` |

## Steps

<!-- Use this instead when the skill has exactly one route. Delete the Workflow section. -->

1. <step> — <what it produces>
2. <step> — <what it produces>

## Files

| Path | What it is | Read it when |
| --- | --- | --- |
| `templates/<file>` | <what it is> | <the condition that makes it worth opening> |
| `references/<file>.md` | <what it is> | <the condition> |
| `scripts/<file>` | <what it does> | Never — <the step that executes it> |
