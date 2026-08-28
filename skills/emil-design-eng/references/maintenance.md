# Consolidation maintenance

## Package and eval layout

```text
skills/emil-design-eng/
├── SKILL.md
├── references/
│   ├── motion-principles.md
│   ├── motion-standards.md
│   ├── apple-design.md
│   ├── animation-vocabulary.md
│   ├── design-engineering-catalog.md
│   ├── animation-plan-template.md
│   ├── provenance.md
│   └── maintenance.md
├── workflows/
│   ├── apply-motion.md
│   ├── find-opportunities.md
│   ├── review-motion.md
│   ├── improve-motion.md
│   └── prototype.md
├── evals/
│   └── evals.json
└── scripts/
    └── validate.py
```

Keep router short. Every task leaf lives exactly one directory below package root and is linked directly from `SKILL.md`. Do not add reference-to-reference routing chains. Root selects the complete file set for a mode.

`evals/evals.json` is provider-neutral. Every case names expected mode, self-contained prompt, and observable assertions. Run every case in a fresh session across fast/economical, balanced/default, and highest-reasoning profiles. Record provider, model, thinking level, Pi version, loaded files, tokens, tool calls, routing result, assertion results, unauthorized mutations, and visual checks that actually ran.

## Relative-link rules

- Resolve a link relative to the Markdown file containing it.
- Package links from `SKILL.md` use `references/file.md` or `workflows/file.md`.
- Leaf files should use local anchors, not sideways links to other leaves.
- Never use CWD-relative paths for bundled files. Agents must resolve them from the loaded skill directory.

## Retired command names

The transition aliases have been removed. Do not recreate packages named `animation-vocabulary`, `apple-design`, `find-animation-opportunities`, `improve-animations`, `prototype`, or `review-animations`. Route callers to an explicit `emil-design-eng` mode instead.

Pi does not create redirects for deleted skills, and running sessions retain their startup discovery snapshot. Restart Pi after package changes. Old commands should be unknown in a fresh session.

## Discovery and collision caveats

- Pi recursively discovers every directory containing `SKILL.md` under `~/.agents/skills/`, including nested packages.
- Same-name skills from global, project, package, settings, or CLI locations collide. Pi warns and keeps the first discovered definition. Do not rely on load order.
- Pi permits a frontmatter name that differs from the parent directory, but the Agent Skills standard does not. These packages keep names and directories equal.
- Root `.md` discovery differs between `.pi/skills` and `.agents/skills`. Use `<name>/SKILL.md` packages for portable behavior.
- Keep the umbrella and retired names out of `.skill-lock.json`; otherwise installer updates can restore or overwrite locally maintained content.
- A running Pi session retains its startup discovery snapshot. Restart Pi after adding or removing skills.

## Post-removal gates

1. Run `python3 skills/emil-design-eng/scripts/validate.py` from repository root.
2. Start a fresh Pi session and require zero diagnostics and exactly one Emil-family command.
3. Confirm old commands are absent from completion and unknown when entered.
4. Run every eval case across all three capability profiles. Require correct routing, no unauthorized mutations, and no quality regression against retained baselines.
5. Search active prompts, agents, docs, settings, package manifests, scripts, CI, and project configs for retired command invocations and explicit legacy skill paths.
6. Confirm `.skill-lock.json` contains neither the umbrella nor retired names.
7. Check project, package, settings, and CLI skill sources so duplicate legacy packages cannot silently restore old commands.
