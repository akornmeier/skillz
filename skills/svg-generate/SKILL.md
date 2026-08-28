---
name: svg-generate
description: Creates static, editable SVG diagrams such as flowcharts, architecture diagrams, decision trees, matrices, and risk maps. Use for deterministic non-data-driven diagrams; use D3 for interactive data visualizations and infographic-builder for sourced visual narratives.
compatibility: Requires file write access and Python 3 for bundled structural validation. Visual inspection requires an SVG-capable browser or renderer.
metadata:
  category: diagram-generation
---

# SVG Diagram Generation

Create raw, editable SVG without adding a rendering library. Follow the target project's design tokens and output conventions when present.

## Workflow

1. Determine the diagram's audience, question, output path, dimensions, and required labels.
2. Choose the simplest suitable structure: flow, tree, layered architecture, matrix, map, timeline, or relationship diagram.
3. Write SVG with:
   - a responsive `viewBox`;
   - non-empty `<title>` and `<desc>` elements;
   - semantic `<g>` groups with unique descriptive IDs;
   - selectable text and a system font stack;
   - explicit arrow markers and labeled connections;
   - project colors or CSS custom properties when available;
   - redundant labels or shapes when color carries meaning.
4. Save to the user-requested or project-appropriate `.svg` path. Do not assume a deliberation directory.
5. Validate structurally:

   ```bash
   python3 <skill-directory>/scripts/validate_svg.py <output.svg>
   ```

6. Render or open the SVG when supported. Inspect clipping, overlap, reading order, contrast, label size at delivery dimensions, and light/dark context where relevant.
7. Repair structural or visual failures and repeat validation before delivery.

## Diagram guidance

- **Decision matrix:** options as rows, criteria as columns, with text labels in addition to color.
- **Trade-off map:** labeled axes and points; use size only when it encodes a defined value.
- **Risk map:** label probability, impact, quadrants, and every plotted risk.
- **Flowchart:** use distinct process and decision shapes with labeled conditions.
- **Architecture diagram:** show boundaries, direction, protocols, and trust or ownership zones that matter to the question.

Use context-dependent spacing, typography, and palette rather than universal hard-coded styling. Keep decorative detail subordinate to comprehension.
