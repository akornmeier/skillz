# Global Agent Skills

This repository stores user-global skills discovered by Pi from `~/.agents/skills/`.

## Layout

Skills and their evaluation contracts are self-contained; shared evaluation infrastructure stays at repository root:

```text
skills/<skill-name>/
├── SKILL.md
├── references/   # optional, one-level task knowledge
├── workflows/    # optional, one-level task procedures
├── evals/        # provider-neutral cases owned by this skill
├── scripts/      # optional deterministic checks
└── assets/       # optional

evals/
├── README.md
├── profiles.example.json
├── run-record.schema.json
└── scripts/      # repository-wide definition validation
```

`emil-design-eng` is the sole skill and command for the consolidated motion and interaction family. The temporary compatibility aliases have been removed.

`SKILL-AUTHORING-REVIEW.md` documents the authoring review and provider-neutral evaluation plan for the locally maintained skills.

## Management

- Pi discovers these skills automatically; no `settings.json` mapping is required.
- When this repository is cloned elsewhere, `scripts/link-skills.sh` symlinks each skill into `~/.agents/skills` (Pi) and `~/.claude/skills` (Claude Code), and prunes links to skills removed from the repository. Pass `-n` for a dry run or other directories as arguments. Run it once with `--install-hooks` to relink automatically after every `git pull`, merge or rebase, preserving the selected target directories (relative paths are anchored to the installation directory). Existing hooks not managed by this script are left untouched with a warning; integrate the linking command manually if needed.
- Keep project-specific configuration in the project that consumes a skill rather than modifying the installed skill package.
- `.skill-lock.json` retains installer metadata for third-party skills. Locally maintained skills in this repository are intentionally not lock-managed.
- Generated dependencies and caches are ignored. A skill with a package manifest should install its dependencies within its own directory.

## PR workflow

`file-pr` files the PR, `babysit-pr` watches it through CI and review bots (its `scripts/pr-wait` watcher, or `watch_pull_request` in T3 Code), and `leaving-pr-comments` formats any comment posted on the user's behalf. `full-send` chains these into an unattended run that merges; `half-send` stops with the PR ready for the user. `sol-loop` and `council` add cross-model review before or after filing, and `hillclimb` frames a goal and runs council rounds until every score clears a bar; `modernize` and `takeover` pick up existing PRs, and `finish-line` checks a planf3 spec, GitHub issue, or in-conversation task against the code and closes it once nothing is left. For a structural audit, run `/thermo-nuclear-code-quality-review` (Pi: `/skill:thermo-nuclear-code-quality-review`) yourself; no skill invokes it.

## Project course

`project-course` keeps a repository on course across sessions with one opt-in file, `specs/COURSE.md`: a North Star, milestones linked to `planf3` specs, non-goals, protected boundaries, an area and verification map, and an append-only decision log. Only accepted entries carry authority; agents propose changes instead of editing them. `planf3` reads the course when planning, links each plan to its milestone, and marks the milestone done after a build. `full-send`, `half-send`, and `babysit-pr` run `planf3`'s `scripts/spec_guard.py` (see `skills/planf3/references/linked-spec-guard.md`) so a PR cannot silently change accepted criteria, course text, or protected paths. `finish-line` closes one ticket; a `project-course` drift audit checks the whole project read-only and reports certain, evidence, and inference findings separately.

## Validation

Check skill linking and generated hooks in temporary directories:

```bash
python3 scripts/test_link_skills.py
bash -n scripts/link-skills.sh
shellcheck scripts/link-skills.sh
```

Validate every skill's evaluation definitions and local Markdown links without running models:

```bash
node evals/scripts/validate-cases.mjs
```

Run the plan, guard, and drift checkers' unit tests, then the drift check on this repository:

```bash
python3 -m unittest skills/planf3/evals/test_validate_plan.py skills/planf3/evals/test_spec_guard.py skills/project-course/evals/test_check_drift.py
python3 skills/project-course/scripts/check_drift.py --repo-root .
```

Validate the consolidated motion family package:

```bash
python3 skills/emil-design-eng/scripts/validate.py
```

See [evals/README.md](evals/README.md) for capability profiles, isolation requirements, run records, and evaluation provenance.
