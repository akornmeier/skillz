<!-- TEMPLATE, not a skill. Copy to the new skill's directory as SKILL.md, then delete
     this comment: frontmatter must be the file's first line. Delete any section the
     skill has no use for; an empty heading is worse than a missing one. -->
---
name: skill-name
description: Describes the capability, intended situations, and relevant boundaries in plain language.
# Optional portable fields: license (string), compatibility (1–500 characters),
# metadata (string map), allowed-tools (experimental space-separated string).
# Declare actual environment requirements; never invent a license or permission guarantee.
---

# Skill Name

One paragraph: what this skill is for and what it produces. Not why it exists, not its history.

## Contracts

State exact contracts and costly safety boundaries. Label portable requirements, named client behavior, and project policy separately.

- <an exact path, filename, or output format>
- <an opinion that is the author's, not the model's default>
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
3. Run `<validator>`; fix and rerun until it passes.

## Files

Resolve paths from this skill's own directory, not the working directory. Read the sections needed for the task; shared references are valid when justified. Keep one owner for detailed contracts, with short safety reminders where mistakes would be costly.

| Path | What it is | Read it when |
| --- | --- | --- |
| `templates/<file>` | <what it is> | <the condition that makes it worth opening> |
| `references/<file>.md` | <what it is> | <the condition> |
| `scripts/<file>` | <interface, dependencies, exits, safe failure> | Run at <step>; inspect for debugging/security review |
