# Audit Skills

Read-only directory health check by default. Findings prioritize work; scanning is not behavioral qualification.

1. Resolve the requested root(s). If absent, inspect relevant conventional/configured roots for the client's setup and state coverage; ask when ambiguous. Use `references/compatibility.md` for locations/collisions. Do not equate conventional roots with every installed package.
2. Scan once: run `uv run --offline --script <base>/scripts/lint_skill.py <root> ...` with explicitly resolved roots after approved setup. Classify unreadable/malformed portable entries as BROKEN portability; other format/local errors or advice as FLAGGED; no findings as mechanically CLEAN. Client loaders may tolerate defects, so actual load status needs client evidence. No per-skill subprocess loop.
3. Triage BROKEN first: report concrete defects and proposed fixes. Confirm scope before repair/removal; an audit does not authorize mutation, paid runs, or changes to installed copies.
4. Assess selected skills: default to a single agent. Use relevant dimensions of `references/review-rubric.md`; assess all fourteen only for comprehensive grades. Prioritize flagged skills, but a user-selected mechanically clean skill may still merit judgment review. Delegation is optional for broad work, with explicit ownership and approved model/time budget; never automatically create one grader per flag. Reuse mechanical facts across identical copies, not behavioral passes from a different revision/setup.
5. Report in chat unless a saved report was requested: BROKEN first, then FLAGGED in linter severity order. Give each actionable finding its evidence and suggested fix. State how many were scanned, graded, unassessed, and behavior-qualified (often zero). CLEAN means no detected mechanical finding, not full rubric or task success.
6. Offer the highest-priority scoped repairs. Keep remaining findings visible without silently expanding into the Improve route or launching profiles.
