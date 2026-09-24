# Copy workflow

## Owned job

Create or revise marketing-page and feature-page copy, including page-level conversion diagnosis.

**Excludes:** offer/pricing/package design, SEO optimization, blocked-action paywalls, optional expansion prompts, signup/onboarding flows, forms engineering, experiment execution, channel assets or calendars, paid ads, and media production. Return to the router when another route owns the primary decision.

## Input checklist

Confirm or derive:

- Mode: new draft, preservation-first edit, or CRO diagnosis
- Artifact and surface: page type, feature, existing copy/page, and requested format
- Audience, awareness/traffic context, problem, desired outcome, differentiator, and primary action
- Available product facts and proof; constraints on length, layout, terminology, and deliverable
- For CRO: observed behavior, baseline, known friction, and screenshots/page content when available

**Shared-reference routing:** If required product or audience facts remain missing after checking supplied/project context, the router loads `../references/product-context.md`. It loads `../references/voice-and-evidence.md` only when voice, customer language, proof, claim strength, urgency, persuasive UI, or accessibility needs guidance beyond supplied facts. Do not restate those references here.

## Process

1. **Set mode and boundary.** For edits, state what meaning and structure must survive. For CRO, separate observed problems from hypotheses.
2. **Build the argument.** Define current problem, credible better state, product path, and one primary action. Assign one idea to each section.
3. **Create or revise.** Default page order: hero, proof, problem, benefits, how it works, objections, and final CTA. Adapt order to the page’s job rather than filling every slot.
4. **Run preservation-first passes.** Check clarity, benefit connection, specificity, emotional fit, objection coverage, and action friction. After each change, confirm earlier meaning was not lost.
5. **Diagnose CRO when requested.** Review value proposition, headline/message match, CTA hierarchy, scannability, proof placement, objections, and friction in that order. Tie every recommendation to an observed issue; label unmeasured impact as a hypothesis.
6. **Apply shared integrity rules.** Use `../references/voice-and-evidence.md` for claim strength, customer language, persuasion, and accessible interaction copy.
7. **Deliver usable copy.** Provide complete requested text first, then concise rationale, alternatives, and unresolved inputs.

## Output template

```markdown
# Copy deliverable
**Mode / artifact:**
**Audience / page job:**
**Primary action:**
**Core argument:** [problem → outcome → product path]

## Diagnosis [edit or CRO only]
| Priority | Observed issue | Why it matters | Recommended change |
|---|---|---|---|

## Message hierarchy
1. [primary message]
2. [supporting message]
3. [objection/proof role]

## Ready-to-use copy
### Hero / opening
**Headline or hook:**
**Support:**
**Primary CTA:**

### Proof and problem
[Final section copy]

### Benefits and mechanism
[Final section copy]

### Objections and final CTA
[Final section copy]

## Alternatives
- [headline, hook, or CTA] — [when to use]

## Evidence gaps or assumptions
- [gap] → [needed input or safe treatment]
```

## Stop conditions

- Product, audience, desired outcome/problem, or primary action is too unknown for specific copy: ask one compact question for only missing facts.
- An edit lacks the original text, or a CRO audit lacks page content/screenshots: request the artifact before diagnosing; a labeled greenfield draft may still proceed.
- Pricing-page work is ambiguous between copy revision and offer redesign: return to the router for one targeted scope question.
- A claim, proof point, urgency device, or consequence fails the loaded evidence rules: apply that reference's safe treatment and continue.
- The attempted action is blocked, or the main job becomes SEO, offer, onboarding, or optional expansion: stop and reroute rather than combining workflows.

## Source note

The current-problem → better-state → product-path argument adapts Ludwig von Mises' Human Action Model from the prior copywriting guidance.

## Route quality check

- Can a reader identify what this is, who it is for, why it matters, and what to do next on one scan?
- Does an edit preserve supplied meaning, and does every CRO recommendation point to an observed issue?
- Does each section advance one coherent argument with one clear primary action?
- Is every requested artifact complete and ready to use, not merely advice or placeholders?
- Did the draft apply every loaded shared-reference decision?
