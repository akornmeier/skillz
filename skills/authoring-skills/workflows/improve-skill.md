# Improve Skill

Match scope to the request. Do not turn a question or narrow repair into an unrequested rewrite or paid evaluation campaign.

## Modes

- **Review-only**: default for review, explain, assess, or questions. Return findings; no edits, snapshots/report files, model calls, or installed-copy changes. Use only already provisioned offline tools.
- **Targeted repair**: change the requested behavior or wording. Check affected dimensions and focused cases. Leave unrelated profiles and sections alone; ask before widening scope.
- **Comprehensive improvement**: explicitly requested broad improvement/release work. Assess all fourteen dimensions and retain repository release qualification across every required profile. Missing live approval/evidence leaves release unqualified, not silently waived.

## Steps

1. Locate and scope: resolve the named editing target and mode. If copies are ambiguous, inspect relevant client roots/configuration using `references/compatibility.md` and ask which to edit. Never assume project precedence or search the entire disk. Editing target and loaded target need separate evidence.
2. Inspect and lint: run `uv run --offline --script <base>/scripts/lint_skill.py <skill-dir>` with the selected target contract after approved dependency setup. Record errors/advice and metadata/body/static scenario estimates. Do not copy a static verdict into a behavioral grade.
3. Assess: read relevant dimensions of `references/review-rubric.md`; comprehensive work covers all fourteen. Identify evidence-backed defects and relevant cases. Review-only stops with findings, checks actually run, and unassessed coverage. Do not infer a behavioral failure solely from alternate wording, partial reads, or shared references.
4. Preserve baseline before edits: snapshot/digest the original target outside active skill-discovery trees. For behavioral comparisons use identical prompts, fixtures, provider/model/thinking, tools, permissions, and containment. Read the evaluation sections of `references/authoring-guidelines.md` when designing comparisons.
5. Repair narrowly: read the applicable authoring sections, keep useful examples/contracts/safety reminders, and change only the requested or evidenced defect plus coupled consumers. Prefer clear routing and well-placed gotchas to blanket stronger modals. Do not edit descriptions merely to satisfy a phrase regex.
6. Verify: rerun affected static checks and focused deterministic cases; fix caused failures and repeat until those checks pass. Broader findings require scope approval. Report remaining defects explicitly; a deliberately retained failure is not a pass.
7. Observe only within approved scope: when live evidence is relevant, read `references/tuning-diagnostics.md` for controlled baselines and preflight. Obtain explicit model/cost/time/top-level/nested-run approval and demonstrated isolation/containment first. No approval or missing guarantee means no launch. Targeted iteration need not run unrelated profiles; comprehensive release retains the full matrix. Runner exits: 0 completed capture, 1 failed, 2 blocked, 3 timed out. None alone grades task assertions.
8. Diagnose and retest: use primary evidence and the tuning reference to form an edit hypothesis. If no justified edit follows, report the observation rather than inventing one. Rerun affected comparisons under the same controls only within budget; freeze each revision and keep held-out details out of edit prompts.
9. Report concisely: mode/target, findings or edits, evidence/checks actually run, and remaining coverage. Include scoped rubric statuses when useful; all fourteen for comprehensive assessment. For observed changes, link symptom, primary evidence, edit, and retest result; no mandatory empty table. Label static estimates versus measured runtime cost. If no observation ran, state why and leave behavior unqualified.
