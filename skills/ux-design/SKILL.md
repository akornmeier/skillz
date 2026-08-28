---
name: ux-design
description: Applies psychology-informed UX principles to design and review interfaces, flows, forms, navigation, onboarding, dashboards, and product journeys. Use for UX critiques, interaction decisions, heuristic reviews, accessibility-aware recommendations, and diagnosing confusion, overload, or misleading behavior.
license: See LICENSES.md
compatibility: Designed for Pi and Agent Skills-compatible coding agents. Core use requires only file access; browser access is optional for reviewing a live product or checking sources.
metadata:
  category: design
  source: https://lawsofux.com/
  source-author: Jon Yablonski
  source-license: CC-BY-NC-ND-4.0
---

# UX Design

Use UX laws as **diagnostic lenses, not proof or commandments**. Observed user behavior, accessibility requirements, domain constraints, and product evidence outrank a named principle.

## Workflow

1. **Inspect the context.** Establish the intended users, task, device and input methods, environment, user familiarity, business constraints, accessibility needs, and available research or analytics. Inspect the real implementation and states when available.
2. **Frame the problem behaviorally.** Describe what users may fail to notice, understand, choose, remember, reach, recover from, or complete. Do not start by choosing a law.
3. **Route directly.** Use the reference routing below and load only the law groups relevant to the observed user problem.
4. **Choose a small set.** Usually 2–5 principles are enough. Name a law only when it materially explains the issue.
5. **Translate each law into a design move.** Tie it to a specific element, user action, expected benefit, tradeoff, and falsifiable validation method.
6. **Check conflicts.** Simplifying a novice flow may slow experts; adding emphasis may create noise; hiding choices may harm comparison; accepting flexible input may create ambiguity or security risk.
7. **Separate evidence levels.** Label findings as observed evidence, accessibility/platform requirement, research-informed principle, heuristic judgment, or hypothesis.
8. **Prioritize.** Rank by user harm, frequency, task criticality, confidence, and implementation cost—not by how many laws support the finding.

## Output format

For each material finding, report:

```text
Finding: [specific interface behavior]
User impact: [who is affected and how]
Principle: [one primary law; optional supporting law]
Rationale: [context-specific causal argument]
Recommendation: [smallest useful design change]
Tradeoff: [cost, conflict, or failure mode]
Validation: [method and observable success/failure signal]
Evidence level: [observed | requirement | research-informed | heuristic | hypothesis]
Source: [specific source URL when naming a law]
```

For implementation work, also include acceptance criteria and verify responsive, loading, empty, error, success, keyboard, touch, zoom, reduced-motion, and assistive-technology-relevant states.

## Non-negotiable rules

- Prefer measured behavior over appeals to authority. Never say a law “proves” a design decision.
- Do not invent users, research findings, conversion lifts, accessibility results, or certainty.
- Do not use “Miller’s 7±2” as a menu-item limit or treat the Doherty Threshold as a universal performance standard.
- Preserve necessary complexity; remove extraneous effort rather than merely hiding information.
- Prefer recognition over recall and put memory burden on the interface where practical.
- Keep familiar conventions unless evidence justifies retraining costs.
- Do not rely on color, motion, hover, or pointer precision alone.
- Never recommend deceptive defaults, manufactured urgency, obstruction, hidden costs, forced continuity, or other dark patterns.
- Treat accessibility as an independent requirement, not merely another UX preference.
- Make validation capable of disproving the recommendation.

## Reference routing

- Visual grouping, hierarchy, salience, or missed content: [perception-and-visual-hierarchy.md](references/perception-and-visual-hierarchy.md)
- Memory, attention, density, scanning, or recall: [memory-attention-and-load.md](references/memory-attention-and-load.md)
- Menus, options, defaults, prioritization, or decisions: [choice-and-decision-making.md](references/choice-and-decision-making.md)
- Targets, latency, forms, tolerance, or task time: [interaction-and-response.md](references/interaction-and-response.md)
- Progress, motivation, completion, interruption, or remembered journeys: [motivation-and-journeys.md](references/motivation-and-journeys.md)
- Conventions, onboarding, learnability, or irreducible complexity: [models-learning-and-complexity.md](references/models-learning-and-complexity.md)
- End-to-end critique: [review-checklist.md](references/review-checklist.md)
- Attribution and provenance: [sources.md](references/sources.md) and [LICENSES.md](LICENSES.md)

## Final quality gate

Before delivery, confirm that every named principle maps to a concrete issue; recommendations account for users and constraints; accessibility was checked directly; hypotheses are labeled; conflicts are visible; citations are traceable; and the proposed test could reveal that the advice was wrong.
