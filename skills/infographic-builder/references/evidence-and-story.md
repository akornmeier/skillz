# Evidence and story

## Evidence ledger

Each visible factual statement should resolve to a claim ID. Recommended fields:

| Field | Purpose |
|---|---|
| `claim_id` | Stable reference used in storyboard and QA |
| `role` | hero, support, context, caveat, source-only |
| `claim_text` | Exact proposed wording |
| `value`, `unit` | Numeric value and unit, kept separate |
| `period` | Observation period or date |
| `population`, `geography` | Scope and denominator context |
| `source_title`, `publisher`, `source_url` | Provenance |
| `accessed_at` | Retrieval date |
| `method_note` | Definition, sample, uncertainty, or caveat |
| `status` | verified, needs-review, or blocked |

`verified` means the cited source was checked and supports the exact displayed claim. It does not mean the source is infallible.

## Data audit

Before comparing values, check:

- same unit and scale;
- same period or a clearly explained difference;
- comparable populations and geographies;
- nominal versus inflation-adjusted currency;
- total versus per-capita or rate;
- count versus percentage-point change versus percent change;
- observed, estimated, modeled, or projected values;
- sample size, uncertainty, suppression, and missingness;
- revised data and publication date;
- whether aggregation hides important variation.

Recompute derived values with inspectable code or formulas. Keep raw inputs and record rounding rules. Do not reverse-engineer precise values from a low-resolution chart unless clearly labeled as an estimate.

## Claim ladder

Rank candidate content:

1. **Main message:** the single claim the artifact exists to communicate.
2. **Proof:** strongest 2–4 pieces of evidence.
3. **Context:** benchmark, comparison, definition, or mechanism needed to interpret proof.
4. **Caveat:** limitation that changes interpretation.
5. **Detail:** useful only for close reading.

If the headline cannot be supported by the proof and caveat together, rewrite it.

## Story scoring

Score each candidate fact from 0–2 on:

- relevance to the audience's decision;
- strength and reliability of evidence;
- difference from what the audience likely knows;
- visual explainability;
- consequence if misunderstood.

Use the score to prioritize, not to automate editorial judgment. A necessary caveat may have low novelty but still be mandatory.

## Narrative tests

A good story passes these tests:

- **Ten-second test:** headline plus hero visual communicate the main message.
- **Because test:** every supporting panel can complete “The main message is true/important because…”
- **So-what test:** the implication follows without overstating causality.
- **Removal test:** removing a panel would weaken understanding; otherwise remove it.
- **Counterclaim test:** the visible caveat prevents the most likely misreading.
- **Source test:** every factual element can be traced to evidence.

## Headline patterns

Prefer evidence-backed conclusions over labels:

- Weak: “Quarterly Revenue”
- Better: “Revenue grew each quarter, led by enterprise renewals”

- Weak: “The Water Cycle”
- Better when appropriate: “Earth's water continually moves through four linked stages”

Do not make a conclusion headline when the evidence only supports a neutral topic title.
