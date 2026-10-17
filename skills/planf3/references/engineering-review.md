# Engineering review

Run this review when creating or updating plan content, and after a build deviation changes tasks, interfaces, or verification. The template owns the HTML shape; this review judges whether its content supports the request.

## Review gates

1. **Acceptance and coverage.** Compare the request and any source spec against the acceptance criteria. Each criterion describes observable behavior, with exact values where required. Each has implementing tasks and verification in the coverage table. Each task serves a criterion, including the supporting work needed to enable it. Non-goals and global constraints are explicit. Material assumptions and unresolved blockers remain visible even without `--questionable`.
2. **Interfaces.** For shared contracts, compare each consumer with its producer: names, signatures, types, defaults, error behavior, and ownership agree. Define a new contract once and link consumers to it; reference existing repository types. Omit interface blocks where no meaningful cross-task contract exists. Do not write implementation bodies that the contract and tests already determine.
3. **Verification.** Every task names concrete input cases or conditions, assertions, a repository-appropriate command (or an explicit manual procedure), and expected exit status and observable results. Trace each criterion to checks that actually exercise its behavior, not merely a passing suite. Task checks establish local behavior; phase checks establish integration; global checks establish repository-wide compatibility. Choose focused tests, builds, migration checks, or scoped visual/accessibility checks to suit the change rather than forcing identical TDD steps everywhere.
4. **Dependencies.** Producers precede consumers; phase ordering and bounded runs preserve prerequisites. Parallel lanes do not share writable files. A failed prerequisite blocks dependent work rather than becoming a completed checkbox.
5. **Executability.** Existing paths, symbols, and commands are grounded in the repository; proposed paths are labeled new. Required tools, fixtures, and setup are identified. Distinguish intended test coverage from checks actually executed. If a failing test is required, its expected failure concerns the target behavior, not an unrelated setup error.
6. **Failure modes and scope.** Relevant boundaries, invalid inputs, partial failures, and compatibility concerns have owners and checks. Remove speculative tasks and redundant code transcripts. Missing product decisions are blockers, not permission to invent requirements.

## Repair loop and record

Fix findings, rerun structural validation, and repeat the affected review gates until no actionable findings remain. An interface repair includes its consumers; a task or test repair includes its coverage rows. Do not equate a validator exit code with semantic correctness.

Record a concise review result in Notes: gates checked, repairs made, remaining assumptions or blockers, and checks not performed. Unresolved blockers may be delivered for a decision only when labeled **not build-ready**; do not proceed to implementation. Self-review is not independent review, and planned verification is not execution evidence.
