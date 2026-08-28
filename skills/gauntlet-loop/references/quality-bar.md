# Choosing an Inspectable Quality Bar

A quality bar must let a fresh critic answer, from primary evidence, “Does this candidate meet or beat the standard?”

## Selection order

1. **User-supplied exemplar plus hard requirements** — strongest when the exemplar represents the desired outcome and is legally and technically inspectable.
2. **Several best-in-category exemplars** — useful when one example has accidental quirks that should not become requirements.
3. **Objective threshold** — tests, latency/error budgets, recovery drills, accessibility checks, security properties, factuality checks, or another reproducible measurement.
4. **Reference implementation or accepted corpus** — compare behavior, maintainability, clarity, or output under equivalent conditions.
5. **Proposed bar** — when none was supplied, name a real comparator or measurement and explain why it predicts success.

Use both exemplars and objective gates when one cannot cover the whole goal. A beautiful reference cannot establish correctness; a passing test suite cannot establish visual quality.

## Bar test

Reject or refine a proposed bar unless all are true:

- **Relevant:** it represents the user's desired outcome rather than mere prestige.
- **Accessible:** the critic can open, run, render, measure, or otherwise inspect it.
- **Comparable:** candidate and reference can be evaluated on equivalent inputs and conditions.
- **Observable:** the judgment can cite visible behavior, text, pixels, measurements, or test evidence.
- **Stable enough:** it will not silently change between rounds, or changes can be recorded.
- **Safe and lawful:** using it does not require unauthorized access, disclosure, or copying protected expression.

Aspirational bars may be unreachable. They are still useful for direction, but the launch prompt must not turn “beats the exemplar” into a false correctness claim. Use references to judge qualities and outcomes—not as permission to copy protected expression, branding, or a living creator's distinctive voice.

## Write the one-sentence bar

Use:

> Judge the actual **[candidate artifact]** against **[specific reference or threshold]** under **[equivalent conditions]**, because it provides inspectable evidence of **[qualities that matter]**.

Examples:

- **Visual product:** Compare equivalent desktop and mobile flows side by side with the supplied best-in-category screenshots, while separately requiring keyboard and contrast checks.
- **Writing:** Compare each finished section with the supplied reference passages for clarity and information density, then verify factual claims against cited primary sources.
- **Backend:** Require the candidate to pass the supplied conformance and failure-recovery suite and meet the stated p95 latency and error-rate thresholds under the same load profile.
- **Developer tool:** Run candidate and reference on the same representative tasks, then compare correctness, time-to-completion, error recovery, and usability evidence.
- **Unknown domain:** Find two or three respected, directly inspectable examples and define one reproducible task or measurement that exposes the qualities the goal depends on.

## Build criteria without over-prescribing the route

The launch prompt may summarize a small set of gates, but should not dictate implementation. Classify criteria as:

- **Blocking:** required for a defensible win.
- **Material:** a meaningful gap against the reference.
- **Polish:** useful only after blockers and material gaps are resolved.

For each criterion, the running lead should record:

| Field | Meaning |
| --- | --- |
| Requirement | Observable outcome, not an adjective |
| Inspection | How a critic will inspect it |
| Pass evidence | What would prove it passed |
| Status | Unknown, pass, fail, blocked, or not applicable |
| Evidence | Artifact path, screenshot, command output, or measurement |

Do not change criteria after seeing candidates merely to favor one. If new evidence justifies a change, record the reason before the next judgment.

## Fair comparisons

Blind A/B is appropriate only when alternatives target the same outcome and can be presented under equivalent conditions.

- Label candidates A/B without author, model, branch, timestamp, or chronology.
- Normalize viewport, inputs, test fixtures, instructions, and evidence packaging.
- Preserve real quality differences; do not normalize away the thing being judged.
- Ask for a winner, tie, neither, confidence, criterion-level evidence, and the largest decisive gap.
- Treat a tie, inaccessible artifact, or insufficient evidence as “not yet a win.”

Do not force A/B for complementary components, incomparable scopes, or security/correctness claims that require direct verification rather than preference judging.
