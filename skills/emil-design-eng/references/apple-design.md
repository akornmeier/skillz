# Apple-inspired fluid interface design

Guidance distilled from Apple design talks, chiefly *Designing Fluid Interfaces* (WWDC 2018), and translated to the web. Treat platform values and web-library mappings as starting points. Confirm current APIs, browser support, and behavior before implementation.

## Contents

- [Core model](#core-model)
- [Response and direct manipulation](#response-and-direct-manipulation)
- [Interruption and springs](#interruption-and-springs)
- [Velocity handoff and momentum](#velocity-handoff-and-momentum)
- [Boundaries and gesture intent](#boundaries-and-gesture-intent)
- [Spatial consistency](#spatial-consistency)
- [Materials and depth](#materials-and-depth)
- [Multimodal feedback](#multimodal-feedback)
- [Accessibility](#accessibility)
- [Typography](#typography)
- [Design foundations](#design-foundations)
- [Verification](#verification)

## Core model

A fluid interface responds with low latency, tracks direct input continuously, preserves momentum, and can be redirected without a visible jump. Motion is successful when it supports safety, understanding, achievement, or delight without delaying action.

Use the canonical motion standards for shared timing, easing, performance, and reduced-motion rules. This reference owns Apple-inspired gesture, material, typography, and design reasoning.

## Response and direct manipulation

- Acknowledge press or touch-down immediately, but commit the action at the appropriate semantic event.
- During drag, keep the surface aligned with the pointer rather than waiting for release.
- Preserve the offset where the user grabbed the element; do not snap its center to the pointer.
- Use pointer capture after drag intent is established so tracking continues outside the original hit area.
- Keep a short timestamped position history when release velocity matters.
- Do not lock input while a transition settles.

```js
el.addEventListener("pointerdown", event => {
  el.setPointerCapture(event.pointerId)
  const grabOffset = event.clientY - el.getBoundingClientRect().top
  // Track positions and timestamps after drag intent is established.
})
```

## Interruption and springs

Gesture-driven motion should start from the live presentation value and preserve continuity when the target changes. A spring can help only if the chosen implementation actually starts from the current value and carries velocity when retargeted.

Apple describes springs with damping ratio and response:

- Damping ratio near `1.0` settles without visible overshoot.
- A lower ratio permits oscillation.
- Response describes how quickly the spring approaches its target; it is not a fixed duration.

Values cited in the source material include:

| Interaction | Damping | Response |
| --- | ---: | ---: |
| Move or reposition | `1.0` | `0.4` |
| Rotation | `0.8` | `0.4` |
| Drawer or sheet | `0.8` | `0.3` |

Do not assume a web library's `bounce`, `duration`, stiffness, or damping fields map directly to those platform parameters. Check the installed library version and verify reversal behavior visually.

For two-dimensional direct manipulation, independent axis values may be easier to retarget and tune than a single scalar distance. Use the representation supported by the actual interaction and library.

## Velocity handoff and momentum

At release, settling motion should continue from the pointer's current velocity rather than visibly stopping and restarting. Libraries differ: some accept absolute pixels per second, others normalized or internal velocity. Verify units.

Some APIs normalize velocity by remaining distance:

```text
relativeVelocity = gestureVelocity / (targetValue - currentValue)
```

Guard zero or near-zero remaining distance and confirm the API expects this form.

Choose a destination using projected momentum when a flick should carry farther than the release point. Apple's sample uses exponential decay:

```js
function project(initialVelocity, decelerationRate = 0.998) {
  return (initialVelocity / 1000) * decelerationRate / (1 - decelerationRate)
}

const projected = currentPosition + project(releaseVelocity)
const target = nearestSnapPoint(projected)
```

Treat `0.998` as source-specific, not a universal web default. Tune with target-device evidence and apply bounds before selecting a snap point.

## Boundaries and gesture intent

- Apply progressive resistance beyond a boundary instead of a hard stop.
- Use a small movement threshold before committing a drag direction.
- Detect plausible gestures together, then cancel losing interpretations once intent is clear.
- Avoid a double-tap delay unless double tap is an actual product gesture.
- Ignore additional pointers unless multi-touch is intentional.
- Allow cancellation by reversing or leaving the target where the interaction model supports it.

A common rubber-band shape is:

```js
function rubberband(overshoot, dimension, constant = 0.55) {
  return (overshoot * dimension * constant) /
    (dimension + constant * Math.abs(overshoot))
}
```

The constant needs device and surface tuning.

## Spatial consistency

- Enter and exit along paths that preserve where a surface came from.
- Anchor menus, popovers, and sheets to their trigger or source.
- Keep viewport-centered modals centered.
- Intermediate motion should signal the destination rather than interpolate without spatial meaning.
- On reversal, avoid a velocity discontinuity. Retarget from the live state and verify the library's behavior.

## Materials and depth

Translucency can express a floating functional layer, but it is not automatically legible or performant.

- Use material weight to distinguish hierarchy.
- Avoid stacking low-contrast translucent surfaces when text legibility suffers.
- Pair modal focus with an appropriate scrim; keep parallel, non-blocking panels visually separate without falsely implying modality.
- Test `backdrop-filter`, blur, shadows, and animated filters on representative browsers and hardware.
- Provide a solid or higher-opacity fallback when reduced transparency or browser support requires it.
- Prefer semantic contrast and clear boundaries over attempts to imitate platform vibrancy exactly.

```css
.toolbar {
  background: rgb(255 255 255 / 60%);
  backdrop-filter: blur(20px) saturate(180%);
  border-top: 1px solid rgb(255 255 255 / 40%);
}
```

This is an example, not a default token set.

## Multimodal feedback

Combine visual, sound, and haptic feedback only when all three rules hold:

1. **Causality:** the user can identify the event that produced the feedback.
2. **Harmony:** channels feel synchronized on representative hardware.
3. **Utility:** feedback adds meaning rather than noise.

Reserve sound or haptics for meaningful commit, success, error, or snap events. Browser vibration, audio autoplay, and device support require capability checks and user-respectful fallbacks.

## Accessibility

- Replace large movement, parallax, elastic overshoot, and viewport-scale transitions under reduced motion while retaining useful state feedback.
- Check support before relying on reduced-transparency or increased-contrast media features.
- Preserve keyboard operation and visible focus independently from pointer motion.
- Test large text, zoom, localization, contrast over materials, and touch target behavior.
- Avoid synchronized brightness or motion effects that create discomfort.

```css
@media (prefers-reduced-motion: reduce) {
  .sheet {
    transform: none;
    transition: opacity 200ms ease;
  }
}
```

## Typography

- Adjust tracking by size: display text often tolerates tighter spacing, while small text may need more room.
- Adjust leading with size, script, density, and line length rather than applying one ratio everywhere.
- Build hierarchy from size, weight, spacing, and placement together.
- Prefer relative units so layout responds to user text size and zoom.
- Use optical sizing only when the selected font supports it.
- Start with the platform system stack when it meets the product's identity and language needs; custom type remains a product decision.

```css
:root { font: 100%/1.5 system-ui, sans-serif; }
.display {
  font-size: clamp(2rem, 5vw, 4rem);
  line-height: 1.05;
  letter-spacing: -0.02em;
  font-optical-sizing: auto;
}
```

## Design foundations

Use these questions when Apple-style detail risks becoming imitation rather than design:

- **Purpose:** What user need earns this feature or motion?
- **Agency:** Can the user interrupt, cancel, undo, or choose another path?
- **Responsibility:** Are privacy, safety, and failure consequences visible?
- **Familiarity:** Does the interaction preserve learned conventions unless evidence supports a change?
- **Flexibility:** Does it adapt to device, input, language, expertise, and ability?
- **Simplicity:** Is the common path clear without hiding necessary context?
- **Craft:** Are typography, spacing, motion, errors, and edge cases coherent?
- **Delight:** Does delight emerge from the whole experience rather than decoration?

## Verification

- Prototype interaction and visuals together when static reasoning is insufficient.
- Interrupt and reverse gestures repeatedly.
- Compare slow drag, fast flick, cancellation, and boundary resistance.
- Test real touch hardware when velocity or haptics matter.
- Toggle reduced motion and any supported transparency/contrast preferences.
- Trace filters and gesture work before making performance claims.
- Record exact library versions and checks run.
