---
name: authoring-skills
description: Creates new Agent Skills and improves existing ones for reliable triggering, better outcomes, and lower token cost, with a linter that measures the tokens a skill forces on every trigger. Use when the user wants to author, package, review, shrink, or debug a skill, or health-check a skills directory, or says "create a skill", "make a skill for", "turn this into a skill", "improve this skill", "make this skill token efficient", "review my skill", "this skill never triggers", "why isn't my skill firing", "audit my skills", "skills health check", "which skills need work", "tune this skill", "Claude ignores the rule in my skill", "my skill reads the wrong files", "the skill works on the big model but not the small one", or names an installed skill and asks to make it smaller, cheaper, faster to load, or more token efficient.
---

# authoring-skills

Keep skills discoverable, useful, and economical. Clients usually advertise metadata first, deliver instructions on selection or explicit invocation, and load supporting resources as needed. Exact loading, caching, and permissions vary by client. The linter reports static estimates, not measured tokens or task quality.

## Contracts

The rules that cannot be derived from the files themselves. Everything else is judgment.

- Portable format: YAML frontmatter with `name` matching its directory and a non-empty `description`. Optional fields and client extensions have distinct contracts in the compatibility reference.
- Local setup: global source here is `~/.agents/skills/`, exposed to Claude Code through a symlink. Choose project/user location for the actual client; never assume a project copy wins or an editing path is the loaded path.
- House defaults: one capability per skill, a small router, clear resource routing, imperative body instructions. Shared references and short safety reminders are valid when useful. Scripts normally execute without source reads; debugging/security review are exceptions.
- Repository release policy: schema-1 `evals/evals.json`, at least three execution cases, all three required profiles, and full rubric/evidence review. Write cases before extensive body expansion; static presence proves neither authorship timing nor execution.
- Improve modes: review-only for reviews/questions (no edits or model calls), targeted repair for narrow changes, comprehensive improvement for explicit broad/release work. Match checks to scope; ask before expanding it.
- Linter success proves only its selected static checks. No observed pass without primary evidence; report unassessed or blocked coverage explicitly.
- Prefer portable core instructions. Label client-only features and safe fallbacks; do not treat metadata as permission enforcement.
- Obtain approval before widening scope, paid/model calls, or changing installed copies outside the requested target.

## Workflow

Select the single best-matching workflow and read its file before acting.

| Workflow | When to call it | File to read |
| --- | --- | --- |
| Create | The prompt asks for a new skill, or to package a workflow, procedure, or expertise into one | `workflows/create-skill.md` |
| Improve | The prompt asks to fix, shrink, review, make token efficient, or debug the triggering of a skill that already exists, or to tune it against observed runs | `workflows/improve-skill.md` |
| Audit | The prompt asks about a skills directory as a whole: a health check, which skills need work, what is broken | `workflows/audit-skills.md` |

## Files

Paths are relative to this skill's own directory (announced as the base directory when the skill loads), not the working directory.

| Path | What it is | Read it when |
| --- | --- | --- |
| `references/compatibility.md` | Portable format, named clients, local policy, runtime setup | Deciding frontmatter, discovery, collisions, permissions, or script prerequisites |
| `references/authoring-guidelines.md` | Authoring recommendations and evaluation principles | Deciding a name, description, structure, script, cut, or evaluation. Read enough of the relevant sections |
| `references/review-rubric.md` | Fourteen stable dimensions with pass/fail/not assessed/not applicable evidence states | Comprehensive assessment, or relevant dimensions for a scoped review/repair or audit |
| `references/tuning-diagnostics.md` | The observe, diagnose, refine, retest loop; the navigation signals a trace exposes; a symptom-to-edit table | Diagnosing an observed run, or deciding what edit a symptom implies |
| `templates/SKILL.md` | Frontmatter and section skeleton for a new skill | Authoring a `SKILL.md` from scratch |
| `templates/evals.json` | Local schema-1 execution suite skeleton | Writing a new skill's evals |
| `evals/trigger-queries.json` | Frozen labeled discovery corpus, separate from execution cases | Evaluator preparing approved discovery runs; keep validation/fresh details out of optimizer/edit prompts |
| `scripts/lint_skill.py` | Format/local-contract errors, attributed advice, static context estimates | Run `uv run --offline --script <base>/scripts/lint_skill.py <skill-dir>` after approved setup; inspect source for debugging/security/interface work |
| `scripts/run_fresh_session.py` | Capture outcomes, manifest identity, trace and supplemental evidence | Run with Python only after approved live preflight in tuning diagnostics; inspect source when debugging/security-reviewing it |
| `scripts/trace_skill_use.py` | Correlated delivery evidence and requested read windows | Run `python3 <base>/scripts/trace_skill_use.py <skill-dir> <transcript>` on saved evidence; inspect source when debugging/security-reviewing it |
