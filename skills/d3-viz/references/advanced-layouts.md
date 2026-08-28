# Advanced D3 Layouts

Read this for hierarchies, force networks, chords, matrices, and geographic visualization. Consult the installed D3 version and upstream API documentation for exact signatures.

## Shared preparation

- Define the data contract and stable IDs before running a layout.
- Clone data when the layout mutates nodes, links, or coordinates.
- Keep raw/domain data separate from layout/view-model data.
- Validate empty roots, missing parents/endpoints, cycles, duplicate IDs, negative weights, and disconnected components.
- Explain what position, area, angle, link width, and color mean.
- Add textual summaries or alternate tables/lists; complex SVG topology is rarely sufficient on its own.

## Hierarchies

Build with `d3.hierarchy`, `d3.stratify`, or `d3.stratify().path()` as appropriate.

- **Tree/dendrogram:** best when parent-child structure and paths matter.
- **Treemap:** compact part-to-whole comparison; labels disappear in small cells.
- **Partition/sunburst/icicle:** exposes depth and ancestry; angle is harder to compare than aligned length.
- **Pack:** useful for grouping, weaker for precise magnitude comparison.

Checks:

- Call `.sum()` only on values that should roll up; avoid double-counting pre-aggregated parents.
- Sort deliberately and consistently before layout.
- Preserve ancestor context during drill-down and provide a reset/breadcrumb.
- Ensure small or deep nodes remain discoverable outside pointer hover.

## Force networks

A force layout is an exploratory arrangement, not proof of clusters or importance.

- Explicitly define whether links are directed, weighted, or duplicated.
- Set link identity with stable IDs.
- Tune forces from data meaning and viewport, not arbitrary attractive output alone.
- Consider adjacency matrices for dense networks and trees for acyclic hierarchies.
- Offer search, filtering, neighborhood focus, and a readable details panel.
- Stop superseded simulations and avoid updating application state every tick.
- If pinning is supported, decide whether it persists and provide reset.

## Chord and flow diagrams

- Build and retain an index-to-label mapping; matrix order controls interpretation.
- Decide whether flows are directed. Do not mirror values unless the relationship is genuinely symmetric.
- Verify self-links, missing combinations, and aggregation rules.
- Use sorting, direct labels, and focused highlighting to reduce crossing complexity.
- For many entities, prefer a matrix or filtered view.
- Explain ribbon direction and width in the legend/description.

For source-to-target flows across stages, consider a Sankey-specific package compatible with the project rather than forcing a chord representation.

## Heatmaps and matrices

- Preserve explicit row/column ordering; alphabetical order is not always meaningful.
- Distinguish missing cells from zero.
- Use `scaleBand` for cells and a sequential/diverging color scale appropriate to the domain.
- Show a legend with units and thresholds.
- For large matrices, add labels on focus, sticky headers, aggregation, or zoom; consider canvas after profiling.
- If clustering rows/columns, expose that reordered state and the clustering rationale.

## Geography

- Confirm input geometry and coordinate reference system. GeoJSON consumed by `d3-geo` is normally longitude/latitude.
- Choose projection for the geographic extent and analytical goal; no projection preserves every property.
- Use `projection.fitExtent`/`fitSize` with actual geometry and account for legends/insets.
- Choropleths should usually encode normalized rates, not raw totals that mostly reflect population/area.
- Define how unmatched feature IDs, missing values, disputed regions, and out-of-bounds points behave.
- Use `geoPath` for SVG or canvas context rendering.
- Avoid treating a web tile map and a projected static map as interchangeable; follow any existing mapping stack.
- Attribute external geographic data as its license requires.

## Unique definitions

Clips, masks, gradients, filters, and marker IDs share document scope. Generate stable unique IDs per component instance and reference the same sanitized value from `url(#...)`. Global IDs such as `clip`, `gradient`, or `arrow` break when multiple charts render.

## Validation

- Compare aggregates and node/link counts against source data.
- Fix a random seed where deterministic visual regression matters and the API permits it.
- Test layout with smallest, largest, disconnected, duplicate, and malformed examples.
- Check labels at narrow widths and dense extremes.
- Verify keyboard/touch alternatives and reduced motion.
- Profile layout and rendering separately.
