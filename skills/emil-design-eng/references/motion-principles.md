# Motion principles

## Rule types

Do not present every recommendation as a universal law. Label reasoning when it matters:

- **Accessibility requirement:** needed to preserve access or user preferences.
- **Measured technical constraint:** requires evidence from the target browser and workload.
- **House default:** safe starting value, adjustable to product context.
- **Craft preference:** aesthetic judgment, not a correctness claim.
- **Visual-test-dependent judgment:** must be checked in motion, not inferred from code alone.

## Decision gate

Ask in order:

1. **Frequency.** Remove motion from keyboard-driven or very frequent actions unless it provides essential state feedback. Keep frequent feedback near-imperceptible. Occasional surfaces can use standard motion. Rare moments can spend more of the delight budget.
2. **Purpose.** Accept feedback, spatial consistency, state indication, explanation, or prevention of a jarring change. Reject decoration that competes with repeated work or readable data.
3. **Speed.** Keep routine UI motion short enough that it never blocks input. Longer motion needs a rare or explanatory context.
4. **Function.** Motion must improve orientation, causality, or feedback. If it delays action or moves information being read, delete it.

"No animation" is a valid and often better result.

## Craft foundations

- Feedback begins with the input and remains continuous through direct manipulation.
- Enter and exit paths preserve spatial identity. Trigger-anchored surfaces originate at their trigger; viewport-centered modals remain centered.
- Gesture motion starts from the live presentation value, remains interruptible, and hands off release velocity when the implementation supports it.
- Deliberate user phases can be slower; system responses should resolve quickly.
- Motion language should match product personality. Crisp tools need less motion than playful consumer products.
- Good defaults and invisible edge-case handling matter more than configuration breadth.
- Prototype interaction and visuals together when static reasoning cannot answer the question.

## Accessibility and evidence

Reduced motion means a gentler equivalent, not automatically no feedback. Prefer opacity or color changes over large movement, parallax, elastic motion, or viewport-scale transitions. Check target-platform support for reduced-transparency and increased-contrast signals before relying on them.

Do not infer smoothness from API choice. CSS, WAAPI, JavaScript animation, `clip-path`, filters, and promoted layers all depend on property, browser, layer count, memory, and workload. Measure when performance is material.
