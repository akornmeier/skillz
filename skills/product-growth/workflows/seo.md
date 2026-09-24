# SEO workflow

## Owned job

Optimize one named page for page-level organic discovery: search intent, page and heading structure, title and meta description, contextual internal links, and extractable answers. When used as a secondary pass, begin only after the primary route has produced the page.

**Exclude:** crawl/indexation engineering, robots or sitemap work, Core Web Vitals, programmatic SEO systems, broad content calendars or site architecture, publishing/deployment, backlink campaigns, and standalone schema generation or validation.

## Input checklist

- [ ] Target page, current draft, or enough detail to create its structure
- [ ] Primary query and any known related questions
- [ ] Audience, buyer stage, and desired page action
- [ ] Page type: article, product, use case, comparison, alternative, or other
- [ ] Search-result or competitor observations, if available
- [ ] Candidate pages for contextual internal links
- [ ] Required product facts, proof, and constraints for this page

## Process

1. **Set the page job.** Classify primary intent and buyer stage. State what the searcher needs answered and what action the page should support. Keep related queries only when the same page can answer them coherently.
2. **Diagnose intent fit.** Compare current page promise, opening, coverage, and CTA with that job. Name mismatches before proposing edits.
3. **Build the answer path.** Write one descriptive H1, then order H2/H3 sections around searcher decisions. Use definition, steps, comparison, pros/cons, or FAQ sections only when intent calls for them. Comparison pages must explain who each option fits, not merely rank the seller first.
4. **Draft metadata.** Provide a distinct title and meta description that match page content, primary intent, and likely click motivation. Avoid keyword repetition; apply `../references/voice-and-evidence.md` to claims and promises.
5. **Make answers extractable.** Put a direct, self-contained answer immediately after each question-like heading. Use numbered steps for processes and tables for true side-by-side comparisons; add context after the direct answer.
6. **Plan internal links.** Suggest relevant inbound and outbound links with descriptive anchors, placement, and purpose. Use confirmed URLs only; label the rest as candidate pages.
## Output template

```markdown
## Page-level SEO brief
- Page / type:
- Primary query:
- Intent / buyer stage:
- Searcher need:
- Page action:
- Main diagnosis:

## Metadata
- Title:
- Meta description:

## Page structure
| Level | Heading | Searcher question / section job | Block format |
|---|---|---|---|

## Extractable answer blocks
### [Question heading]
[Direct standalone answer, followed by supporting context if needed]

## Internal links
| Direction | Source | Target | Suggested anchor | Placement / purpose |
|---|---|---|---|---|

## Evidence or content gaps
- [Missing fact needed for a claim or section]
```

## Stop conditions

- If no target page or primary query can be established, ask one compact question for the minimum missing inputs before drafting.
- If requested work is only an excluded technical, scaled, planning, or deployment task, state the page-level boundary and offer a page brief as the narrow handoff.
- If live-page access is unavailable, do not claim a rendered-page or search-result inspection; work from supplied content and label the limitation.

## SEO quality check

- [ ] One primary intent governs title, H1, section order, and CTA.
- [ ] Important questions receive immediate answers that still make sense when extracted.
- [ ] Headings are descriptive, hierarchy is logical, and terms read naturally.
- [ ] Metadata accurately previews page content without unsupported promises.
- [ ] Every link suggestion is contextual, has a descriptive anchor, and points to a confirmed URL or labeled candidate.
- [ ] Ranking diagnosis labels technical health and authority as untested unless evidence was supplied.
- [ ] Deliverable remains page-level and includes no crawl, pSEO, calendar, deployment, or standalone schema work.
