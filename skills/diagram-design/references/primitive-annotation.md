# Annotation Callout (italic-serif aside)

Use for editorial asides — the "italic pointer" that marks a detail without competing with the primary diagram grammar. Think marginalia: *"structure IS the index"*, *"no imports, no configuration"*.

## Grammar

```svg
<!-- 1. Italic resolved serif text -->
<text x="904" y="36" fill="var(--color-ink)" font-size="14" font-style="italic"
      font-family="Georgia, serif" text-anchor="end">no imports, no configuration</text>
<!-- 2. Dashed Bézier leader -->
<path d="M 820 44 Q 700 84 520 216" fill="none"
      stroke="var(--color-muted)" stroke-width="1" stroke-dasharray="4,3"/>
<!-- 3. Landing dot -->
<circle cx="520" cy="216" r="2" fill="var(--color-ink)"/>
```

## Rules
- Italic + serif together signal "editorial voice" against the diagram's sans/mono body. Don't substitute italic sans or italic mono — the combination is load-bearing.
- Dashed path (`stroke-dasharray="4,3"`) distinguishes the callout leader from primary arrows (which are solid).
- Place callouts in margins (top-right, bottom-left). Never inside the active diagram area.
- Max 2 callouts per diagram. More becomes commentary, not signal.

## Colors

| Intent | Text | Leader |
|---|---|---|
| Neutral aside | resolved `ink` | resolved `muted` |
| Focal / accent | resolved `accent` | resolved `accent` at lower opacity |
| Tertiary | resolved `muted` | resolved `soft` |

## Anti-patterns
- Solid arrow leader (reads as a flow arrow).
- Italic sans or italic mono — the serif is load-bearing.
- Callouts crossing primary arrows / lifelines — offset to a clear margin.
- Using a callout to label something the diagram should label directly — put the label on the element.
