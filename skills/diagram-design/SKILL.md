---
name: diagram-design
description: Creates polished technical and product diagrams as standalone HTML with embedded CSS and inline SVG. Use for architecture, flowchart, sequence, state, ER, timeline, swimlane, quadrant, nested, tree, layer, Venn, and pyramid diagrams that need editorial page treatment. Use svg-generate for raw SVG, d3-viz for data-driven or interactive graphics, and infographic-builder for sourced visual narratives.
license: See LICENSE
compatibility: Requires file write access and Python 3 for bundled validation. Browser rendering is recommended for visual review. Website-based style onboarding requires network access and user approval.
metadata:
  category: diagram-generation
  output: standalone-html
  version: "1.1"
---

# Diagram Design

Create one standalone HTML document with embedded CSS and inline SVG.

## Boundaries

Use this skill when the deliverable is an editorial HTML page containing a static technical or product diagram.

Use another skill when:

- raw editable `.svg` is the main deliverable: use `svg-generate`;
- marks derive from data, scales, simulation, zoom, brushing, or runtime interaction: use `d3-viz`;
- claims, statistics, citations, evidence ledgers, or visual storytelling drive the artifact: use `infographic-builder`;
- a table, paragraph, or short text diagram communicates the idea better: do not create a graphical diagram.

Do not add D3, chart libraries, web fonts, CDN assets, or runtime dependencies.

## Select one diagram type

| Content | Type and reference |
|---|---|
| System components and connections | [Architecture](references/type-architecture.md) |
| Decisions and branches | [Flowchart](references/type-flowchart.md) |
| Ordered messages between actors | [Sequence](references/type-sequence.md) |
| States, events, and guards | [State](references/type-state.md) |
| Entities, fields, and relationships | [ER](references/type-er.md) |
| Events placed in time | [Timeline](references/type-timeline.md) |
| Process ownership and handoffs | [Swimlane](references/type-swimlane.md) |
| Two-axis positioning | [Quadrant](references/type-quadrant.md) |
| Containment or scope | [Nested](references/type-nested.md) |
| Parent-child hierarchy | [Tree](references/type-tree.md) |
| Stacked abstraction levels | [Layers](references/type-layers.md) |
| Set overlap | [Venn](references/type-venn.md) |
| Rank, hierarchy, or drop-off | [Pyramid](references/type-pyramid.md) |

Load only the selected type reference. Load [annotation](references/primitive-annotation.md) or [sketchy](references/primitive-sketchy.md) guidance only when requested.

## Resolve the style guide

Bundled defaults are read-only: [references/default-style-guide.md](references/default-style-guide.md).

Project customization belongs at:

```text
.pi/diagram-design/style-guide.md
```

Apply style inputs in this order:

1. explicit tokens supplied for the current request;
2. project-local `.pi/diagram-design/style-guide.md`;
3. bundled defaults.

Current-request overrides are temporary unless the user asks to save them. If the project-local file does not exist, follow [references/onboarding.md](references/onboarding.md). Ask whether to derive tokens from an approved website, accept pasted tokens, or adopt bundled defaults. Write only the project-local file; never edit this skill package.

## Build workflow

1. Confirm audience, message, output path, theme, and required labels.
2. Select one diagram type and read only its reference.
3. Resolve the style source and copy the nearest light, dark, or full template from `assets/`.
4. Replace every template token; remove unused placeholders and elements.
5. Use one reading direction and split content that exceeds the selected type's complexity budget.
6. Draw connections before nodes; mask labels crossing lines; keep legends outside the node field.
7. Add accessible HTML and SVG descriptions.
8. Validate, repair, and rerun until structural checks pass.
9. Render at intended dimensions when browser capability exists; inspect text fit, clipping, overlap, contrast, and reading order.

Inspect or copy only the selected template and type example. Do not load all variants.

## Output contract

The result must include:

- doctype, language, charset, viewport, meaningful page title, one `<main>`, and one non-empty `<h1>`;
- embedded CSS, system font stacks, and no network-loaded resources;
- exactly one inline SVG with a finite positive `viewBox`;
- SVG `role="img"`, `aria-labelledby`, non-empty `<title>` and `<desc>`, unique IDs, and resolvable local references;
- selectable text and redundant labels or shapes when color carries meaning;
- no more than two focal accent elements;
- no shadows, glow, decorative gradients, oversized rounding, or color-only status;
- a prose summary when the SVG description cannot concisely explain a complex diagram.

Use enough padding for system-font metric differences. The layout grid guides major geometry and spacing; typography, stroke widths, small radii, and optical corrections may use documented exceptions.

## Accessibility pattern

```html
<svg viewBox="0 0 1000 600" role="img"
     aria-labelledby="diagram-title diagram-desc"
     xmlns="http://www.w3.org/2000/svg">
  <title id="diagram-title">Request processing architecture</title>
  <desc id="diagram-desc">Requests pass from the browser through the API to storage.</desc>
  <!-- diagram -->
</svg>
```

Keep the title concise. Describe reading order, major relationships, and conclusion rather than every decorative shape.

## Validation

Validate a generated diagram:

```bash
python3 <skill-directory>/scripts/validate_diagram.py output.html --strict
```

Validate the bundled inventory:

```bash
python3 <skill-directory>/scripts/validate_diagram.py --package <skill-directory>/assets --strict
```

Structural validation cannot prove good layout, text fit, contrast, reading order, or assistive-technology behavior. Report only visual checks actually performed.

## Delivery

Report the output path, selected type, style-guide source, validator command and result, visual checks performed, and remaining manual-review risks.
