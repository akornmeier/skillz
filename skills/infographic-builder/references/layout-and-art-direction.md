# Layout and art direction

## Build hierarchy before style

Allocate the strongest contrast and most area to the main message. Use spacing, alignment, grouping, and scale before borders, shadows, textures, or illustration.

A useful allocation heuristic—not a rigid formula:

- 10–15% title and framing;
- 40–55% primary evidence;
- 20–35% supporting evidence/context;
- 10–15% caveat, method, sources, and action.

Change this when the medium or story requires it. Never compress sources below legibility to preserve decoration.

## Storyboard fields

For each section record:

- section ID and reading order;
- communication job;
- associated claim IDs;
- exact takeaway;
- proposed visual form;
- priority: primary, secondary, tertiary;
- approximate span/height;
- annotation and caveat;
- mobile/reflow behavior;
- accessibility equivalent.

## Medium patterns

### Social/mobile

- use one dominant fact or short sequence;
- front-load context in the headline/deck;
- assume small display and quick scanning;
- consider a carousel rather than a dense poster;
- keep branding and source visible but subordinate.

### Presentation

- design for distance, not laptop zoom;
- one focal idea per visual;
- limit tiny footnotes; put full methods in notes or companion material;
- test at actual projection dimensions.

### Report/editorial

- support close reading with annotations, methods, and citations;
- retain a strong first-pass route through the page;
- avoid making every panel equal weight.

### Interactive web

- show an understandable default state;
- make filters and hover details optional, not required for the conclusion;
- support keyboard, touch, reduced motion, and a static/table equivalent;
- deep-link or label filtered state when users may share it.

## Art direction brief

Define:

- tone in audience terms, such as clinical, urgent, optimistic, editorial, or playful;
- palette roles: background, text, muted, primary data, highlight, warning;
- typography roles: display, body, number, source;
- illustration role: explanatory, contextual, emotional, or decorative;
- icon style and stroke/fill consistency;
- image treatment and crop behavior;
- what must remain editable and deterministic.

Avoid vague bundles like “beautiful, premium, modern.” Explain what visual choices make the tone appropriate.

## Prompt structure for image generation

When the user asks for a generation prompt, write it in this order:

1. artifact and exact aspect ratio/dimensions;
2. title, deck, and audience-appropriate tone;
3. composition and strict reading order;
4. section-by-section content with exact ordering;
5. palette, typography, icon/illustration language;
6. whitespace, density, and hierarchy;
7. negative constraints;
8. production note that generated text/numbers require replacement or verification.

Useful negative constraints:

- no extra statistics, labels, logos, pins, legends, or decorative charts;
- no reordered timeline dates or process steps;
- no illegible microtext or cropped title;
- no 3D quantitative marks;
- no invented map details;
- no text baked into illustration when an editable overlay is planned.

For factual work, generate the visual substrate separately and overlay verified text, charts, and citations in SVG/HTML/design software.
