# UX review checklist

Use this for a full interface or flow review. Do not claim a check passed unless the relevant state or implementation was actually inspected.

## Contents

- [1. Context and evidence](#1-context-and-evidence)
- [2. Information and visual structure](#2-information-and-visual-structure)
- [3. Comprehension, memory, and decisions](#3-comprehension-memory-and-decisions)
- [4. Interaction and system status](#4-interaction-and-system-status)
- [5. Learning and complexity](#5-learning-and-complexity)
- [6. Journey and ethics](#6-journey-and-ethics)
- [7. States to inspect](#7-states-to-inspect)
- [8. Prioritization](#8-prioritization)
- [9. Validation plan](#9-validation-plan)

## 1. Context and evidence

- [ ] Primary users, goals, device/input, environment, and familiarity are identified.
- [ ] Available analytics, research, support issues, and constraints are separated from assumptions.
- [ ] Critical, frequent, low-frequency/high-harm, and expert tasks are distinguished.
- [ ] Accessibility, privacy, safety, security, localization, and regulatory requirements are recorded independently of UX heuristics.

## 2. Information and visual structure

- [ ] Page purpose and primary action are apparent without reading every element.
- [ ] Proximity, similarity, containers, and connections communicate the same grouping.
- [ ] Headings, labels, and reading order remain meaningful at narrow widths and zoom.
- [ ] Important content is not banner-like, off-screen, transient, or competing with excessive salience.
- [ ] Color, shape, motion, and position are not the sole carriers of meaning.
- [ ] Polished appearance is not being used as evidence of actual usability.

Relevant laws: Common Region, Proximity, Prägnanz, Similarity, Uniform Connectedness, Selective Attention, Von Restorff, Aesthetic-Usability.

## 3. Comprehension, memory, and decisions

- [ ] Content is chunked by user goal with clear labels.
- [ ] Users do not need to remember values, constraints, or choices from another screen.
- [ ] Necessary comparisons are visible side by side or otherwise externalized.
- [ ] Options are relevant and differentiated; filters/search preserve broad access where needed.
- [ ] Defaults and recommendations are explicit, explainable, reversible, and user-serving.
- [ ] Simplification has not removed context, informed consent, safeguards, or expert capability.

Relevant laws: Chunking, Cognitive Load, Miller’s Law, Working Memory, Serial Position, Choice Overload, Hick’s Law, Cognitive Bias, Occam’s Razor.

## 4. Interaction and system status

- [ ] Controls have clear affordances, names, states, and adequately sized hit areas.
- [ ] Keyboard order follows visual/logical order; focus is visible and not obscured.
- [ ] Touch, pointer, keyboard, zoom, and assistive-technology-relevant paths work.
- [ ] Every action receives timely, perceivable feedback and prevents accidental duplicate submission.
- [ ] Loading, timeout, offline, retry, partial failure, empty, and success states preserve context.
- [ ] Forms state constraints early, accept safe variation, preserve input, and explain recovery.
- [ ] Destructive or irreversible actions are separated, explicit, and recoverable where possible.

Relevant laws: Fitts’s Law, Doherty Threshold, Postel’s Law, Parkinson’s Law.

## 5. Learning and complexity

- [ ] Familiar controls behave according to platform and domain conventions.
- [ ] Product terminology and conceptual structure match researched user models.
- [ ] A new user can reach a safe, meaningful first outcome without a mandatory tour.
- [ ] Contextual help appears at the moment of need and remains searchable later.
- [ ] Automation and defaults reveal assumptions and support override.
- [ ] Complexity removed from the screen has not simply moved to memory, support, operations, or recovery.

Relevant laws: Jakob’s Law, Mental Model, Paradox of the Active User, Tesler’s Law.

## 6. Journey and ethics

- [ ] Progress is truthful and tells users what remains.
- [ ] Users can pause, save, resume, skip optional work, or abandon without coercion.
- [ ] High-anxiety moments and endings clearly communicate outcome and next steps.
- [ ] Interruptions, prompts, urgency, defaults, and salience advance the user’s chosen goal.
- [ ] Cancellation, refusal, privacy, and error paths are not intentionally worse than acceptance paths.
- [ ] Engagement patterns do not exploit completion tension, cognitive bias, or compulsion.

Relevant laws: Flow, Goal-Gradient Effect, Peak-End Rule, Zeigarnik Effect, Cognitive Bias.

## 7. States to inspect

At minimum inspect, where applicable:

- default, hover, focus, active, selected, disabled;
- first use, returning use, novice, expert;
- empty, sparse, typical, dense, long content, localization;
- loading, slow network, offline, timeout, partial and total failure;
- validation before/after submit, corrected input, duplicate submit;
- success, cancellation, back navigation, refresh, interrupted/resumed;
- narrow/wide viewport, 200%+ zoom, text enlargement;
- keyboard-only, touch, reduced motion, high contrast/forced colors, screen-reader semantics.

## 8. Prioritization

Score each finding qualitatively:

- **Impact:** blocker / major / moderate / minor
- **Reach:** all / common segment / limited segment / edge case
- **Frequency:** every task / recurring / occasional / rare
- **Confidence:** observed / strong evidence / plausible / speculative
- **Effort:** small / medium / large / unknown

Prioritize blockers, irreversible harm, exclusion, and frequent critical-path failures. Never demote an accessibility or safety defect merely because the affected segment is smaller.

## 9. Validation plan

For each recommendation specify:

1. representative participants or production segment;
2. realistic task and context;
3. current baseline;
4. observable success and guardrail metrics;
5. disconfirming result that would reverse the recommendation;
6. accessibility and segment-level checks;
7. follow-up after novelty wears off when relevant.

Avoid validating only preference. Include task success, errors, comprehension, recovery, confidence, and unintended consequences.
