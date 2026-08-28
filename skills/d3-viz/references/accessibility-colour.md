# Accessibility and Color

Read this before shipping an interactive or color-encoded visualization.

## Accessible output

A chart needs an equivalent understanding, not merely an ARIA role.

- Give the chart a concise visible title when appropriate.
- Give the SVG/figure an accessible name and useful description; avoid duplicating surrounding prose.
- Summarize the key trend or conclusion in text.
- Provide a data table or downloadable data when users need exact values or when the visual structure is too complex for an equivalent SVG reading order.
- Hide decorative axes/grid lines from assistive technology when they create noise, but do not hide the only representation of data.
- Test with the project's supported screen reader/browser combinations where possible.

A common figure structure:

```html
<figure aria-labelledby="chart-title" aria-describedby="chart-summary">
  <h2 id="chart-title">Quarterly revenue</h2>
  <p id="chart-summary">Revenue increased in every quarter, from …</p>
  <svg role="img"><!-- chart --></svg>
  <!-- optional table/details -->
</figure>
```

Use unique IDs per chart instance.

## Keyboard and touch

- Any action available on click must be operable by keyboard.
- Keep focus order small and purposeful; hundreds of focusable SVG marks are usually unusable.
- Prefer roving focus, a list/table companion, or keyboard navigation among meaningful points.
- Show a visible focus indicator with sufficient contrast.
- Trigger tooltip/details on focus as well as hover.
- Provide controls for zoom, reset, filters, and brush ranges; do not require precision dragging.
- Ensure pointer targets are large enough and do not rely on hover on touch devices.
- Announce meaningful selection/filter changes with existing application patterns, not noisy updates for every pointer move.

## Motion

- Check `prefers-reduced-motion` and remove or shorten nonessential transitions.
- Avoid flashing, rapid looping, and large unprompted movement.
- Give users control over autoplaying or continuous animation.
- Preserve the final information state when animation is disabled.

## Color rules

1. Never use color as the only indicator of category, status, or selection.
2. Check text and essential graphical-object contrast against adjacent colors under the project's accessibility target.
3. Use a perceptually ordered sequential palette for magnitude.
4. Use a diverging palette only around a meaningful midpoint.
5. Keep categorical palettes small; direct-label, group, facet, or add shape/pattern when categories exceed reliable distinction.
6. Test simulated color-vision deficiencies, grayscale, light/dark themes, and selected/disabled states.
7. Prefer project CSS variables/tokens and verify their resolved contrast in every theme.
8. Keep missing/unknown values visibly distinct from zero and from the ends of a scale.

D3 palette families are not automatically accessible in every arrangement or background. Validate actual adjacent colors and mark sizes rather than trusting a palette name.

## Redundant encoding examples

- Line series: color + dash pattern + direct label.
- Scatter categories: color + symbol shape.
- Heatmap alerts: color + icon/text or outlined cells.
- Selection: color + stroke/size/annotation.
- Positive/negative: diverging color + position around a labeled zero baseline.

## Content safety

Data labels may come from users or external systems:

- Use `.text()` / `textContent`, not `.html()` with interpolation.
- If rich HTML is truly required, use the project's sanitization utility and an allowlist.
- Do not put sensitive raw records into SVG metadata, DOM attributes, debug logs, or downloadable tables.

## Verification checklist

- Navigate the entire interaction with keyboard only.
- Check visible focus and Escape/dismiss behavior.
- Verify touch interaction at narrow widths.
- Disable color or inspect in grayscale.
- Enable reduced motion.
- Zoom text/browser to the project's target level and resize the container.
- Inspect accessible name, description, and reading order.
- Confirm exact values are available without a precision pointer.
- Test empty, error, loading, and no-results states.
