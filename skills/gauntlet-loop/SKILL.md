---
name: gauntlet-loop
description: Designs or runs multi-agent improvement loops with isolated builders, fresh critics, inspectable quality bars, iterative repair, and progress tracking. Use for reference-driven artifact improvement, independent review, blind comparison, or Gauntlet Loop launch prompts.
compatibility: Prompt design works in any harness. Faithful execution requires file access plus a delegation capability that starts isolated fresh-context agents; concurrent builders also require isolated workspaces.
metadata:
  category: orchestration
  version: "1.0"
---

# Gauntlet Loop

Turn a destination and a real standard of excellence into a compact launch prompt or, when explicitly requested and supported, run the loop.

The essential mechanism is:

> Lead decomposes → builder produces → fresh critic inspects and compares → builder closes the largest gap → fresh critic judges again.

## Determine the requested mode

- **Design mode (default):** choose the quality bar and return a short prompt the user can paste into an agentic harness.
- **Run mode:** use only when the user explicitly asks to start or execute the loop. Read [references/protocol.md](references/protocol.md) first.

Do not start expensive delegated work merely because the user asked for a prompt. If the request is ambiguous, default to design mode.

## Inputs

Extract:

- **Goal** — the outcome, not the user's guessed implementation.
- **References** — examples, screenshots, files, URLs, products, prose, specifications, implementations, tests, metrics, or datasets.
- **Constraints** — required stack or format, scope, safety, compatibility, deadline, and non-negotiable requirements.
- **Harness** — Claude Code, Codex, Pi, or another agentic environment.
- **Run controls** — optional time, cost, concurrency, or user-defined stop conditions.

If the goal is absent, ask for it. Ask another question only when the answer would materially change the scope, quality bar, safety, or spend. Never replace a clear goal with a detailed architecture or predetermined work breakdown.

## Choose an inspectable bar

Open supplied references when tools allow. Treat the real artifact as evidence; do not rely on the user's or builder's summary of it. If a reference cannot be opened, label it uninspected and include a note; never imply that it was inspected.

Read [references/quality-bar.md](references/quality-bar.md), then choose the strongest bar that the active harness can actually inspect:

1. Prefer the user's concrete reference or measurable requirement.
2. If several exist, use the strongest relevant reference set and required objective gates.
3. If none exists, find or propose a concrete comparison or measurement that serves the same directional role as real Call of Duty screenshots in a game-quality loop.
4. Explain the selected bar in one sentence.

Do not use adjectives such as “amazing,” “AAA,” or “production-ready” as the bar by themselves. Do not promise that a subjective reference can prove correctness, security, or performance; add objective gates where those qualities matter.

## Design the launch prompt

Read [references/launch-prompt.md](references/launch-prompt.md). Produce the shortest prompt that still preserves these contracts:

- Give the lead the **goal, bar, references, constraints, and stop controls**, not an architecture.
- Let the lead choose the approach and split the work into the smallest useful pieces that can be improved and judged independently.
- Assign each important piece to a builder and to a **separate critic in a fresh context**. Parallelize only independent work and require isolated workspaces or explicit non-overlapping ownership for concurrent writers.
- Critics inspect the real output—rendered pixels, running behavior, files, prose, test output, measurements, or other primary evidence—not builder summaries. Withhold builder rationale, self-assessment, identity, and the lead's preferred answer.
- Critics compare directly with the bar, using anonymized side-by-side A/B judging only for comparable alternatives under equivalent conditions; use direct gates for complementary work and correctness properties. A tie or insufficient evidence is not a win.
- A losing review identifies the largest **verified** material gap and returns it for a targeted repair, followed by another fresh review.
- Do not prescribe a fixed number of rounds. Continue while a material gap remains and another pass has a credible improvement hypothesis. A win requires every blocking gate to pass with no unresolved material loss; otherwise stop only on user cancellation, configured budget, blocked verification, or stalled progress and name the state honestly.
- Treat a user-specified round count as a maximum control, not evidence of success. Reaching the cap without a win means stopped, not won.
- Maintain a simple live `progress.html`, `progress.md`, or equivalent workbench with current artifacts and evidence.
- Allow a fresh, scope-preserving smoothing/integration pass after major waves when separately improved parts no longer feel coherent, then re-review the integrated result.
- Request subagents and the highest supported reasoning effort only in harness-appropriate language.

Keep implementation choices, exact decomposition, and role count out of the generated prompt. Include a user-specified round count only as a cap, never as a victory criterion.

## Design-mode output

Return only:

1. **Quality bar:** one sentence naming the reference/measurement and why it is inspectable.
2. **Launch prompt:** one compact fenced block, normally 1–4 short paragraphs.
3. **Note:** only when an inaccessible reference, missing agent capability, safety issue, or harness mismatch must be disclosed.

Do not bury the launch prompt beneath an essay. Do not repeat the entire protocol outside the prompt.

## Run mode requirements

A skill is guidance, not an orchestration runtime. Inspect the available tools before promising independent agents. Tool names vary by installation.

- Use only a delegation capability that starts every builder, critic, judge, and smoother in a separate fresh or ephemeral context.
- Do not simulate independent criticism in the current conversation.
- Do not assume named tools such as `subagent`, `dispatch_agent`, or `dispatch_team` exist.
- Parallelize only independent tasks. Concurrent writers need worktrees, sandboxes, copies, or explicit non-overlapping ownership.
- If faithful isolation is unavailable, stop and explain the limitation; offer the design-mode prompt instead.
- Never touch production systems, shared live data, publish externally, install software, or incur paid service costs without permission.

Create a project-local `.gauntlet/<goal-slug>/progress.md` from [assets/progress-template.md](assets/progress-template.md), unless the user or harness specifies another workspace. Keep candidate artifacts, critiques, comparisons, and evidence beside it. Follow the full [protocol](references/protocol.md).

## Harness portability

Read [references/harnesses.md](references/harnesses.md) when naming execution features.

In particular, `/loop` and `/effort ultracode` are Claude Code-specific concepts, not portable commands. For Pi, request fresh delegated agents and the maximum supported thinking level; Pi core does not include subagents or an autonomous loop scheduler. For any harness, use its actual available capability rather than inventing one.
