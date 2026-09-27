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
- When this repository is cloned elsewhere, `scripts/link-skills.sh` symlinks each skill into `~/.agents/skills` (Pi) and `~/.claude/skills` (Claude Code), and prunes links to skills removed from the repository. Pass `-n` for a dry run or other directories as arguments. Run it once with `--install-hooks` to relink automatically after every `git pull`, merge or rebase.
- Keep project-specific configuration in the project that consumes a skill rather than modifying the installed skill package.
- `.skill-lock.json` retains installer metadata for third-party skills. Locally maintained skills in this repository are intentionally not lock-managed.
- Generated dependencies and caches are ignored. A skill with a package manifest should install its dependencies within its own directory.

## Validation

Validate every skill's evaluation definitions and local Markdown links without running models:

```bash
node evals/scripts/validate-cases.mjs
```

Validate the consolidated motion family package:

```bash
python3 skills/emil-design-eng/scripts/validate.py
```

See [evals/README.md](evals/README.md) for capability profiles, isolation requirements, run records, and evaluation provenance.
