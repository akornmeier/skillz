---
name: project-course
description: Sets up and maintains an opt-in project course at specs/COURSE.md (North Star, milestones linked to planf3 specs, non-goals, protected boundaries, an area and verification map, and an append-only decision log) and runs read-only drift audits that separate certain, evidence, and inference findings. Use when the user asks to set up a project course, create or update specs/COURSE.md, run a project drift audit, map the as-built areas, or record, accept, or supersede course decisions and proposals. Not for planning one feature (planf3), closing one ticket (finish-line), or YAML expertise files (mental-model).
compatibility: Requires Python 3.9+ and the sibling planf3 skill, whose scripts/validate_plan.py and scripts/course_parser.py the drift checker imports.
metadata:
  category: implementation-planning
---

# Project Course

One file keeps a project on course across sessions and plans: `specs/COURSE.md`. It names where the project is going, which `planf3` specs serve each milestone, what is out of scope, what must not be touched without asking, and which decisions are settled. It is opt-in. A repository without it works exactly as before, and this skill never adds other required docs.

## Contracts

- **One canonical path.** The course lives at `specs/COURSE.md`, next to the plans it links. Other files may point to it in one or two lines; never copy its content elsewhere.
- **Only accepted text carries authority.** Plans, shipping skills, and audits treat everything else as context, never as a constraint:
  - **Governed prose and boundaries** (North Star, Non-Goals, Precedence, Protected Boundaries) are accepted when present and neither marked `Inferred — needs developer review` nor inside a `> PROPOSED` block.
  - **Decision Log rows and linked `docs/decisions/` ADRs** are accepted only with `Status: Accepted` (a bare `Accepted` cell counts). A row marked `Superseded by D-NNN` is history, not authority.
  - **Bookkeeping is exempt.** Updating a milestone's `Spec` or `Status` and correcting the Area & Verification Map need no approval.
  - Every template placeholder starts with the `Inferred` mark, so a fresh course constrains nothing until the developer accepts it.
- **Changing accepted text needs the developer.** Accepting an inferred entry, adding or superseding a decision, and editing goals, non-goals, precedence, or protected boundaries require explicit approval in the conversation. Without it, append a dated `> PROPOSED YYYY-MM-DD (agent): <change>. Reason: <why>.` block under Pending Proposals.
- **Milestone status vocabulary is fixed:** `Planned | Active | Done | Dropped`.
- **Link, don't duplicate.** When the repo already has ADRs under `docs/decisions/` or a `mental-model` expertise file, link them from the course instead of restating them.
- **Read-only by default.** `init-course` writes only `specs/COURSE.md` (and an approved pointer line); `drift-audit` edits nothing. Neither changes code.
- **No boilerplate.** Never add a required doc tree, archive folders, tracker headers, per-repo check scripts, or version stamps. Git history is the archive.

## Precedence

When sources disagree, the course's own Precedence list wins. If it has none accepted, use: accepted Protected Boundaries and decisions, then the accepted North Star and Non-Goals, then the active plan, then code comments and older docs. Surface every conflict; never resolve one silently.

## Route to one workflow

Read only the matching workflow before acting:

| Workflow | Use when | File |
| --- | --- | --- |
| Init Course | No `specs/COURSE.md` exists and the user wants one, or wants the as-built areas mapped | [workflows/init-course.md](workflows/init-course.md) |
| Drift Audit | The user asks whether the project, its plans, or its docs have drifted from the course | [workflows/drift-audit.md](workflows/drift-audit.md) |
| Update Course | Recording, accepting, or superseding a decision; applying or rejecting a proposal; updating milestones or the area map; acting on stale-doc triage | [workflows/update-course.md](workflows/update-course.md) |

If `specs/COURSE.md` already exists, Init Course hands off to Update Course instead of overwriting it.

## Resources

- [templates/COURSE.md](templates/COURSE.md) — starter course; copy it, never edit the template in place.
- `scripts/check_drift.py` — deterministic `Certain` checks. Run `python3 <skill-directory>/scripts/check_drift.py --repo-root .` (add `--json` for machine output). Exit 0 means no certain failures (warnings allowed), 1 means at least one, 2 means bad input or a missing sibling script. It checks that milestone specs, area-map paths, and decision links exist, that milestone status matches linked task markers, that decision IDs are unique, and that every `specs/*.html` plan validates for its class: legacy plans and retired plans (whose `forward refs` end in `; Retired: ...` or `; Superseded by ...`) are skipped with a warning, completed plans are validated without file checks, and active plans are validated with `--repo-root`.
- `../planf3/scripts/course_parser.py` — the shared parser that `check_drift.py` and planf3's `spec_guard.py` both use; do not read it for instructions.

## How the rest of the suite uses the course

- [planf3](../planf3/SKILL.md) reads accepted course text when creating plans, links each plan to its milestone both ways, and marks the milestone `Done` when its specs finish.
- `full-send`, `half-send`, and `babysit-pr` run planf3's `spec_guard.py`, which stops unapproved edits to accepted course text and protected paths on a PR.
- `finish-line` closes one ticket; this skill checks the whole project.
