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

## PR review

`file-pr` reviews the committed diff for introduced bugs before every new-code upload, in both Claude Code (`/file-pr`, using the `code-review` skill) and Pi (`/skill:file-pr`, using a nested read-only `pi` run). Unresolved P0–P2 findings stop the upload; only an explicit per-attempt user waiver skips review, labeled bypassed. For a structural audit, run `/thermo-nuclear-code-quality-review` (Pi: `/skill:thermo-nuclear-code-quality-review`) yourself; it is not part of the gate.

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

Validate the consolidated motion family package:

```bash
python3 skills/emil-design-eng/scripts/validate.py
```

See [evals/README.md](evals/README.md) for capability profiles, isolation requirements, run records, and evaluation provenance.
