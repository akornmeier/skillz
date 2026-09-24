# Paywall workflow

## Owned job

Design the in-product decision shown when a paid feature gate, usage limit, trial end, or tier entitlement blocks or changes what a user can do. Define trigger, message hierarchy, screen copy, upgrade action, truthful consequences, alternatives, and escape behavior.

**Exclude:** non-blocking promotional upsells, public pricing-page copy, package or price-setting decisions, signup/onboarding, cancellation or save flows, failed-payment/dunning flows, and payment-system implementation.

## Input checklist

- [ ] Gate type: feature, usage limit, trial end, or tier entitlement
- [ ] Exact trigger and action the user was attempting
- [ ] Current plan, destination plan, and gated entitlement or limit
- [ ] Value the user has already experienced and benefit unlocked by upgrade
- [ ] Displayed price, billing period, trial terms, and renewal terms, if applicable
- [ ] Exact consequences of declining or letting the trial end, including data and access
- [ ] Available alternatives: delete, reduce usage, continue free, export, back, or close
- [ ] Platform and flow constraints

## Process

1. **Confirm route fit.** Verify the router's paywall condition still holds; return to the router if new facts invalidate it.
2. **Map the consequence.** State what action is blocked, what remains available, what happens to existing work or data, and every non-purchase option. Apply `../references/voice-and-evidence.md` to consequence and urgency wording.
3. **Set the hierarchy.** Lead with why the screen appeared, then the relevant outcome unlocked, plan and billing facts, primary upgrade action, practical alternative, and visible close or back action.
4. **Draft for the gate type.** Feature gates explain the paid capability; limits show the current limit and next available action; trial-end screens state the effective time and post-trial state. Keep benefits tied to the user's current task.
5. **Make the choice explicit.** Name billing period and charge before commitment. Apply the shared reference's autonomy rules to defaults, actions, dismissal, and refusal copy.
6. **Define escape behavior.** Closing or declining returns the user to a safe state without losing unaffected work. A hard gate may appear again when the user retries it; otherwise respect dismissal and avoid repeated interruption.
7. **Specify the handoff.** Describe the next upgrade step, confirmation, immediate entitlement change, and recovery if purchase is canceled or fails, without designing payment infrastructure.

## Output template

```markdown
## Paywall decision brief
- Gate type / trigger:
- Attempted action:
- Why this moment:
- Upgrade unlocks:
- Current plan → destination plan:

## Consequence map
- If upgraded:
- If declined / dismissed:
- Existing work and data:
- Non-purchase alternatives:

## Screen copy
- Headline:
- Body:
- Plan / price / billing line:
- Primary CTA:
- Alternative action:
- Close / back label:
- Supporting details:

## Behavior
- On primary CTA:
- On alternative:
- On close / back:
- When it may appear again:
- After successful upgrade:

## Unresolved facts
- [Fact required before stronger or more specific copy is safe]
```

## Stop conditions

- If post-decline, post-limit, or post-trial consequences are unknown, ask one compact question before writing consequence or loss language.
- If the upgrade action would commit a purchase but price, billing terms, or escape path cannot be established, ask one compact question. If purchase occurs in a later disclosed step, omit unknown terms from copy and list them under unresolved facts.
- If requested wording or behavior fails the loaded integrity or autonomy rules, apply that reference's safe treatment and continue.
- If new facts invalidate the router's paywall condition or place the request in an excluded area, stop and return to the router.

## Paywall quality check

- [ ] New facts still satisfy the router's paywall condition.
- [ ] Copy says why the screen appeared and what the upgrade changes.
- [ ] Decline consequences distinguish blocked action from unaffected access, work, and data.
- [ ] Price, billing period, renewal, and trial terms shown are explicit where relevant.
- [ ] Primary CTA, non-purchase alternative, and close or back action are unmistakable.
- [ ] Dismissal returns safely and recurrence follows retry or a stated rule.
- [ ] Every loaded shared-reference decision is reflected in wording and behavior.
