---
name: infographic-builder
description: Plans, builds, and reviews evidence-based infographics, storyboards, SVGs, HTML visuals, social graphics, and generation prompts. Use when research, statistics, comparisons, timelines, or processes must become a sourced, accessible visual narrative.
compatibility: Local planning and SVG or HTML work requires file access; bundled scripts require Python 3. Optional Higgsfield work requires separate authentication, credits, network access, and explicit approval.
metadata:
  category: design
  outputs: infographic
---

# Infographic Builder

Build the information architecture first and the visual artifact second. Every visual element must help a defined audience understand one defensible message.

## Non-negotiable rules

- Never invent facts, values, dates, units, citations, denominators, or causal claims.
- Separate sourced facts from interpretation and design recommendations.
- Preserve time periods, populations, geographies, uncertainty, and caveats.
- Do not encode meaning with color alone or make decoration appear quantitative.
- Include readable sources and a text alternative in production delivery.
- Prefer deterministic SVG or HTML for charts, labels, maps, and citations.
- Never install software, upload material, spend credits, or claim checks without approval and evidence.
- Treat generated text, labels, numbers, and quantitative geometry as untrusted drafts.

## Choose the mode

Infer the least risky mode that satisfies the request:

1. **Plan:** brief, source ledger, story spine, and storyboard.
2. **Build locally (default):** plan plus editable SVG, HTML, or a component in the user's stack.
3. **Hybrid:** deterministic information layer plus an approved generated illustration or background.
4. **Generated concept:** visual exploration only; recreate verified information in an editable deterministic layer.

Ask a question only when the answer changes audience, evidence, safety, scope, format, or spend.

## Workflow

### 1. Inspect and scaffold

Inspect source material, datasets, links, brand assets, target channel, dimensions, language, accessibility needs, and repository conventions. Read [references/discovery.md](references/discovery.md) when inputs or requirements are ambiguous.

For a new package, run:

```bash
python3 <skill-directory>/scripts/scaffold.py <output-directory> <slug>
```

Complete the generated brief, source ledger, and storyboard before production.

### 2. Define the communication contract

Record the audience, context, goal, one-sentence main message, ten-second recall test, required facts, prohibited claims, and delivery constraints. If the message contains unrelated outcomes, split the artifact or choose one.

### 3. Build and verify the evidence ledger

For every factual claim, record a stable claim ID, exact wording or value, units, period, population or geography, source, access date, caveat, and verification status. Read [references/evidence-and-story.md](references/evidence-and-story.md).

Stop for clarification when sources conflict, cannot be opened, omit required context, mix incompatible populations or units, overstate causality, or create rights or confidentiality risks. Mark unknowns; never fill them with plausible values.

### 4. Select the story and visual grammar

Build one story spine: hook → strongest verified anchor → two to four supporting facts → context → caveat → implication or action. Every panel must map to a claim ID or be explicitly explanatory or decorative.

Read [references/visual-grammar.md](references/visual-grammar.md) before choosing charts or diagrams. Use the simplest form that answers the analytical question; avoid 3D quantitative marks, misleading baselines, decorative maps, and area encodings that imply unsupported magnitude.

### 5. Storyboard before styling

Assign each section a job, claim IDs, visual form, takeaway, and visual weight. Establish primary, secondary, and tertiary reading levels. Read [references/layout-and-art-direction.md](references/layout-and-art-direction.md) for medium-specific composition and generation-prompt guidance.

### 6. Produce the editable source of truth

Default output order:

1. `<slug>.brief.md`
2. `<slug>.sources.csv`
3. `<slug>.storyboard.md`
4. editable `.svg`, `.html`, or project component
5. `<slug>.alt.md`
6. `<slug>.validation.md`
7. optional derived `.png` or `.pdf`

For SVG, include `viewBox`, `<title>`, `<desc>`, selectable labels, semantic groups, and readable source notes. For HTML, use semantic structure, a summary or data table, keyboard-accessible interaction, responsive layouts, and reduced-motion support.

Use Higgsfield only after explicit approval and only for non-data-bearing imagery. Read [references/higgsfield.md](references/higgsfield.md) before any command. Check availability without authenticating or spending credits:

```bash
<skill-directory>/scripts/check-higgsfield.sh
```

### 7. Validate, repair, and deliver

Read [references/quality-gates.md](references/quality-gates.md), inspect at intended size, and verify evidence, calculations, visual semantics, hierarchy, density, contrast, accessibility, source legibility, and export integrity.

Run the structural validator:

```bash
python3 <skill-directory>/scripts/validate_infographic.py <output-directory> <slug> --production --strict
```

Fix errors and warnings, rerun, and complete the manual review. The script cannot prove factual, visual, or accessibility correctness.

Deliver file paths, formats, main message, source limitations, assumptions, unresolved risks, commands actually run, checks completed, external services and costs, and the recommended next review or export step.
