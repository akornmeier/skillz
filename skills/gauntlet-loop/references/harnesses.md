# Harness Adapters

The Gauntlet Loop is a workflow, not a universal command. Verify capabilities in the active environment before naming them.

## Claude Code

Use Claude Code's installed subagent mechanism to obtain clean role contexts. Ask for the highest supported effort level when the user accepts the additional cost.

`/loop`, `/effort`, and an `ultracode` option are version- or environment-specific. Mention exact slash commands only when they are known to exist or the user explicitly asks for that syntax. Otherwise say:

> Use subagents with fresh contexts and the highest reasoning effort supported by this Claude Code environment.

A fresh critic should receive the original goal, bar, relevant rules, and actual artifact, but not the builder transcript or self-assessment.

## Codex

Codex capabilities differ by product and installation. Request isolated agents or workspaces and the highest available reasoning effort without calling it ultracode. If isolated subagents are unavailable, the harness cannot perform strict independent criticism; return the launch prompt or ask the user to choose a capable environment.

Prefer objective gates for backend and systems work, while still using fresh critics to inspect the actual implementation and command output.

## Pi

Pi core has no built-in subagents, `/loop`, `ultracode`, autonomous loop scheduler, maximum-round flag, or cost-budget flag. A Pi skill cannot create fresh contexts by itself.

Faithful execution requires a loaded extension/controller or explicit isolated child processes. Tool names and schemas are installation-specific; inspect available tools instead of assuming `subagent`, `dispatch_agent`, or `dispatch_team`.

A suitable child-agent pattern uses a separate ephemeral invocation, for example conceptually:

```bash
pi --mode json -p --no-session --thinking high "<role prompt>"
```

This is not a complete secure controller. A real controller must also define tool allowlists, workspace isolation, bounded concurrency, usage aggregation, cancellation propagation, output capture, and child-process cleanup. Pi has no built-in sandbox; a child has the operating-system permissions of its process.

Thinking levels are model/provider dependent. Request the maximum supported level rather than assuming `max` is accepted. Do not describe Pi's thinking setting as ultracode.

Aborting an interactive parent does not guarantee arbitrary spawned children are terminated. A controller or extension must propagate cancellation. Hard cost, token, runtime, and round limits require controller logic; prompt wording alone is only a soft limit.

## Unknown harness

Use capability-oriented wording:

> Use isolated fresh-context subagents and the highest supported reasoning effort. Parallelize independent work only when writers have isolated workspaces. If genuine context isolation is unavailable, state that the independent-builder/critic contract cannot be guaranteed.

Do not simulate multiple agents as role-play in one context and call it independent review.
