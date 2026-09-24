---
name: unslop
description: Revises prose to remove formulaic AI-sounding language while preserving meaning, voice, facts, formatting, and protected text. Use when the user asks to humanize, tighten, de-slop, or edit prose for a more natural voice. Do not apply automatically to code, quotations, legal text, or text the user asked to preserve exactly.
compatibility: Has no runtime dependencies. Works with plain text and text-based documents; follow the document's house style and preservation constraints.
metadata:
  category: prose-editing
---

# Unslop

Edit prose, not the author's intent. A natural voice is specific and appropriate to the audience, not deliberately messy.

## Workflow

1. Identify the audience, purpose, requested tone, house style, and protected spans.
2. Mark facts, quotations, citations, links, code, product names, legal language, and exact strings that must not change.
3. Remove only patterns that make the prose vague, repetitive, inflated, or formulaic.
4. Preserve meaning and factual certainty. Do not add opinions, anecdotes, sources, or claims.
5. Compare the revision with the source, restore accidental meaning changes, and check formatting.

If the user asks for diagnosis rather than a rewrite, report examples and suggested changes without editing the text.

## Editing priorities

1. **Meaning and protected text:** Preserve claims, qualifiers, quoted material, Markdown structure, links, code, and requested terminology.
2. **Specificity:** Replace vague praise, generic concern, and unsupported attribution with available facts. If no fact is available, cut the claim rather than inventing one.
3. **Directness:** Remove throat-clearing, chatbot pleasantries, generic conclusions, and repeated summaries.
4. **Plain language:** Prefer concrete verbs and familiar words over puffery, jargon, and abstract metaphors.
5. **Rhythm:** Vary sentence length when it improves readability; split sentences that require rereading.
6. **Consistency:** Use one term for one concept and follow the document's punctuation and heading style.

## Common patterns

Revise when they hurt the text, not as blanket bans:

- promotional filler: "pivotal," "vibrant," "groundbreaking," "testament to"
- vague attribution: "experts believe," "reports suggest," "some critics argue"
- empty participles: "highlighting," "showcasing," or "ensuring" without a concrete result
- inflated verbs: "serves as," "stands as," "boasts," "utilizes," "leverages"
- canned contrasts and lists: forced "not just X, but Y," false ranges, or automatic groups of three
- synonym cycling: several labels for the same person or concept
- filler and hedging: "it is important to note," "in order to," "could potentially"
- chatbot voice: "Of course," "Great question," "I hope this helps," or a closing offer with no purpose
- unsupported feeling language: "stays close at hand" when a mechanism or measurable fact is available
- formatting habits: excessive em dashes, colons, bold lead-ins, title case, or decorative emoji

Do not replace one tell mechanically with another. Punctuation, passive voice, adverbs, first person, and technical terms can all be correct in context.

## Examples

**Inflated**

> This groundbreaking release serves as a testament to our enduring commitment to innovation.

**Direct**

> This release adds offline sync and cuts startup time from 2.1 seconds to 1.4 seconds.

**Preservation case**

> The contract defines "Services" as a legal term, and the code sample calls `createServices()`.

Keep the quotation and identifier exact unless the user explicitly asks to change them.
