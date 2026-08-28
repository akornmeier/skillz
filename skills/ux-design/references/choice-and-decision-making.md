# Choice and decision-making

Use these principles when users must choose, prioritize, compare, or act under uncertainty. Reducing decisions is not automatically good: discoverability, informed consent, comparison, expert speed, and reversibility may require visible options.

## Choice Overload

**Principle.** A large or poorly differentiated option set can increase effort, avoidance, regret, or arbitrary selection.

**Use when:** plan selection, product catalogs, filters, permission prompts, settings, or onboarding choices produce hesitation or abandonment.

**Design moves:** remove irrelevant options for the current context; group by goal; explain meaningful differences; provide filtering and side-by-side comparison; offer a transparent, reversible recommendation where evidence supports it.

**Failure modes:** hiding fees or tradeoffs; collapsing distinct choices into vague labels; assuming fewer options always improve outcomes; using a default to steer users against their interests.

**Validate:** decision time, abandonment, reversals, errors, confidence, and comprehension of tradeoffs.

Source: https://lawsofux.com/choice-overload/

## Cognitive Bias

**Principle.** Human judgments use shortcuts that can systematically distort interpretation and decisions; designers and stakeholders are subject to these biases too.

**Use when:** framing prices, defaults, social proof, prioritizing roadmap evidence, interpreting research, or reviewing potentially manipulative patterns.

**Design moves:** present balanced evidence; make defaults explicit and reversible; separate observed facts from interpretation; seek disconfirming evidence; include affected groups in review; document who benefits from the framing.

**Failure modes:** treating users as irrational targets to exploit; labeling any disagreement a bias; believing awareness eliminates bias; using dark patterns justified as “behavioral design.”

**Validate:** comprehension testing, alternative framings, independent review, disaggregated outcomes, and predeclared success criteria.

Source: https://lawsofux.com/cognitive-bias/

## Hick’s Law

**Principle.** Decision time often grows with the number and complexity of meaningful alternatives, especially when options are unfamiliar and speed matters.

**Use when:** commands, emergency actions, navigation, first-run choices, and complex multi-step tasks.

**Design moves:** reduce irrelevant alternatives; group and label by user goal; sequence dependent decisions; make common paths easy; retain search or expert access; explain differences where comparison is necessary.

**Failure modes:** “always show fewer choices”; hiding options users need to compare; applying the law to skilled scanning or open-ended browsing without evidence; simplifying into ambiguous abstractions.

**Validate:** time to a correct choice, first-click success, error/reversal rates, and novice-versus-expert performance.

Source: https://lawsofux.com/hicks-law/

## Occam’s Razor

**Principle.** When alternatives explain and support the task equally well, prefer the one with fewer assumptions or unnecessary parts.

**Use when:** choosing between interaction models, reducing feature or visual complexity, and resolving speculative architecture.

**Design moves:** remove elements that do not support a user goal; prefer direct language and standard controls; compare simpler hypotheses before adding mechanisms.

**Failure modes:** mistaking minimalism for usability; deleting safeguards, context, accessibility, or advanced capability; claiming the simplest implementation is simplest for the user.

**Validate:** verify that the reduced design preserves completion, comprehension, recovery, edge cases, and expert needs.

Source: https://lawsofux.com/occams-razor/

## Pareto Principle

**Principle.** Outcomes and usage are often unevenly distributed; a small subset of causes or workflows may account for a large share of impact. The 80/20 ratio is a heuristic, not a guaranteed law.

**Use when:** prioritizing usability fixes, performance work, support issues, or common workflows.

**Design moves:** identify high-frequency/high-harm paths from actual data; improve those first while protecting critical low-frequency cases; segment rather than averaging unlike users.

**Failure modes:** inventing an 80/20 split; neglecting rare safety, accessibility, legal, or high-value tasks; optimizing only for the majority and excluding edge populations.

**Validate:** analyze observed distributions, severity, and segment-level outcomes; monitor what worsens after prioritization.

Source: https://lawsofux.com/pareto-principle/

## Combined checks

- Are options genuinely unnecessary, or merely inconvenient for the design?
- Can users understand differences without remembering multiple screens?
- Are recommendations and defaults transparent, reversible, and aligned with user interests?
- Does prioritization protect low-frequency but high-severity journeys?
- What evidence would falsify the team’s preferred framing?
