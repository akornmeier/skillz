# Framework Integration

Read this when implementing D3 in React, Vue, Svelte, or a lifecycle-managed component system.

## Contents

- [Pick one owner for each DOM subtree](#pick-one-owner-for-each-dom-subtree)
- [Lifecycle checklist](#lifecycle-checklist)
- [Responsive component pattern](#responsive-component-pattern)
- [Event boundaries](#event-boundaries)
- [Imports and dependencies](#imports-and-dependencies)
- [React notes](#react-notes)
- [Vue and Svelte notes](#vue-and-svelte-notes)

## Pick one owner for each DOM subtree

### Framework-owned marks (default)

Use D3 for pure calculations and render with the framework:

```javascript
const x = d3.scaleLinear(xDomain, [0, innerWidth]);
const y = d3.scaleLinear(yDomain, [innerHeight, 0]);
const path = d3.line().x(d => x(d.x)).y(d => y(d.y))(data);
// Render `path`, ticks, and marks with framework templates/JSX.
```

Prefer this when:

- marks map cleanly to component templates;
- application state controls selection and filtering;
- server rendering or framework transitions matter;
- the chart benefits from the project's component and accessibility primitives.

Memoize expensive layouts only after measuring. Scale constructors are usually cheap; force, contour, hierarchy, and geographic preprocessing may not be.

### D3-owned island

Let D3 own the descendants of one dedicated element when joins, transitions, axes, drag, brush, or zoom are substantially simpler imperatively:

```javascript
const root = d3.select(element);
root.selectAll("circle.mark")
  .data(data, d => d.id)
  .join(
    enter => enter.append("circle").attr("class", "mark"),
    update => update,
    exit => exit.remove(),
  )
  .attr("cx", d => x(d.x))
  .attr("cy", d => y(d.y));
```

The framework owns the element; D3 owns only its descendants. Do not render framework children into that same subtree.

## Lifecycle checklist

- Scope every selection to a passed element/ref; avoid `d3.select("svg")` or page-wide selectors.
- Use stable keys in D3 joins and framework loops.
- Separate one-time setup from updates when practical; avoid clearing the SVG on every state change.
- Cancel or replace in-flight transitions before starting incompatible ones.
- Cleanup must stop force simulations, interrupt transitions, remove behavior listeners, disconnect observers, and remove external tooltip/portal nodes created by the chart.
- Development strict modes may mount effects twice; setup and cleanup must be symmetric.
- Do not mutate props. Many D3 layouts and `forceSimulation` mutate nodes/links, so clone or build view-model objects first.
- Keep shared selection, filter, and viewport state in the application; D3 callbacks should dispatch semantic events.

## Responsive component pattern

1. Observe the chart container with `ResizeObserver` if pixel dimensions matter.
2. Store or pass the measured dimensions without creating a resize feedback loop.
3. Return no marks for zero or negative inner dimensions.
4. Recompute ranges and layout from dimensions.
5. Prefer `viewBox` and `width: 100%` when proportional scaling is sufficient.
6. Disconnect the observer during cleanup.

## Event boundaries

D3 v6+ passes `(event, datum)` to listeners. Convert low-level events to app-level intent:

```javascript
selection.on("click.chart", (event, datum) => {
  onSelect?.(datum.id);
});
```

- Namespace external D3 listeners so cleanup can target them.
- Do not store framework component instances or synthetic events in D3 data.
- Use pointer events rather than separate mouse/touch logic where possible.
- Prevent zoom/drag from swallowing normal page gestures unless the interaction requires it; provide visible reset controls.

## Imports and dependencies

Follow the existing project:

- If it uses `d3`, `import * as d3 from "d3"` is consistent.
- If it uses modular packages, import only those modules; do not add the umbrella package too.
- Use the repository's package manager and lockfile.
- Confirm installed D3 major version before copying examples; event signatures and APIs differ across old versions.
- Keep TypeScript datum types explicit. D3 generics can otherwise infer `unknown` or hide mutation.

## React notes

- Effects must return cleanup and include every reactive input actually read.
- Avoid calling React state setters on every simulation tick or pointer move. Let D3 update the isolated render layer or throttle semantic updates.
- `useId()` can seed unique, sanitized IDs for clips, masks, and gradients; do not use one global `#clip` across chart instances.
- For SSR, defer browser-only APIs (`ResizeObserver`, layout measurement) until mounted.

## Vue and Svelte notes

- Put D3-owned content under one bound element/action and clean it up in unmount/destroy hooks.
- Use reactive declarations/computed values for scale/layout calculations when framework ownership is practical.
- Avoid mixing template-rendered children with imperative D3 joins under the same group.
- When an action/composable receives updates, make updates idempotent and retain cleanup handles.
