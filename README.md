# Global Agent Skills

This repository stores user-global skills discovered by Pi from `~/.agents/skills/`.

## Layout

Normal skills are self-contained:

```text
skills/<skill-name>/
├── SKILL.md
├── references/   # optional, one-level task knowledge
├── workflows/    # optional, one-level task procedures
├── evals/        # optional, provider-neutral cases
├── scripts/      # optional deterministic checks
└── assets/       # optional
```

`emil-design-eng` is the sole skill and command for the consolidated motion and interaction family. The temporary compatibility aliases have been removed.

`SKILL-AUTHORING-REVIEW.md` documents the authoring review and provider-neutral evaluation plan for the locally maintained skills.

## Management

- Pi discovers these skills automatically; no `settings.json` mapping is required.
- Keep project-specific configuration in the project that consumes a skill rather than modifying the installed skill package.
- `.skill-lock.json` retains installer metadata for third-party skills. Locally maintained skills in this repository are intentionally not lock-managed.
- Generated dependencies and caches are ignored. A skill with a package manifest should install its dependencies within its own directory.

## Validation

Validate the consolidated motion family without running models:

```bash
python3 skills/emil-design-eng/scripts/validate.py
```

The command checks the umbrella, retired-name absence, direct links and anchors, package inventory, long-reference contents sections, installer lock state, active command references, and provider-neutral evaluation definitions.
