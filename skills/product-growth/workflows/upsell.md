# Upsell workflow

## Owned job

Promote incremental product value when the user can decline and continue: optional in-product upgrades, banners, modals, inline prompts, and a single expansion message tied to product use.

**Excludes:** paywalls, pricing/package design, pre-activation onboarding, referral or affiliate programs, lifecycle sequences, cancellation/dunning/billing mail, cold outreach, provider implementation, and channel scheduling.

## Input checklist

Confirm or derive:

- Current user state, value already experienced, qualifying behavior, and whether progress remains available without purchase
- Incremental capability/outcome, plan or eligibility rules, stated price/terms if shown, and destination after each action
- Surface/channel, timing, audience, exclusions, prior exposure/dismissal, and competing prompts
- Requested artifact: one in-product prompt or one expansion message
- Available product facts/proof plus voice, UI, legal, and measurement constraints

**Shared-reference routing:** If required product, plan, or audience facts remain missing after checking supplied/project context, the router loads `../references/product-context.md`. Load `../references/voice-and-evidence.md` for every interruptive in-product surface and whenever wording uses claims, proof, customer language, urgency, or comparison. Do not restate those rules here.

## Process

1. **Confirm route fit.** Verify the router's upsell condition still holds; return to the router if new facts invalidate it.
2. **Choose a value moment.** Prefer demonstrated success, relevant intent, approaching future need, renewal, or a positive milestone. Avoid prompts before the user can understand the incremental benefit.
3. **Map the message.** Connect value already received → next outcome → capability that unlocks it → accurate action and consequence. Use observed behavior only when collection and wording are appropriate.
4. **Choose the lightest surface.** Prefer inline or user-invoked prompts over interruption. Use one prompt for one decision; use a single expansion message only when it adds product-use context at a useful later moment.
5. **Set behavior rules.** Default to one prompt per qualifying event, suppress converted or ineligible users, remember dismissal until a new relevant event, and prevent overlapping prompts.
6. **Write the complete experience.** Include recognition, incremental outcome, primary CTA, neutral decline, and accurate next state.
7. **Apply shared integrity rules.** Use `../references/voice-and-evidence.md` for claims, persuasion, choice behavior, and accessibility.
8. **Measure responsibly.** Pair conversion rate with dismissals, task completion, complaints or unsubscribes, and downstream retained use. Label tests as hypotheses.

## Output template

```markdown
# Upsell recommendation
**User / qualifying moment:**
**Value already realized:**
**Incremental value:**
**Why this surface / timing:**

## Message hierarchy
1. [recognize context or progress]
2. [next outcome and relevant capability]
3. [clear choice and consequence]

## Ready-to-use copy
**Headline / subject:**
**Body / preview:**
**Primary CTA:**
**Decline:**
**After action / dismissal:**
## Behavior rules
- Eligibility / exclusions:
- Trigger / timing:
- Frequency / dismissal memory:
- Conflict / stop rules:
- How current progress remains available:

## Measurement and open inputs
- Primary outcome:
- Guardrails:
- [gap or assumption] → [needed input/test]
```

## Stop conditions

- New facts invalidate the router's upsell condition: stop and return to the router.
- No value moment or credible incremental benefit can be identified: ask one compact question or recommend no prompt.
- Current-plan behavior, eligibility, destination, or material terms are unknown: do not imply them; request the missing fact.
- A requested persuasion device fails the loaded integrity rules: apply that reference's safe treatment and continue.
- Request expands into onboarding, offer design, billing recovery, referrals, lifecycle programs, affiliate operations, or broad campaign strategy: stop and reroute or state the boundary.

## Route quality check

- Does the prompt occur after credible value or intent, and can the user continue without buying?
- Is incremental value tied to this user’s state rather than a generic feature list?
- Are CTA, neutral decline, next state, frequency, suppression, and conflict behavior explicit?
- Does a single expansion message have one job and stop when no longer relevant?
- Did the design apply every loaded shared-reference decision?
