# Apply motion

Use for implementation, tuning, and debugging. Source edits require user implementation intent.

## Workflow

1. Identify interaction, trigger, frequency, purpose, input methods, and current behavior.
2. Inspect existing tokens, component primitives, motion libraries, and reduced-motion conventions. Extend them instead of adding a parallel system.
3. Choose the smallest motion that passes the decision gate. Deletion is preferred when motion has no purpose or repeats constantly.
4. Define a verification gate before editing. Include one mechanical check and only the visual or device checks available in the environment.
5. Implement the smallest change. Preserve interruptibility, live-state continuity, origin, and input during transitions.
6. Run the focused mechanical check. Use browser evidence for feel, reduced motion, touch, or performance claims.
7. Report exact files changed, checks run, and checks not run.

## Common recipes

```css
/* Press feedback, when frequency and product tone permit it */
.button {
  transition: transform 160ms var(--ease-out);
}
.button:active {
  transform: scale(0.97);
}
```

```css
/* Entry without a mount effect */
.popover {
  opacity: 1;
  transform: scale(1);
  transform-origin: var(--radix-popover-content-transform-origin);
  transition: opacity 180ms var(--ease-out), transform 180ms var(--ease-out);

  @starting-style {
    opacity: 0;
    transform: scale(0.95);
  }
}
```

Use the primitive's real state attributes and origin variable. Keep centered modals centered.

For crossfades that visibly double-expose content, first fix timing and layout. A small temporary blur, around `2px`, may bridge the swap, but filters need browser testing and can cost paint or GPU time.

For gesture interactions, preserve pointer offset, capture the pointer, track a short velocity history, project momentum when choosing a snap point, and hand release velocity to the spring if the library supports it. Never lock input until an animation completes.

## Debugging

- Increase duration temporarily or use DevTools playback controls to find origin, easing, and coordination errors.
- Step frame by frame when two properties drift.
- Interrupt the animation repeatedly and reverse direction.
- Compare reduced-motion behavior with default behavior.
- Trace representative workload before making frame-rate or compositor claims.
