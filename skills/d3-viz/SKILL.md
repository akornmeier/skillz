---
name: d3-viz
description: Builds and reviews bespoke D3.js visualizations, including SVG or canvas charts, networks, hierarchies, maps, scales, zooming, brushing, and transitions. Use when a task mentions D3 or needs custom interactive visualization beyond a standard chart library.
compatibility: Requires the host project's JavaScript runtime and package manager. Follow its installed D3 version, framework, browser targets, and dependency conventions.
metadata:
  category: data-visualization
---

# D3 Visualization

Use D3 when the task needs custom visual encoding, layout, or interaction. Prefer an existing chart component for conventional charts when it already meets the product, accessibility, and performance requirements. Use raw SVG rather than D3 for static diagrams with no data-driven behavior.

## Workflow

1. **Inspect the project first.** Identify the framework, package manager, installed D3 version/modules, component conventions, styling system, test setup, and browser targets. Do not add a second D3 copy or replace the project's conventions without reason.
2. **Confirm the data contract.** Inspect representative data; define fields, types, units, null handling, stable keys, ordering, and whether relationships are directed. Parse and validate at the boundary rather than inside attribute callbacks.
3. **Choose the visual form.** State the analytical question and select the simplest encoding that answers it. Read [decision-guide.md](references/decision-guide.md) when choosing a chart, scale, or rendering surface.
4. **Choose DOM ownership.** In component frameworks, prefer framework-owned marks with D3 for calculations. Use D3-owned DOM only when complex joins, transitions, or behaviors justify it. Read [framework-integration.md](references/framework-integration.md).
5. **Implement in layers.** Keep data preparation, scales/layout, axes, marks, interaction, and presentation separable. Scope selections to the component root; never select or clear unrelated page elements.
6. **Add interaction deliberately.** Make hover behavior available to keyboard and touch users, keep app state outside D3, and clean up observers, simulations, listeners, and transitions. Read [interaction-performance.md](references/interaction-performance.md).
7. **Build accessibility in.** Give the visualization an accessible name and description, avoid color-only meaning, support reduced motion, and provide an equivalent summary or table when the SVG is too complex. Read [accessibility-colour.md](references/accessibility-colour.md).
8. **Verify behavior.** Run the repository's formatter, type checker, tests, and build. Exercise empty, one-point, null, duplicate, negative, extreme, and dense data; resize the container; test keyboard/touch use; and check light/dark themes if supported.

## Core decisions

### Rendering surface

- **SVG:** default for axes, labels, moderate mark counts, and element-level interaction.
- **Canvas:** use when measured DOM/rendering cost is unacceptable for dense marks or high-frequency updates.
- **Hybrid:** use canvas for marks and SVG/HTML for axes, labels, focus, and controls.
- **WebGL:** consider only for very large or 3D scenes where canvas is insufficient.

Do not rely on a universal mark-count cutoff. Measure with representative data and target hardware.

### Framework integration

- **Framework-owned DOM:** D3 computes scales, shapes, ticks, and layouts; the framework renders elements. This is the default for React, Vue, and Svelte.
- **D3-owned island:** D3 owns descendants of one dedicated `ref`/element. The framework owns the container and state. Never let both systems mutate the same descendants.
- Use stable data keys with `.data(data, key)` or framework keys.
- Prefer targeted joins over clearing and rebuilding the entire SVG.
- Use immutable copies before sorting or when layouts/simulations mutate input objects.

### Responsive layout

- Measure the container, not the window.
- Use `ResizeObserver` only when actual pixel dimensions drive layout; disconnect it on cleanup.
- Use an SVG `viewBox` plus fluid CSS for charts that can scale proportionally.
- Recompute ranges, axes, hit targets, and layout when dimensions change.
- Handle zero-width and hidden containers without creating invalid scale ranges.

## Non-negotiable quality rules

- Treat labels and tooltip content as untrusted. Prefer `textContent`/`.text()`; do not interpolate data into `.html()`.
- Derive domains from validated data. Include zero only when the encoding requires a meaningful baseline; do not force it for every line or scatter plot.
- Use `scaleSqrt` for circle radius when area represents magnitude.
- Use `scaleUtc` for instant-based cross-time-zone data; use `scaleTime` for local calendar time.
- Clip marks to the plot region when zooming or drawing beyond axes.
- Transform a dedicated marks layer during zoom; keep margins and UI layers separate.
- Stop force simulations, interrupt transitions, disconnect observers, and remove external tooltip nodes/listeners during cleanup.
- Respect `prefers-reduced-motion`; animation must not be required to understand the result.
- Keep interaction state serializable and owned by the application when other components depend on it.
- Prefer project theme tokens or CSS custom properties over hard-coded colors.

## Advanced layouts

For force networks, hierarchies, chords, geographic projections, and dense matrices, read [advanced-layouts.md](references/advanced-layouts.md) before implementing. These layouts often mutate data or encode assumptions that must be made explicit.

## Assets

Assets are starters, not framework-neutral drop-ins:

- [`assets/react-responsive-bar-chart.jsx`](assets/react-responsive-bar-chart.jsx) — accessible React + D3 bar chart with framework-owned structure and D3-owned marks layer.
- [`assets/vanilla-responsive-bar-chart.js`](assets/vanilla-responsive-bar-chart.js) — scoped vanilla D3 renderer with an explicit cleanup function.
- [`assets/sample-data.json`](assets/sample-data.json) — representative datasets for chart and layout testing.

Copy an asset only when it matches the target stack, then adapt imports, types, styles, labels, and data contracts to the project. Do not add dependencies or CDN scripts if the repository already has a dependency strategy.
