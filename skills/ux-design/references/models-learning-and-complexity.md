# Models, learning, and complexity

Use these principles when users transfer prior knowledge, skip instruction, learn by doing, or encounter necessary domain complexity. Research users’ language and expectations rather than assuming the design team’s model is shared.

## Jakob’s Law

**Principle.** People bring conventions learned from other products and usually expect familiar interface patterns to behave consistently.

**Use when:** navigation, forms, commerce, search, account controls, or redesigns introduce a novel interaction model.

**Design moves:** follow platform and domain conventions; spend novelty where it creates real value; make migration reversible or staged when practical; retain familiar terminology and control behavior.

**Failure modes:** copying a competitor’s defects; suppressing useful innovation; assuming conventions are identical across cultures, devices, or accessibility modes; changing appearance while secretly changing behavior.

**Validate:** expectation tests before interaction, first-click success, migration studies, support issues, and novice-versus-returning-user behavior.

Source: https://lawsofux.com/jakobs-law/

## Mental Model

**Principle.** Users form simplified internal explanations of how a system works and use them to predict outcomes.

**Use when:** users repeatedly take the “wrong” path, fear irreversible outcomes, misinterpret state, or apply vocabulary differently from the team.

**Design moves:** learn models through interviews, observation, card sorting, journey mapping, and error analysis; expose state and consequences; use user vocabulary; make conceptual objects and relationships consistent.

**Failure modes:** treating personas as evidence of a mental model; training around a confusing architecture; mistaking the implementation model for the user model; assuming one audience has one model.

**Validate:** ask users to predict the result of an action, explain where information lives, and recover from a changed or unexpected state.

Source: https://lawsofux.com/mental-model/

## Paradox of the Active User

**Principle.** Many users begin acting toward an immediate goal instead of first reading comprehensive instructions, even when instruction might save time later.

**Use when:** onboarding is skipped, manuals go unread, users learn through trial, or advanced capability remains undiscovered.

**Design moves:** enable a safe first success; teach in context at the moment of need; use examples and progressive hints; keep help searchable and persistent; allow undo and recovery.

**Failure modes:** mandatory tours before users have context; tooltip cascades; hiding core controls until training is complete; assuming nobody uses documentation.

**Validate:** first-session observation, time to first meaningful outcome, hint use, error recovery, later feature discovery, and return-to-help behavior.

Source: https://lawsofux.com/paradox-of-the-active-user/

## Tesler’s Law

**Principle.** Every meaningful system contains some irreducible complexity; design determines whether the system, the user, or another actor bears it.

**Use when:** simplifying expert tools, compliance flows, configuration, data entry, or complex domains.

**Design moves:** identify the irreducible decisions; automate repeatable work safely; provide defaults with visible assumptions; stage complexity by role and moment; keep advanced control available; document where complexity was moved.

**Failure modes:** hiding complexity rather than reducing it; shifting work to users, support, operations, or error recovery; over-automating judgment; designing for an idealized rational user.

**Validate:** map effort across the full service, including exceptions and downstream actors; test novice and expert paths, override behavior, and automation failures.

Source: https://lawsofux.com/teslers-law/

## Combined checks

- What does the user expect before interacting, and where did that expectation come from?
- Does terminology match the user’s domain rather than the data model?
- Can a user achieve a safe first outcome without completing a tour?
- Which complexity is inherent, which is extraneous, and who bears each part?
- Do defaults and automation expose assumptions and support correction?
