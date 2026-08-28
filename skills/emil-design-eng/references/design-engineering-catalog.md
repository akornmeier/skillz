# Design engineering technique catalog

Focused implementation recipes retained from the pre-consolidation Emil skill. Load this file only when `apply` or `advise` mode needs detail beyond the canonical standards. Existing project conventions win. Treat values as starting points and verify behavior in the target browser.

## Contents

- [Craft posture](#craft-posture)
- [Component interaction recipes](#component-interaction-recipes)
- [Reveal and transform techniques](#reveal-and-transform-techniques)
- [Gesture and drag techniques](#gesture-and-drag-techniques)
- [Perceived performance](#perceived-performance)
- [Component product craft](#component-product-craft)
- [Debugging motion](#debugging-motion)
- [Quick review scan](#quick-review-scan)

## Craft posture

- Train taste by studying strong interfaces, reproducing interactions, and explaining why each detail helps.
- Invisible details compound: defaults, interruption, empty states, focus behavior, and failure handling matter more than decorative novelty.
- Beauty is useful when it improves trust, comprehension, or adoption. It is not permission to slow frequent work.
- Match the product's existing personality and tokens before introducing a new motion language.

## Component interaction recipes

### Press feedback

Use a subtle active state when frequency and product tone permit it:

```css
.button {
  transition: transform 160ms var(--ease-out);
}
.button:active {
  transform: scale(0.97);
}
```

Do not add visible scale to dense or keyboard-first controls without testing whether it distracts. Keep focus indication independent from press feedback.

### Trigger-anchored surfaces

Popover, menu, and tooltip motion should preserve the relationship to the trigger. Use the primitive's computed origin rather than hardcoding a guess. Centered modals remain centered.

### Repeated tooltips

A first tooltip may use a short intent delay. Once one toolbar tooltip is open, adjacent tooltips can appear immediately so scanning does not feel blocked. Confirm the component library's skip-delay behavior before custom implementation.

### Entering content

Prefer a near-final starting state over appearance from zero size. `@starting-style` can express CSS entry when target browser support is sufficient:

```css
.toast {
  opacity: 1;
  transform: translateY(0);
  transition: opacity 180ms var(--ease-out), transform 180ms var(--ease-out);

  @starting-style {
    opacity: 0;
    transform: translateY(8px);
  }
}
```

Use the framework's normal presence mechanism when exit animation or older-browser support requires it.

### Dynamic lists

Rapidly added or removed items need interruption-safe transitions and stable layout. Stagger only occasional group entrances; never delay access to controls while a stagger completes.

### Crossfades

First fix layout, timing, and opacity overlap. If two states still double-expose, a small temporary blur around `2px` can bridge the change. Profile filters on representative hardware and provide a reduced-motion alternative.

### Hold to confirm

A progress overlay can use `clip-path: inset()` while held and snap back quickly on release. The action still needs keyboard access, cancellation, clear labeling, and a non-motion state indicator.

## Reveal and transform techniques

- Translate percentages are relative to the element's own dimensions. `translateY(100%)` can hide a sheet by its own height without a measured pixel offset.
- `scale()` also scales descendants. That is useful for press feedback but can distort text or borders at larger ranges.
- Set `transform-origin` to the physical source of trigger-anchored motion.
- `clip-path: inset(top right bottom left)` supports directional reveals, comparison sliders, and progress masks. It is not automatically cheap; profile large or complex clips.
- A duplicated active layer clipped over an inactive layer can create seamless tab or segmented-control color transitions. Keep semantics in one interactive control and mark visual duplicates inert.
- Three-dimensional transforms need perspective, backface handling, and reduced-motion treatment. Use them for meaningful depth, not routine navigation.

## Gesture and drag techniques

1. Capture the pointer after drag intent is established.
2. Preserve the offset from the point where the user grabbed the element.
3. Track recent positions and timestamps for release velocity.
4. Ignore additional pointers unless multi-touch is an explicit feature.
5. Use a small intent threshold before committing direction.
6. Apply progressive resistance beyond boundaries rather than a hard stop.
7. Select the destination from both position and velocity.
8. Start settling from the live presentation value and pass velocity only when the chosen library supports it.
9. Keep input available while motion settles.
10. Test reversal, cancellation, slow drag, fast flick, and real touch hardware.

A velocity threshold such as `Math.abs(distance) / elapsedMs > 0.11` is only a starting hypothesis. Tune it with device evidence and pair it with distance, direction, and accessibility requirements.

## Perceived performance

- Immediate input acknowledgment often matters more than decorative loading motion.
- Skeletons and progress indicators should represent real state and avoid implying precision the system does not have.
- Faster spinner rotation can change perceived wait, but it does not fix latency. Measure actual completion time and avoid motion that increases cognitive load.
- Skip repeated tooltip delays and remove artificial transition waits from frequent workflows.
- Keep loading, success, warning, and error feedback causally attached to the action that produced it.

## Component product craft

### Defaults over option volume

Ship a coherent default before adding configuration. A component with one reliable install path, accessible markup, predictable interruption, and strong edge cases is more valuable than a large prop surface.

### Handle edge cases invisibly

Consider hidden-tab timers, pointer gaps, rapid repeated actions, content reflow, long labels, localization, reduced motion, touch hover, and failed media. Users should not need to understand the machinery.

### Naming and documentation

Use names that communicate purpose. Interactive documentation and copyable examples lower adoption cost, but examples must reflect current APIs and accessibility behavior.

### Cohesion

Easing, duration, spacing, sound, haptics, and visual treatment should feel like one product. A playful component can carry more bounce; a professional tool usually benefits from quieter motion.

## Debugging motion

- Inspect at normal speed first, then use slow motion to locate discontinuities.
- Step frame by frame when opacity, transform, blur, or color drift apart.
- Trigger actions repeatedly and reverse them mid-flight.
- Test keyboard, mouse, touch, reduced motion, zoom, and long content.
- Use a performance trace before claiming compositor behavior or frame-rate improvement.
- Review on representative hardware when gesture feel or filters matter.
- Record what was not tested.

## Quick review scan

| Check | Preferred response |
| --- | --- |
| `transition: all` | Name only intended properties. |
| Entrance from `scale(0)` | Start near final size with opacity when scale is appropriate. |
| Slow `ease-in` response | Use an existing responsive curve unless context justifies otherwise. |
| Triggered surface grows from center | Use the trigger-derived origin; keep modals centered. |
| Frequent or keyboard action waits on motion | Remove or reduce nonessential motion. |
| Rapid state uses restarting keyframes | Use a retargetable transition or verified spring. |
| Layout property animates every frame | Consider transform-based structure or measure the actual cost. |
| Movement ignores reduced motion | Provide a gentler state-preserving alternative. |
| Hover motion persists on touch | Gate hover-specific behavior by pointer capability. |
| Review claims smoothness without rendering | Mark visual and performance checks as not run. |
