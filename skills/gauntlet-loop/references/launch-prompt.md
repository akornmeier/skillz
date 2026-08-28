# Compact Launch Prompt

The prompt should feel like a destination plus a demanding operating rule, not a project plan. Preserve the mechanism and remove ceremony.

## Default shape

Adapt this; do not mechanically fill every bracket or retain empty sections.

```text
Build [GOAL], subject to [CONSTRAINTS]. Judge the real result against [BAR AND ACCESSIBLE REFERENCES] under equivalent conditions. [OPTIONAL OBJECTIVE GATES]. Use the highest reasoning effort this harness supports.

Lead the work yourself: choose the approach, then split it into the smallest useful pieces that can be improved and judged independently. Fan out fresh-context builders for independent work and separate fresh-context critics for every important piece; isolate concurrent writers. Do not let builders grade themselves. Critics must inspect the actual artifact without builder rationale or lead preference and compare it directly with the bar—anonymized under equivalent conditions when feasible—not a builder summary. Use A/B only for comparable alternatives and direct gates for correctness. When ours loses or evidence is insufficient, identify the largest verified material gap, repair it, and send the real result to a new critic. Continue only while a targeted pass can credibly close a material gap. A win requires all blocking gates and no unresolved material loss; otherwise stop on my request, a configured cap, blocked verification, or stalled progress, and report that state honestly.

Keep a simple live progress page or workbench showing the latest artifacts, comparisons, critiques, and verification evidence. After major parallel waves, use a fresh scope-preserving smoothing pass if the parts need coherence, then have another fresh critic inspect the integrated result.
```

## Compression rules

Keep:

- goal;
- concrete bar and where to find it;
- required constraints and objective gates;
- lead-chosen decomposition;
- separate fresh builders and critics;
- safe isolation for concurrent writers;
- inspection of primary artifacts without builder rationale or lead preference;
- blind/equivalent comparison only for comparable alternatives;
- largest verified-gap repair loop;
- success only after blocking gates pass with no material unresolved loss;
- non-arbitrary stopping with user/budget/block/stall safeguards;
- live progress artifact;
- optional smoothing followed by fresh review.

Cut:

- suggested architecture;
- a guessed list of components or workstreams;
- exact role count;
- fixed rounds, except a user-required count expressed only as a stop cap;
- motivational repetition such as “perfect” or “wow” when the concrete bar already carries the standard;
- long explanations of why independent review works;
- harness commands that are not known to exist.

## Harness wording

- **Claude Code:** “Use subagents and the highest supported effort level.” Mention `/loop` or `/effort ultracode` only if the user's installed version actually exposes those commands or the user explicitly requests that syntax.
- **Codex:** “Use isolated agents/workspaces and the highest supported reasoning effort available in this Codex environment.” Do not call that setting ultracode.
- **Pi:** “Use a loaded delegation capability that creates fresh ephemeral child contexts, and the maximum thinking level supported by the selected model.” Do not imply Pi core has `/loop`, ultracode, or built-in subagents.
- **Unknown harness:** “Use isolated subagents and the highest supported reasoning effort.”

Never weaken critic independence merely to name a preferred model. Capability matters more than branding.

## Examples

### Visual artifact

```text
Create [GOAL]. Compare equivalent rendered views directly with [REFERENCE SET], and require [ACCESSIBILITY/FUNCTIONAL GATES]. Use isolated subagents and the highest reasoning effort available.

Choose the implementation and split the artifact into the smallest pieces that can be improved and visually judged on their own. Give each important piece a fresh builder and a separate harsh fresh-context critic, isolating concurrent writers. Critics inspect the running result without builder rationale, at matched viewports, and compare it anonymously side by side with the references; they do not review builder summaries. If ours loses, close the largest verified visible or behavioral gap and send it to a new critic. Continue only while a credible material improvement remains; win only when all gates pass with no unresolved material loss, and otherwise stop honestly on my request, a configured cap, blocked verification, or stalled progress. Maintain a live workbench of screenshots, comparisons, and decisions, and smooth the integrated result between major waves when needed before fresh final review.
```

### Engineering artifact

```text
Build [GOAL] within [REPOSITORY/STACK CONSTRAINTS]. The bar is [REFERENCE IMPLEMENTATION OR SPEC] plus [TEST, LATENCY, RECOVERY, SECURITY, OR COMPATIBILITY GATES] run under equivalent conditions. Use fresh delegated agents and the highest supported reasoning effort.

Choose the design and decompose only along independently verifiable outcomes, isolating concurrent writers. Separate builders from fresh critics; critics receive no builder rationale or lead preference, inspect the actual diff and running behavior, execute the relevant checks, and compare evidence with the bar rather than trusting summaries. Return the largest verified material failure for a targeted repair, then use a new critic. Continue only while a credible improvement remains; win only when all blocking gates pass with no material unresolved loss, and otherwise stop honestly on my cancellation, a configured cap, blocked verification, or stalled progress. Keep a live progress workbench with candidates, command output, measurements, and unresolved risks; use a fresh integration pass only when parallel changes need coherence, then reverify.
```
