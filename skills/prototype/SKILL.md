---
name: prototype
description: Builds throwaway interactive prototypes to test state models, business logic, data shapes, or competing UI layouts. Use when validating whether logic feels correct or exploring multiple interface variants before production implementation.
compatibility: Requires the host project's existing runtime and task runner. Browser access is needed for UI variants; a terminal is needed for logic prototypes.
metadata:
  category: product-prototyping
---

# Prototype

A prototype is temporary code that answers one explicit question. Choose one branch before writing:

- **Logic, state transitions, or data shape:** read [LOGIC.md](LOGIC.md). Build a small interactive terminal app that exposes difficult cases.
- **Layout, hierarchy, or UI direction:** read [UI.md](UI.md). Build structurally different variants on one route with a URL-stable switcher.

If genuinely ambiguous, ask. When the user is unavailable, choose the branch that matches the surrounding code and state the assumption.

## Shared contracts

1. Mark prototype code clearly and place it near the relevant module or page without inventing a new project structure.
2. Provide one command or URL that runs the prototype through the project's existing tooling.
3. Keep state in memory by default; use isolated scratch persistence only when persistence is the question.
4. Add only the tests, error handling, and abstraction needed to run the experiment safely and answer its question. Production standards apply when validated code is promoted.
5. Make relevant state and variant identity visible so the user can explain what changed.
6. Verify the run command, primary interactions, and cleanup path before handoff.
7. After the question is answered, fold the decision into production code through the normal review process. Ask before creating branches, commits, issue comments, or other externally visible records. Do not leave prototype-only routes, switchers, or unsafe shortcuts in production.
