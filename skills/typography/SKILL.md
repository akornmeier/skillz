---
name: typography
description: Sets and reviews typography for web pages, apps, and print, covering typeface choice and pairing, web font loading, type scales and fluid sizes, line length, line height and vertical rhythm, OpenType and variable fonts, link underlines, text wrapping, text contrast, dark-mode text, and print or PDF typesetting (page margins, grids, justification, CMYK black, bleed, PDF/X, print stylesheets). Use when writing or reviewing CSS that styles text, choosing or loading fonts, building a type scale, fixing text that is hard to read, or preparing a document for print or PDF. Works alongside ui-rules, which owns spacing, color, mobile, and dashboard rules for whole screens.
license: See LICENSES.md
---

# Typography

Set type that reads well, or review type that doesn't. On screens, apply the rules below. For print, PDF, or a print stylesheet, read [references/print.md](references/print.md) first. Fix what fails, then show the work. In a review-only task, report violations instead of editing.

## How to apply

1. Rules marked (default) are starting points. Break one when the design needs it, and say which rule and why in one line. Unmarked rules are firm: fix every violation, or report it in a review-only task.
2. The user's explicit instruction or the project's design system outranks a (default) rule, not a firm one; flag the conflict instead of shipping it silently. When ui-rules also applies, follow both; where they disagree, follow ui-rules and say so.
3. Measure where a rule gives a number. Compute contrast from the actual colors. Estimate characters per line as column width ÷ (font size × 0.45), or count a rendered line when a browser is available. If you could not check a rule (no rendered page, unknown font metrics), say so; never report an unchecked rule as passing.
4. For a new stylesheet or a base-style rewrite, start from [templates/typography.css](templates/typography.css), which applies every web rule below.
5. When you show the work, list only exceptions: (default) rules broken on purpose, conflicts, and rules you could not check.

## Web rules

### Fonts

- Choose the body face first, then pair any other face against it by role. Use each face where it was designed to work: display cuts for headings, text cuts for body.
- System stack (`system-ui, sans-serif`) for interfaces, dashboards, and tools; a custom face for editorial or brand work. (default)
- Serve `woff2` only, subset to the characters you need, and put every weight and style under one `font-family` name.
- Declare the italic `@font-face` separately. Without it, browsers fake italics by slanting the upright.
- Prefer the variable version of a family: one `@font-face` with `font-weight: 200 900` covers every weight. Set weights with `font-weight` (any number, such as 450); use `font-variation-settings` only for custom axes. (default)
- `font-display: swap` for body and heading faces, `optional` for decorative ones. Never `block` unless the face is the content.
- Preload at most the one or two faces visible on first paint, with `as="font" type="font/woff2" crossorigin`. The `crossorigin` is required even for self-hosted files.
- Add a fallback `@font-face` with `size-adjust` and ascent/descent overrides so the swap barely shifts the layout. (default)
- Keep kerning and standard and contextual ligatures on, using `font-kerning` and `font-variant-ligatures` rather than `font-feature-settings`. Set `font-optical-sizing: auto`. Turn ligatures off in code.

### Size and measure

- Leave the root at `font-size: 100%`; never set it in px. Size text in `rem` or `em`; write media queries in `em`.
- Derive sizes from one modular scale (a ratio such as 1.2–1.333), then make them fluid with `clamp()`. (default)
- Every `clamp()` minimum and maximum is in `rem`, and the middle value includes a `rem` term (`1.6rem + 2.4vw`). Never size text in viewport units alone.
- Body text 45–75 characters per line, about 66 ideal. Multi-column text 40–50 per column; captions and UI text 35–50. (default)
- Set the measure in `em`: `max-width: 30em` on the text column holds about 66 characters in most text faces. Avoid `65ch`: `ch` is the width of a zero, wider than the average letter, so 65ch runs 75–90 characters.
- On narrow screens let the line shorten with the viewport. Never make body text scroll sideways; set `overflow-wrap: break-word` so long URLs wrap.

### Leading and space

- `line-height` is unitless. Body 1.4–1.6, plus about 0.1 for every 10 characters of measure above 65. Headings tighter, toward 1.1 at display sizes. (default)
- Put space below text blocks only (`margin-block-end`), in steps of the body line height (`1lh`); headings are the exception and take extra space above. Rhythm is a guide, not pixel law. (default)
- A heading sits closer to the text it introduces than to the text above it. Space between sections exceeds space within them.

### Hierarchy and color

- Build hierarchy with size and weight first, then position, then a contrasting face, then color, used sparingly. (default)
- Text that does the same job looks the same; text with different jobs does not.
- Body text in a near-black gray (#161616–#333), not #000. Name colors as custom properties (`--text`, `--text-muted`, `--link`). (default)
- Contrast at least 4.5:1 for body text and 3:1 for large text (24px+, or 18.66px+ bold); 7:1 and 4.5:1 where AAA is required. For thin or light weights, WCAG 2 can mislead; add an APCA check.
- Never carry meaning with color alone. Text over images gets a scrim, overlay, or shadow.

### Links and wrapping

- Underline links and nothing else. Links get a color distinct from body text, plus an underline with `text-decoration-thickness: 0.08em`, `text-underline-offset: 0.12em`, and `text-decoration-skip-ink: auto`. A softer underline color that turns `currentColor` on hover is fine. (default for the numbers)
- `text-wrap: balance` on headings, captions, and pull quotes only, never body text, where it is slow and pointless. `text-wrap: pretty` on paragraphs and list items. Both fall back safely, so drop the `&nbsp;` and `<wbr>` hacks they replace.
- Use real quotes and apostrophes, en dashes for ranges, and tabular figures (`font-variant-numeric: tabular-nums`) where numbers align. The rest of the micro-typography rules are in the print reference and apply on screen too.

### Dark mode

- Dark mode is not an inverted palette. Background #121212–#1a1a1a, text #e0e0e0–#f0f0f0, about 13–16:1. Never pure white on pure black (21:1); the letters glow and tire the eye. (default)
- Raise the body weight 20–50 units on a variable face, or one step on a static family, most of all for light weights and small sizes. Optionally add 0.1 to the body line height. (default)
- Swap color tokens under `@media screen and (prefers-color-scheme: dark)`, so print keeps the light tokens, and check contrast in both modes.

## Files

| Path | What it is | Read it when |
| --- | --- | --- |
| `templates/typography.css` | Starter stylesheet applying every web rule: font loading, tokens with computed contrast, fluid scale, measure, rhythm, links, wrapping, dark mode | Writing or replacing a site's base text styles |
| `references/print.md` | Print and PDF rules: format, margins, grids, size and leading, justification, micro-typography, CMYK, paper, bleed, PDF/X, font embedding, accessible PDFs, print CSS | Any print, PDF, or print-stylesheet task, or micro-typography details on screen |
| `LICENSES.md` | Source and MIT notice | Redistributing or quoting this skill |

## Related skills

For spacing, color, mobile, and dashboard rules every screen must pass, use [ui-rules](../ui-rules/SKILL.md).
