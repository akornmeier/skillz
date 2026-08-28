# Perception and visual hierarchy

Use these principles to explain grouping, salience, visual interpretation, and missed information. Visual order must remain understandable without color alone and under zoom, reflow, high contrast, and reduced motion.

## Contents

- [Aesthetic-Usability Effect](#aesthetic-usability-effect)
- [Law of Common Region](#law-of-common-region)
- [Law of Proximity](#law-of-proximity)
- [Law of Prägnanz](#law-of-prägnanz)
- [Law of Similarity](#law-of-similarity)
- [Law of Uniform Connectedness](#law-of-uniform-connectedness)
- [Selective Attention](#selective-attention)
- [Von Restorff Effect](#von-restorff-effect)
- [Combined checks](#combined-checks)

## Aesthetic-Usability Effect

**Principle.** Visual polish can improve perceived ease of use and tolerance for minor friction, but favorable impressions can also conceal real usability defects.

**Use when:** evaluating trust, first impressions, visual coherence, or a mismatch between satisfaction ratings and task performance.

**Design moves:** establish clear typography, spacing, alignment, feedback, and coherent styling; then verify actual task success separately. Include behavioral measures in usability tests rather than asking only whether an interface “felt easy.”

**Failure modes:** using beauty to excuse poor semantics, slow flows, inaccessible contrast, or weak error recovery; assuming aesthetic preference is universal across cultures or audiences.

**Validate:** compare task completion, errors, time, comprehension, and confidence—not just preference scores.

Source: https://lawsofux.com/aesthetic-usability-effect/

## Law of Common Region

**Principle.** Items enclosed by the same visible area tend to be interpreted as a group.

**Use when:** cards, panels, settings, tables, forms, or dashboard sections have unclear boundaries.

**Design moves:** use a restrained border, background, whitespace, or container label to define membership. Make nested regions visually weaker than their parent so hierarchy remains legible.

**Failure modes:** putting unrelated items in one card; creating excessive “card soup”; using containers that imply an interaction or relationship that does not exist.

**Validate:** ask users to identify which label, action, status, or help text belongs to which object without interacting.

Source: https://lawsofux.com/law-of-common-region/

## Law of Proximity

**Principle.** Nearness signals relationship; spacing is therefore semantic, not merely decorative.

**Use when:** labels detach from controls, help text appears attached to the wrong field, list items merge, or related actions feel scattered.

**Design moves:** keep intra-group spacing smaller than inter-group spacing; repeat the spacing rule consistently; preserve grouping at narrow widths and during localization.

**Failure modes:** equal spacing everywhere; compressing touch targets while tightening visual spacing; allowing responsive layouts to reorder items without their labels or actions.

**Validate:** run a quick grouping test at a glance and inspect all breakpoints, long translations, zoom, and error-message states.

Source: https://lawsofux.com/law-of-proximity/

## Law of Prägnanz

**Principle.** People tend to resolve ambiguous or complex visuals into the simplest coherent interpretation available.

**Use when:** icons, diagrams, data graphics, layout silhouettes, or overlapping layers admit multiple interpretations.

**Design moves:** simplify geometry, clarify figure versus ground, remove accidental shapes, and make the intended reading structurally dominant. Add labels when visual simplicity alone cannot make meaning reliable.

**Failure modes:** stripping away distinctions necessary for accuracy; assuming a minimalist icon is self-explanatory; treating “simple-looking” as “simple to use.”

**Validate:** ask representative users what they see and what they expect to happen before explaining it; check monochrome and low-vision views.

Source: https://lawsofux.com/law-of-pr%C3%A4gnanz/

## Law of Similarity

**Principle.** Elements that share appearance are likely to be interpreted as related or equivalent.

**Use when:** users confuse interactive and static text, primary and secondary actions, statuses, categories, or repeated components.

**Design moves:** make same-function controls visually consistent; reserve distinctive styles for meaningful differences; combine color with text, shape, iconography, or position.

**Failure modes:** styling unlike actions identically; making a non-link look like a link; introducing one-off variants that erode a design system; using color as the only distinction.

**Validate:** inventory component variants and ask users to predict which elements behave alike before interaction.

Source: https://lawsofux.com/law-of-similarity/

## Law of Uniform Connectedness

**Principle.** A visible connection—line, path, frame, or shared shape—can communicate a stronger relationship than proximity alone.

**Use when:** showing sequences, dependencies, parent-child relationships, selected ranges, or linked nodes.

**Design moves:** connect only genuinely related items; use direction markers and labels where sequence or causality matters; ensure the relationship survives responsive reflow.

**Failure modes:** decorative lines that imply workflow or causality; tangled connectors; relying on a subtle line that disappears in high-contrast mode.

**Validate:** ask users to describe the relationship and direction; inspect at narrow width, 200% zoom, and forced-colors settings.

Source: https://lawsofux.com/law-of-uniform-connectedness/

## Selective Attention

**Principle.** People allocate limited attention according to their current goal and may filter out content that appears irrelevant, ad-like, or weakly signaled.

**Use when:** users miss banners, state changes, validation, secondary actions, or updates that happen amid competing motion and content.

**Design moves:** align important information with the active task; reduce competing salience; place feedback near its cause; use persistent state changes or explicit announcements when a transient cue could be missed.

**Failure modes:** banner-shaped essential content; multiple simultaneous animations; off-screen toasts; assuming visibility means notice; forcing attention with disruptive motion.

**Validate:** task-based testing, eye-tracking only when warranted, delayed recall, and checks for change blindness. Verify screen-reader announcements and reduced-motion behavior separately.

Source: https://lawsofux.com/selective-attention/

## Von Restorff Effect

**Principle.** An item that differs from otherwise similar peers is more likely to attract attention and be remembered.

**Use when:** emphasizing one primary action, exception, warning, selected item, or recommended path.

**Design moves:** create one meaningful contrast in hierarchy, shape, label, weight, or position; pair visual salience with explicit text and semantics.

**Failure modes:** emphasizing everything; making critical content resemble advertising; using motion or color alone; highlighting a business-preferred option in a manipulative way.

**Validate:** five-second recall, first-action observation, comprehension of why the item differs, color-vision simulation, and reduced-motion testing.

Source: https://lawsofux.com/von-restorff-effect/

## Combined checks

- Can users infer groups without reading every label?
- Is the visual hierarchy still correct when color and motion are removed?
- Does one element dominate for a defensible user reason?
- Do nearby, similar, enclosed, and connected cues agree rather than contradict each other?
- Can a user notice state changes while focused on the primary task?
