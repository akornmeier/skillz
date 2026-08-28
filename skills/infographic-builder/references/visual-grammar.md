# Visual grammar

Choose the visual from the analytical question, not from a preferred template.

## Selection table

| Question | Start with | Key checks |
|---|---|---|
| How much? | Direct number, bar | Supply unit, denominator, and benchmark |
| Which is larger? | Sorted bar or dot plot | Start bar baselines at zero |
| How did it change? | Line or slope chart | Preserve intervals and show gaps |
| How is it distributed? | Histogram, strip, box plot | Show sample size; explain bins/statistics |
| Are variables related? | Scatter plot | Avoid causal language; handle overplotting |
| What share? | Stacked bar or a small pie/donut | Parts must share one whole; keep slices few |
| What happened when? | Timeline | Strict chronological order and proportional spacing when meaningful |
| What happens next? | Process/flow | Distinguish sequence, choice, loop, and parallel work |
| What belongs under what? | Tree or nested layout | Make hierarchy depth and ordering explicit |
| Where? | Map | Geography must explain the pattern; normalize counts when needed |
| What is the exact value? | Table | Align numbers and expose units |

## Encoding integrity

- Position on a common scale is usually more precise than length, angle, area, or color.
- Use area-scaled symbols correctly: radius must grow with the square root of value.
- Use zero baselines for bars and other length encodings.
- If a non-zero baseline is defensible for position charts, label it clearly.
- Do not use perspective, volume, or 3D extrusion for quantities.
- Distinguish zero, missing, unavailable, and not applicable.
- Direct-label series and key values when space allows.
- Show uncertainty when it is material to interpretation.
- Use a diverging scale only around a meaningful midpoint.

## Diagram integrity

Diagrams explain systems but can still mislead:

- arrow direction must have a defined meaning;
- line thickness must not appear quantitative unless it is;
- proximity and containment imply relationships—use them intentionally;
- equal-sized cards suggest equal status;
- sequence numbering must match reading order;
- cycles must show where and why the loop closes;
- decorative icons must not look like a scale.

## Avoid by default

- 3D charts;
- dual axes;
- gauge charts for ordinary values;
- pies with many or similar slices;
- word clouds as evidence of frequency;
- maps when categories would compare better in a bar chart;
- pictogram counts where partial icons or icon area distort magnitude;
- generated charts or maps that cannot be audited.

## Responsive transformations

Do not merely shrink a wide layout. At narrow widths:

- stack panels in story order;
- change grouped bars to small multiples when labels collide;
- move legends to direct labels or a compact key;
- reduce annotation count without removing essential caveats;
- preserve minimum text size and touch targets;
- offer a table or summary for dense visuals.
