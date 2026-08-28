# Motion standards

Canonical defaults for build, review, and planning modes. Copy exact values into plans, then adapt only with a stated reason.

## Timing and easing

These are **house defaults**, not platform laws.

```css
--ease-out: cubic-bezier(0.23, 1, 0.32, 1);
--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);
--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);
```

- Enter or exit: strong `ease-out`.
- Existing on-screen element moving or morphing: `ease-in-out`.
- Hover or color: `ease`.
- Constant motion: `linear`.
- Avoid `ease-in` for responsive UI because it delays visible response.

| Element | Starting range |
| --- | --- |
| Press feedback | 100-160ms |
| Tooltip or small popover | 125-200ms |
| Dropdown or select | 150-250ms |
| Modal or drawer | 200-500ms |
| Marketing or explanation | Context-dependent |

Keep routine UI under 300ms. A modal or drawer may exceed that when distance and context justify it.

## Physicality and origin

- Entrance scale starts near the final size, usually `scale(0.9-0.97)` with `opacity: 0`, not `scale(0)`.
- Trigger-anchored surfaces use the component library's computed origin. Radix commonly exposes `var(--radix-popover-content-transform-origin)`; Base UI commonly exposes `var(--transform-origin)`. Confirm the exact primitive.
- Centered modals keep a centered origin.
- Pressable elements may use `scale(0.97)` with `transform 160ms var(--ease-out)` when frequency and product tone allow it.
- Group entrance stagger starts at 30-80ms between items and must not block interaction.

## Interruptibility and gestures

Prefer transitions for rapidly retargeted predetermined states and springs for direct manipulation when the spring implementation starts from the live value and carries velocity. Verify those behaviors in the chosen library.

Safe spring starting point:

```js
{ type: "spring", duration: 0.5, bounce: 0.2 }
```

Keep visible bounce around `0.1-0.3` and reserve it for momentum or playful contexts. For dismissal, consider both distance and release velocity. Existing family guidance used `Math.abs(distance) / elapsedMs > 0.11` as a starting threshold, which needs device testing.

Apply pointer capture after drag begins, ignore additional pointers, preserve grab offset, and use progressive resistance beyond boundaries instead of a hard stop.

## Performance

`transform` and `opacity` are the preferred default because browsers can often composite them without layout. This is a **strong default**, not a guarantee. Profile the target browser and workload.

Flag and investigate:

- `transition: all`;
- layout properties animated every frame;
- parent CSS variables updated every frame when they invalidate a large subtree;
- large blur/filter radii;
- unnecessary layers or `will-change` left active;
- requestAnimationFrame work that CSS or WAAPI could express more cheaply.

Do not claim all CSS or WAAPI animation is compositor-only. Do not claim a library shorthand is slow without checking its version, generated styles, and measured workload.

## Accessibility

```css
@media (prefers-reduced-motion: reduce) {
  .moving-surface {
    transform: none;
    transition: opacity 200ms ease;
  }
}

@media (hover: hover) and (pointer: fine) {
  .control:hover {
    transform: scale(1.02);
  }
}
```

Keep useful state feedback while removing vestibular movement, parallax, and elastic overshoot. Gate hover-only motion so touch does not retain false hover states. Test keyboard use, focus visibility, zoom, and contrast separately from motion preference.

## Verification

- Inspect at normal speed and slow motion. Slow motion finds discontinuities but does not replace normal-speed judgment.
- Spam reversible controls and interrupt gestures mid-flight.
- Toggle reduced motion in browser tooling.
- Test pointer gestures on representative real hardware when touch feel matters.
- Use a performance trace for frame or compositor claims.
- Record which checks ran. Unrun visual checks stay "not run."
