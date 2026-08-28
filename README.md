# Global Agent Skills

This repository stores user-global skills discovered by Pi from `~/.agents/skills/`.

## Layout

Each skill is self-contained:

```text
skills/<skill-name>/
├── SKILL.md
├── references/   # optional
├── scripts/      # optional
└── assets/       # optional
```

`SKILL-AUTHORING-REVIEW.md` documents the authoring review and provider-neutral evaluation plan for the locally maintained skills.

## Management

- Pi discovers these skills automatically; no `settings.json` mapping is required.
- Keep project-specific configuration in the project that consumes a skill rather than modifying the installed skill package.
- `.skill-lock.json` retains installer metadata for third-party skills. Locally maintained skills in this repository are intentionally not lock-managed.
- Generated dependencies and caches are ignored. A skill with a package manifest should install its dependencies within its own directory.
