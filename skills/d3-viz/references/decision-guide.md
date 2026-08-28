# D3 Decision Guide

Read this when selecting a chart, rendering surface, scale, or axis behavior.

## Start with the question

| Analytical question | Good starting form | Important checks |
|---|---|---|
| Compare categories | Bar, dot, or lollipop chart | Start bars at zero; sort intentionally; use horizontal layout for long labels |
| Show change over time | Line, area, or small multiples | Parse dates once; expose gaps; do not imply interpolation that the data cannot support |
| Show distribution | Histogram, density, box/violin, ECDF | Document bins/bandwidth; show sample size and outliers where relevant |
| Show relationship | Scatter or connected scatter | Avoid overplotting; consider opacity, jitter, binning, or canvas |
| Show part-to-whole | Stacked bars or treemap | Prefer position/length over angle; use pie/donut only for a few large differences |
| Show hierarchy | Indented tree, node-link tree, treemap, partition | Decide whether structure or magnitude matters most |
| Show network | Node-link, adjacency matrix, chord | State whether links are directed/weighted; avoid hairballs |
| Show geography | Choropleth, symbols, density | Match projection and geographic units; normalize rates when appropriate |
| Show range around a midpoint | Diverging bars/heatmap | Use a meaningful center and symmetric treatment when comparison demands it |

Prefer the simplest conventional form that answers the question. Novel layouts increase explanation and accessibility costs.

## Rendering choice

Choose from measured requirements rather than a fixed mark threshold:

- **SVG:** semantic elements, sharp labels, CSS styling, and element-level events. Default for ordinary charts.
- **Canvas:** dense marks, frequent redraws, particle-like animation. Add a separate accessible representation and explicit hit testing.
- **Hybrid:** canvas marks plus SVG/HTML labels, axes, focus, and controls.
- **WebGL:** very large scenes or 3D; consider a specialized library before building this directly with D3 utilities.

Prototype with realistic data and profile interaction on target hardware before switching surfaces.

## Scale selection

| Data/encoding | Scale | Notes |
|---|---|---|
| Continuous position/length | `scaleLinear` | Use `.nice()` for display domains; clamp only when out-of-range data should map to an endpoint |
| Positive values over orders of magnitude | `scaleLog` | Domain must not cross zero; explain log axes |
| Signed values over orders of magnitude | `scaleSymlog` | Choose and document the constant around zero |
| Area or radius encoding | `scaleSqrt` | Radius must be square-root scaled for perceptual area |
| Local calendar dates | `scaleTime` | Local-time interpretation is intentional |
| Instants across time zones | `scaleUtc` | Prefer for server timestamps and cross-zone consistency |
| Ordered categories with width | `scaleBand` | Bars and matrix cells; inspect `bandwidth()` |
| Ordered categories without width | `scalePoint` | Dot and line positions |
| Named categories to style | `scaleOrdinal` | Supply explicit domain for stable color assignment |
| Continuous value to gradient | `scaleSequential` | Use a perceptually ordered interpolator |
| Values around a center | `scaleDiverging` | Domain is `[low, center, high]` |
| Continuous values into equal intervals | `scaleQuantize` | Thresholds derive from numeric extent |
| Distribution into equal-count buckets | `scaleQuantile` | Explain that thresholds depend on the observed sample |
| Domain-specific breaks | `scaleThreshold` | Expose thresholds in the legend |

### Domain rules

1. Validate values and remove/represent missing values before computing extents.
2. Guard empty and constant domains; `d3.extent([])` and collapsed domains need explicit behavior.
3. Include zero for bar lengths and other baseline-dependent encodings. Do not force zero for line/scatter position if it destroys useful resolution.
4. Add padding deliberately; avoid arbitrary constants disconnected from units.
5. Keep category order stable and meaningful.

## Axis and legend rules

- Format ticks with units and locale-aware project conventions.
- Keep tick density responsive; do not rotate every label by default.
- Use grid lines sparingly and behind marks.
- Label axes directly; do not depend on nearby prose.
- A color scale needs a visible legend unless labels make the mapping explicit.
- Legends for threshold/quantile scales must expose bins, not imply a continuous gradient.
- Verify generated IDs for gradients, clips, and masks are unique per chart instance.

## Color selection

- **Categorical:** use a tested discrete palette and limit category count; group or directly label when colors become hard to distinguish.
- **Sequential:** lightness should progress with magnitude.
- **Diverging:** reserve for a meaningful midpoint such as zero, target, or baseline.
- **Semantic:** reuse product tokens for success/warning/error only when their meanings match.
- Never encode critical meaning with color alone. Add position, shape, pattern, text, or direct labels.
