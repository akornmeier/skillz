# Onboarding workflow

## Owned job

Design registration through post-submit handoff, activation messaging, and the first-run path to a defined value event. Own field/step reduction, verification and success states, setup sequencing, empty states, checklists, prompts, recovery copy, and activation measurement.

**Excludes:** lead-capture forms, ongoing lifecycle or retention email programs, broad feature education, paywalls, churn recovery, and product implementation. A single transactional welcome, verification, or stalled-first-run message may support the first-run path; route multi-day nurture elsewhere.

## Input checklist

Confirm or derive:

- Product, user segment, entry source, device constraints, and signup/activation model
- Activation event and evidence that it predicts meaningful value or retention
- Current registration-to-activation screens, fields, actions, permissions, and step count
- Required account data, security/compliance rules, verification timing, and SSO options
- Current drop-off, completion, errors, time-to-value, and segment/cohort data
- Available defaults, templates, demo data, imports, and ways to defer setup
- Voice, UI constraints, support paths, and exact first value users should experience

## Process

1. **Define the boundary.** Distinguish registration, verification, first-run onboarding, and activation. State one measurable activation event; if supplied, preserve it.
2. **Inventory the path.** List every screen, field, click, confirmation, permission, choice, empty state, and wait between entry and activation.
3. **Remove before rewriting.** For each item, keep only what is required for account access, safety, personalization needed now, or activation. Cut, infer, prefill, defer, combine, or make skippable otherwise.
4. **Reconstruct the minimum path to value.** Put the shortest convincing outcome first. Use one primary action per screen, smart defaults, available real or demo data, and progressive disclosure after activation.
5. **Choose guidance sparingly.** Use inline prompts and purposeful empty states before tours. Add a short checklist only when multiple required actions remain; order by value, show honest progress, and allow dismissal when optional.
6. **Write each state.** Provide headline, one-line rationale, field labels/help, primary action, secondary or skip action, errors, loading/waiting feedback, and success transition. Explain verification or permissions before requesting them.
7. **Design recovery.** Preserve completed work, return users to the next incomplete action, provide resend/change/retry paths, and offer human help where failure cannot be self-resolved.
8. **Instrument the path.** Define entry, per-step completion/error, abandonment, activation, and time-to-activation events. Segment only where a distinct path or requirement exists.
9. **Prioritize one change.** Fix the largest observed drop-off or remove the largest unnecessary barrier first; label unmeasured recommendations as hypotheses.

## Output template

```markdown
# First-run recommendation
**User / entry point:**
**Activation event:** [observable event]
**Current path:** [N steps, key drop-off]
**Proposed MPTV:** [N steps]
**Primary hypothesis:**

## Keep / remove / defer
| Current item | Decision | Reason |
|---|---|---|

## First-run flow and copy
| Step/state | User action | Headline + support copy | Primary CTA | Escape/recovery | Event |
|---|---|---|---|---|---|

## Required states
- **Verification or permission:**
- **Guidance / progress treatment:**
- **Empty state:**
- **Error/retry:**
- **Return after interruption:**
- **Activation success + next action:**

## Measurement
- Activation rate:
- Median time to activation:
- Step conversion/error:
- Segment or cohort cut:

## Assumptions and next test
- [assumption] → [measurement or experiment]
```

## Stop conditions

- No activation event can be identified from product behavior or supplied data: ask one compact question before prescribing a flow.
- Legal, security, verification, or required-data constraints are unclear: do not recommend removing or delaying them; mark for confirmation.
- A detailed audit lacks the current flow or states: request the artifact before claiming observed defects. A labeled greenfield or minimum-path concept may proceed from a supplied activation event and known friction.
- Request expands into an ongoing email calendar or retention program: stop at activation and state the boundary.
- A proposed personalization branch lacks a distinct user need or data signal: keep one default path.

## Route quality check

- Is activation one observable value event rather than “completed onboarding”?
- Is every pre-activation step essential, deferred, or explicitly justified?
- Can users identify one next action, skip optional guidance, recover from errors, and resume without lost work?
- Does copy explain value and consequences at the moment of action without teaching the whole product?
- Do events reveal where users stall and how long activation takes, without turning first-run into an ongoing lifecycle program?
