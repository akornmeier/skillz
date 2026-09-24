# Skill evaluations

This repository owns the behavioral evaluations for the skills under `skills/`. Pi does not load or execute these files at runtime.

## Layout

```text
evals/
├── profiles.example.json      # Capability-profile mappings
├── run-record.schema.json     # Evidence record for one case/profile run
├── scripts/
│   └── validate-cases.mjs     # Zero-dependency definition validator
└── runs/                      # Local evidence; ignored by Git

skills/<name>/evals/evals.json # Cases owned by one skill
```

Keep single-skill activation, near-miss, workflow, safety, and output cases with that skill. Put only genuinely cross-skill routing suites under `evals/suites/` if such a suite is added later. Do not duplicate case bodies centrally.

Do not place fixture packages containing `SKILL.md` below `skills/`; Pi recursively discovers them. Materialize simulated skills in disposable workspaces outside the repository's skill tree.

## Capability profiles

Run every case independently under three intent-based profiles:

- **fast/economical:** lowest-cost, low-latency model that supports the required tools and context.
- **balanced/default:** normal production model with its default thinking configuration.
- **highest-reasoning:** strongest available tool-capable model with the maximum appropriate thinking level.

Copy `profiles.example.json` to the ignored `profiles.local.json` and replace environment placeholders with local mappings. Record the exact provider, model ID, thinking level, and Pi version for every run.

## Run contract

For each case and profile:

1. Create a fresh disposable workspace from the case's setup.
2. Isolate the evaluated skill set from unrelated global and project skills.
3. Start a fresh Pi session with equivalent tools, permissions, prompt, and fixture across profiles.
4. For automatic-discovery cases, expose metadata normally and do not force-load the skill with `--skill` or `/skill:`.
5. For explicit-invocation cases, record that discovery was bypassed.
6. Block unapproved network, paid, publishing, merge, commit, installation, and production side effects.
7. Capture the transcript, stderr, output files, workspace diff, loaded files, and tool calls.
8. Grade every expected and forbidden behavior from primary evidence. Unverified criteria do not pass.
9. Save a run record conforming to `run-record.schema.json` under `evals/runs/<case-id>/<profile>.json`.

A typical non-interactive invocation is:

```bash
pi --no-session \
  --model "$PI_EVAL_MODEL" \
  --thinking "$PI_EVAL_THINKING" \
  --print "$PI_EVAL_PROMPT"
```

Adapt flags to the installed Pi version. Use a configurable repository and skills root; do not hardcode `~/code/pi-harness` or `~/.agents/skills` into runners or fixtures.

## Definition validation

Validate structure, profile coverage, repository skill coverage, IDs, and local Markdown links without running models:

```bash
node evals/scripts/validate-cases.mjs
```

The validator discovers current packages from `skills/*/SKILL.md`; it does not use a hardcoded skill inventory.

## Provenance

The original 39-case matrix was created in `pi-harness` commit `2ae8a84`, remained there when skill packages moved in `ff087a9`, and migrated Prototype coverage to the Emil umbrella in `4cff48f`. It was moved here and merged with the later per-skill suites so evaluations version with their owning skills.
