# Interaction and Performance

Read this for tooltips, zoom, brush, drag, transitions, simulations, canvas, and dense data.

## Tooltips

- Prefer a real HTML element associated with the focused/hovered mark.
- Set text with `.text()` or `textContent`. Do not pass untrusted labels to `.html()`.
- Show the same content on focus as on pointer hover; dismiss on blur and Escape when appropriate.
- Position relative to the chart/container when possible; account for scrolling and viewport edges.
- Use `pointer-events: none` for passive tooltips.
- Remove tooltip nodes and listeners on cleanup.
- For dense canvas plots, expose a focusable summary/table or a manageable set of interactive targets.

## Zoom and pan

Use separate layers:

```text
svg
├── defs (clip path)
├── axes
├── plot (translated by margins, clipped)
│   └── marks (zoom transform applies here)
└── controls/annotations
```

- Do not overwrite the margin transform while applying a zoom transform.
- For semantic zoom, rescale axes with `event.transform.rescaleX(x)` / `rescaleY(y)` and redraw marks.
- Restrict scale and translate extents intentionally.
- Filter gestures so wheel zoom does not trap normal page scrolling unexpectedly.
- Provide reset/fit controls and keyboard-accessible alternatives.
- Persist viewport state only if it is meaningful to the application.

## Brush and linked views

- Keep the brush's pixel selection separate from domain/application state.
- Convert through scale inverses, normalize bounds, and handle a cleared brush.
- In linked views, dispatch stable IDs or domain predicates rather than passing DOM nodes.
- Throttle expensive linked recomputation during continuous brush movement; commit final state on `end` when suitable.
- Provide non-drag controls for keyboard users.

## Drag and force simulation

- Clone node and link objects if callers expect immutable data; simulations assign coordinates and may replace link endpoints.
- Resolve link IDs explicitly with `forceLink(links).id(d => d.id)`.
- Raise/reheat on drag start, pin with `fx`/`fy`, then release or retain pinning according to product behavior.
- Stop the old simulation before replacing data or unmounting.
- Bound or collide nodes only when it supports interpretation; document forces that encode meaning.
- Networks become unreadable before they become computationally impossible. Filter, aggregate, cluster, search, or switch to a matrix rather than drawing a hairball.

## Transitions and reduced motion

- Animate changes that preserve object constancy; stable keys are essential.
- Interrupt stale transitions when new data arrives.
- Avoid long staggered sequences for large datasets.
- Respect `prefers-reduced-motion`; skip or shorten nonessential transitions.
- Do not animate axes and marks in ways that temporarily disagree about the scale.
- Never require animation to discover a value or state.

## Performance process

1. Measure with realistic maximum data, interactions, and target hardware.
2. Profile data transformation, layout, DOM count, paint, and event frequency separately.
3. Remove repeated parsing/sorting and unnecessary allocations from render loops.
4. Update only changed attributes and layers; avoid full teardown/redraw by default.
5. Coalesce high-frequency work with `requestAnimationFrame`; debounce completed resize work when appropriate.
6. Use spatial indexes (`quadtree`, Delaunay) for nearest-point hit testing instead of one listener per dense mark.
7. Simplify or aggregate data at the visible resolution.
8. Move to canvas/hybrid rendering only when measurements justify its accessibility and interaction cost.

## Canvas pattern

- Apply device-pixel-ratio scaling while keeping coordinates in CSS pixels.
- Clear and redraw deterministically from current state.
- Keep D3 scales/layouts; render with the 2D context.
- Implement hit testing with a spatial index or offscreen picking strategy.
- Overlay SVG/HTML for axes, labels, focus rings, and controls when useful.
- Provide an accessible equivalent because canvas pixels have no document semantics.

## Common failure modes

- **Marks escape the plot:** add a unique clip path and clip only the marks layer.
- **Zoom jumps:** margin and zoom transforms are being written to the same group.
- **Tooltip drifts:** page and container coordinate systems are mixed.
- **Duplicate charts/listeners:** setup runs repeatedly without symmetric cleanup.
- **Stale callbacks:** lifecycle dependencies omit state read by D3 handlers.
- **Janky resize:** observer callback changes the observed box or redraws more often than a frame.
- **Incorrect joins:** no stable key, duplicate keys, or the key changes with sorting.
- **Simulation leaks:** old simulations continue ticking after data changes/unmount.
