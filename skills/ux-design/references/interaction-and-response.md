# Interaction and response

Use these principles for target acquisition, latency, flexible input, and perceived task duration. Pair them with accessibility standards and measured performance rather than treating memorable numbers as universal guarantees.

## Doherty Threshold

**Principle.** Fast feedback helps sustain the feeling of a continuous exchange between person and system. The often-cited 400 ms threshold is historical guidance, not a single target for every action or network condition.

**Use when:** interactions feel unresponsive, users double-submit, loading interrupts flow, or background work lacks status.

**Design moves:** acknowledge input immediately; update optimistically only when safe and reversible; show determinate progress when progress is knowable; preserve context during loading; prioritize real performance before decorative waiting treatments.

**Failure modes:** fake precision, dishonest progress, adding delay to manufacture perceived value, animation that blocks work, or masking severe latency instead of fixing it.

**Validate:** measure input-to-feedback and end-to-end completion on representative devices and networks; observe duplicate actions, abandonment, and recovery from failure.

Source: https://lawsofux.com/doherty-threshold/

## Fitts’s Law

**Principle.** Acquiring a target generally becomes easier as the target grows and its effective distance decreases.

**Use when:** controls are missed, dense toolbars cause errors, touch use is difficult, or primary actions are far from the work area.

**Design moves:** provide adequately sized hit areas; separate conflicting targets; enlarge the clickable region around icons without changing misleading visuals; place frequent actions near their context; support keyboard and alternative input.

**Failure modes:** measuring only the visible glyph; placing destructive actions too close to frequent actions; optimizing pointer distance while harming reading order or accessibility; assuming desktop hover behavior works on touch.

**Validate:** pointer, touch, keyboard, switch, zoom, one-handed mobile, and motor-impaired use; track mis-taps and correction time. Apply the product’s applicable target-size accessibility criterion independently.

Source: https://lawsofux.com/fittss-law/

## Parkinson’s Law

**Principle.** Work tends to expand to fill the available time; interfaces can also make simple tasks feel as long as the process permits.

**Use when:** forms, setup, booking, checkout, or administrative workflows contain avoidable steps and repeated entry.

**Design moves:** prefill known data with consent; support platform autofill; remove redundant confirmations; provide sensible constraints and clear completion expectations; allow users to skip nonessential work.

**Failure modes:** artificial countdowns; rushing decisions that require care; hiding optionality; optimizing speed at the expense of comprehension, consent, or error prevention.

**Validate:** compare active time, elapsed time, fields touched, errors, abandonment, and confidence against user expectations.

Source: https://lawsofux.com/parkinsons-law/

## Postel’s Law

**Principle.** Interfaces should tolerate reasonable variation in user input while producing clear, predictable output. In modern systems, tolerance must be bounded by security, data integrity, accessibility, and unambiguous meaning.

**Use when:** forms reject harmless formatting, imported data varies, users enter locale-specific values, or capabilities differ across devices.

**Design moves:** normalize safe variations; state constraints before submission; preserve the original input where relevant; validate at the right time; explain corrections; output canonical formats; fail safely when meaning is ambiguous.

**Failure modes:** silently guessing high-stakes values; accepting malformed or dangerous input; security vulnerabilities; lossy normalization; inconsistent interpretation between client and server.

**Validate:** boundary, locale, paste, autofill, assistive-technology, malformed, adversarial, and round-trip cases. Confirm server-side validation and clear recovery.

Source: https://lawsofux.com/postels-law/

## Combined checks

- Does every action receive timely, perceivable feedback without duplicate submission?
- Are hit areas usable across input methods and separated from destructive neighbors?
- Can users complete routine work without redundant entry or ceremony?
- Does flexible input preserve intent while enforcing security and integrity?
- Are loading, timeout, offline, partial-failure, and retry states explicitly designed?
