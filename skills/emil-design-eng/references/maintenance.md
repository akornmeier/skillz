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
- Temporary sibling aliases may use `../emil-design-eng/SKILL.md`. This cross-package link is intentional and must disappear with the alias.
- Never use CWD-relative paths for bundled files. Agents must resolve them from the loaded skill directory.

## Pi-compatible alias pattern

```yaml
---
name: review-animations
description: Temporary explicit-only compatibility alias. Reviews animation code through the consolidated Emil design-engineering skill.
disable-model-invocation: true
metadata:
  alias-for: emil-design-eng
  mode: review
---
```

Alias body must tell the agent to read `../emil-design-eng/SKILL.md` and select the declared mode. `disable-model-invocation: true` hides it from the system prompt but retains `/skill:review-animations`.

Pi appends slash-command arguments to loaded skill content as a final `User: <arguments>` block. The alias hands that final block to the selected umbrella mode as the request. Skill Markdown has no supported `{{args}}`, `$ARGUMENTS`, shell interpolation, command substitution, or nested slash-command forwarding. Do not fake forwarding with those forms.

## Discovery and collision caveats

- Pi recursively discovers every directory containing `SKILL.md` under `~/.agents/skills/`, including nested packages.
- `disable-model-invocation` prevents automatic model routing. It does not remove the slash command.
- Same-name skills from global, project, package, settings, or CLI locations collide. Pi warns and keeps the first discovered definition. Do not rely on load order.
- Pi permits a frontmatter name that differs from the parent directory, but the Agent Skills standard does not. These packages keep names and directories equal.
- Root `.md` discovery differs between `.pi/skills` and `.agents/skills`. Use `<name>/SKILL.md` packages for portable behavior.
- Remove consolidated names from `.skill-lock.json`; otherwise an installer update can overwrite local aliases or umbrella content.
- A running Pi session retains its startup discovery snapshot. Restart Pi after adding, hiding, or removing skills.

## Gates before deleting aliases

1. Run `python3 skills/emil-design-eng/scripts/validate.py --pre-remove-aliases` from repository root.
2. Start fresh Pi sessions and confirm startup reports zero skill diagnostics, one automatic umbrella, and all six explicit slash commands.
3. Invoke every alias with a unique argument sentinel. Confirm selected umbrella mode receives the final `User:` block unchanged.
4. Run every eval case across all three capability profiles. Require correct routing, no unauthorized mutations, and no quality regression against retained baselines.
5. Confirm all active prompts, agents, docs, settings, packages, and project configs no longer call old skill commands. Historical migration notes may retain names.
6. Confirm `.skill-lock.json` contains none of the umbrella or alias names.
7. Commit alias removal separately. Restart Pi and confirm old slash commands are absent while umbrella commands still pass.

Do not remove aliases based only on elapsed time. Remove them when command references and eval failures reach zero.
