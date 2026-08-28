# Default Diagram Design Style Guide

This is the immutable bundled fallback. Never edit it for a project. Put persistent project tokens in `.pi/diagram-design/style-guide.md` as described by `onboarding.md`.

## Contents

- [Semantic tokens](#semantic-tokens)
- [Typography](#typography)
- [Geometry and spacing](#geometry-and-spacing)
- [Node treatments](#node-treatments)
- [Diagram rules](#diagram-rules)
- [Project override requirements](#project-override-requirements)

## Semantic tokens

| Role | Purpose | Light | Dark |
|---|---|---|---|
| `paper` | Page and default SVG background | `#f5f5f5` | `#2d3142` |
| `paper-2` | Optional framed surface | `#ececec` | `#393e53` |
| `ink` | Primary text and stroke | `#2d3142` | `#f5f5f5` |
| `muted` | Secondary text and arrows | `#4f5d75` | `#bfc0c0` |
| `soft` | Sublabels and boundaries | `#7a8399` | `#8e98ac` |
| `rule` | Hairline borders | `rgba(45,49,66,0.12)` | `rgba(245,245,245,0.12)` |
| `rule-solid` | Stronger borders | `#bfc0c0` | `rgba(191,192,192,0.25)` |
| `accent` | One or two focal elements | `#eb6c36` | `#f08a59` |
| `accent-tint` | Focal fill | `rgba(235,108,54,0.08)` | `rgba(240,138,89,0.10)` |
| `link` | HTTP, API, or external flow | `#2e5aa8` | `#6a95d8` |

Use semantic roles rather than copying hex values into instructions. One accent establishes hierarchy; multiple competing accents erase it.

## Typography

Use system stacks so output remains self-contained and works offline:

```css
--font-sans: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
--font-serif: ui-serif, Georgia, Cambria, "Times New Roman", serif;
--font-mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
```

| Role | Stack | Typical size | Usage |
|---|---|---:|---|
| Page title | serif | `1.75rem` | H1 only |
| Node name | sans | `12px` | Human-readable labels |
| Technical sublabel | mono | `9px` | Ports, URLs, commands, field types |
| Eyebrow or tag | mono | `8px` | Uppercase type or axis labels |
| Arrow label | mono | `8px` | Relationship annotations |
| Editorial callout | serif italic | `14px` | Optional asides |

Do not depend on a locally installed brand font for layout correctness. If a brand font is requested, keep a complete fallback stack and inspect wrapping with the fallback active.

## Geometry and spacing

Use a four-pixel grid for major coordinates, node dimensions, padding, and gaps. This is a consistency heuristic, not a mathematical requirement for every SVG value.

Documented exceptions:

- typography sized for legibility;
- stroke widths and opacity;
- small corner radii and marker geometry;
- curves, circles, and optical alignment corrections;
- pattern dimensions chosen to avoid visible repetition.

Prefer node padding of `8`, `12`, or `16`; major gaps of `20`, `24`, `32`, `40`, or `48`; and corner radii no larger than `8` unless a diagram grammar requires a terminal shape.

## Node treatments

| Type | Fill | Stroke |
|---|---|---|
| Focal, one or two maximum | `accent-tint` | `accent` |
| Backend, API, or step | `paper-2` | `ink` |
| Store or state | low-opacity `ink` | `muted` |
| External system | very-low-opacity `ink` | 30% `ink` |
| Input or user | low-opacity `muted` | `soft` |
| Optional or async | very-low-opacity `ink` | dashed 20% `ink` |
| Security boundary | low-opacity `accent` | dashed 50% `accent` |

Never rely on these treatments alone: keep visible labels and, where needed, distinct shapes or line patterns.

## Diagram rules

- Use clean paper by default; dotted texture is optional.
- Keep one reading direction and one dominant grammar.
- Draw arrows before nodes.
- Put an opaque paper-colored mask behind labels that cross lines.
- Place legends after the active node field with a separator.
- Use at most two focal accent elements.
- Avoid shadows, glow, decorative gradients, and generic equal-card grids.
- Split diagrams that exceed the selected type reference's complexity budget.

## Project override requirements

A project-local style guide must contain frontmatter with `schema: 1` and one of:

- `status: accepted-default`
- `status: customized`

It must define light and dark values for all semantic tokens plus complete sans, serif, and mono fallback stacks. Explicit tokens in the current request may override project values temporarily; do not persist them without a request.
