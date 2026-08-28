---
name: find-animation-opportunities
description: Temporary explicit-only compatibility alias. Finds animation opportunities through the consolidated Emil design-engineering skill.
disable-model-invocation: true
metadata:
  alias-for: emil-design-eng
  mode: opportunities
---

# Temporary compatibility alias

Read [the umbrella skill](../emil-design-eng/SKILL.md), then route this request to `opportunities` mode. Follow the umbrella's boundaries and load only files named for that mode.

Pi appends arguments from `/skill:find-animation-opportunities ...` to this file as a final `User: <arguments>` block. Treat that block as the request for `opportunities` mode. Do not look for `{{args}}`, `$ARGUMENTS`, shell expansion, command substitution, or nested slash-command execution. Pi does not interpolate those forms in skill Markdown.

This alias is temporary. Do not copy its content into new prompts, agents, or documentation. Use `/skill:emil-design-eng opportunities ...` instead.
