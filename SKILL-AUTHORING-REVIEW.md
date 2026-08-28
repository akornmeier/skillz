# Skill authoring review

This review covers all 23 skills installed under `~/.agents/skills/`: 13 locally maintained skills and 10 additional global skills. It compares them with Anthropic's [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices), with emphasis on discoverability, context efficiency, progressive disclosure, portability, safety, deterministic workflows, and evaluation coverage.

## Implementation progress

- [x] Generalized evaluation guidance to Pi capability profiles: fast/economical, balanced/default, and highest-reasoning.
- [x] Converted `bowser` and `mental-model` to standard `<name>/SKILL.md` packages.
- [x] Reworked `bowser` discovery metadata, named-session workflow, compatibility guidance, and command reference.
- [x] Narrowed `mental-model` discovery, defined target-file selection, and added a deterministic YAML and line-limit validator.
- [x] Removed hard dependencies on the absent `file-upload` and `diagram-design` skills. Plan F3 now has a self-contained inline-SVG fallback.
- [x] Hardened `elevenlabs-tts` with explicit paid-use approval, safe request encoding, HTTP and MP3 validation, atomic output, and portable playback.
- [x] Added deterministic Plan F3 validation, portable browser guidance, append-only checks, and validation loops across create, update, reference, and build workflows.
- [x] Standardized all audited discovery descriptions in concise third-person language and added portable compatibility metadata where needed.
- [x] Flattened UX and Prototype reference routing, added all identified reference tables of contents, and removed duplicated D3 routing.
- [x] Reduced `infographic-builder/SKILL.md` from 248 to about 100 lines and added strict quality-gate validation.
- [x] Hardened Prototype safety and added a zero-dependency structural SVG validator.
- [x] Added a provider-neutral evaluation suite for all 13 audited skills with 39 self-contained cases, three capability profiles, reproducibility records, and definition validation (117 minimum fresh runs).
- [x] Reworked `diagram-design` for concise discovery, immutable project-local styling, offline assets, accessible SVG, deterministic validation, and provider-neutral evaluation coverage.

## Repository-wide findings

### Already working well

- Pi loads all 13 skills with zero diagnostics.
- Every skill name satisfies the 64-character lowercase-letter, number, and hyphen rules.
- Every description is below the 1,024-character limit.
- Every `SKILL.md` body is below the recommended 500-line limit.
- No Windows-style paths were found.
- All 13 skills use standard `<name>/SKILL.md` packaging.
- `bowser`, `d3-viz`, `gauntlet-loop`, `infographic-builder`, `planf3`, `prototype`, and `ux-design` use progressive disclosure.

### Highest-priority improvements

1. **Execute the evaluation matrix.** Definitions cover all 13 audited skills with three self-contained cases each. Run all 39 cases across Pi's fast/economical, balanced/default, and highest-reasoning profiles with fresh sessions, equivalent tools, and complete reproducibility records.

## Per-skill recommendations

### `babysit-pr` — core update complete

**Implemented:** Third-person discovery metadata, typo fixes, a concise monitoring loop, portable compatibility metadata, and an artifact fallback that does not depend on `file-upload`.

**Evaluation coverage:** Definitions now cover a real finding, a false positive, and an infrastructure failure. Execute them across all configured profiles.

### `bowser` — core update complete

**Implemented:** Standard package layout, third-person discovery metadata, dependency preflight, named-session consistency, corrected workflow numbering, portable compatibility metadata, and a direct `references/commands.md` index.

**Evaluation coverage:** Definitions now cover navigation, form interaction, and parallel sessions. Execute them across all configured profiles.

### `d3-viz` — authoring update complete

**Implemented:** Concise discovery metadata, portable compatibility guidance, direct reference routing without a duplicated index, and a table of contents for the long framework reference.

**Evaluation coverage:** Definitions now cover framework integration, accessible interaction, and dense-data rendering. Execute them across all configured profiles and use the runs to test starter assets against representative projects.

### `diagram-design` — authoring and validation update complete

**Implemented:** Concise third-person discovery metadata with explicit boundaries against `svg-generate`, `d3-viz`, and `infographic-builder`; a 128-line routing-focused entry skill; immutable bundled defaults with project-local `.pi/diagram-design/style-guide.md` precedence; capability-based, approval-gated onboarding; system-font-only offline assets; accessible naming for all 43 inline SVGs; corrected full-template label masks, legend placement, and bounds; an explicit MIT license; and a zero-dependency validator for document structure, SVG accessibility, IDs and references, resource policy, placeholders, simple geometry bounds, gallery links, and exact package inventory.

**Progressive disclosure:** The skill links directly to all type and primitive references, instructs the agent to load only one selected type and variant, and adds contents lists to the long onboarding and default-style references.

**Evaluation coverage:** Definitions now cover standalone architecture discovery with local tokens, complexity-aware swimlane design, and repair of an existing broken diagram. Execute them across all configured profiles, keeping structural validation and browser visual inspection as separate evidence.

### `elevenlabs-tts` — core update complete

**Implemented:** Third-person discovery metadata, compatibility and approval gates, a deterministic generator with safe JSON encoding and API-key handling, HTTP and MP3 validation, atomic output, configurable voice controls, portable playback, and a separate options reference.

**Evaluation coverage:** Definitions now cover local-mock generation, quota errors, and unavailable playback. Execute them across all configured profiles.

### `file-pr` — authoring update complete

**Implemented:** Third-person discovery metadata, portable compatibility guidance, duplicate-PR protection, diff and convention inspection, repository-policy-aware draft handling, and post-creation verification.

**Evaluation coverage:** Definitions now cover an existing PR, an empty or unrelated diff, and repository-specific conventions. Execute them across all configured profiles.

### `gauntlet-loop` — authoring update complete

**Implemented:** Shorter discovery metadata, removal of harness-specific `argument-hint`, a portable project-local run workspace, and a table of contents for the execution protocol.

**Evaluation coverage:** Definitions now cover design mode, faithful run mode, and fallback without isolated agents. Execute them across all configured profiles.

### `infographic-builder` — authoring update complete

**Implemented:** A roughly 100-line entry skill, concise discovery metadata, direct progressive routing, a Higgsfield reference table of contents, and validator `--strict` mode for quality-gated delivery.

**Evaluation coverage:** Definitions now cover planning-only, deterministic local production, and approved hybrid generation. Execute them across all configured profiles.

### `mental-model` — core rewrite complete

**Implemented:** Standard package layout, selective discovery metadata, explicit target-file and line-limit selection, privacy boundaries, and a bundled validator that checks strict YAML, duplicate keys, and line limits. The workflow no longer assumes PyYAML or uses invalid `wc -Z` syntax.

**Evaluation coverage:** Definitions now cover durable updates, consolidation without duplication, and line-limit trimming. Execute them across all configured profiles.

### `planf3` — core portability and validation update complete

**Implemented:** Concise third-person discovery metadata, portable path and browser guidance, explicit optional-image dependencies and approval, a self-contained inline-SVG fallback, and deterministic validation for placeholders, repeat markers, metadata, offline resources, figures, duplicate IDs, required CSS variables, and append-only updates. Every workflow now validates and repairs plan artifacts.

**Evaluation coverage:** The central suite replaces the dependent historical scenarios with independent create, update, and build fixtures plus reproducibility requirements. Execute them across all configured profiles.

### `prototype` — authoring update complete

**Implemented:** Third-person discovery metadata, direct branch routing, a UI reference table of contents, removal of sideways reference chains, context-sensitive testing and error-handling guidance, explicit confirmation for external actions, and cleanup verification.

**Evaluation coverage:** Definitions now cover ambiguous routing, logic prototyping, and UI variant prototyping. Execute them across all configured profiles.

### `svg-generate` — authoring update complete

**Implemented:** Third-person discovery metadata with adjacent-skill boundaries, context-derived output and styling, required accessible text, a structural and visual repair loop, and a zero-dependency XML, reference, and accessibility validator.

**Evaluation coverage:** Definitions now cover architecture diagrams, dense-label repair, and accessibility repair. Execute them across all configured profiles.

### `ux-design` — authoring update complete

**Implemented:** Shorter discovery metadata, direct reference routing without an intermediate index, and tables of contents for both long references.

**Evaluation coverage:** Definitions now cover critique, implementation guidance, and accessibility overriding a heuristic. Execute them across all configured profiles, checking concise output at the highest-reasoning profile and sufficient guidance at the fast/economical profile.

## Recommended implementation order

1. **Completed:** Repair `mental-model`, `bowser`, and missing skill references.
2. **Completed:** Harden `elevenlabs-tts` and the remaining `planf3` paid or executable workflows.
3. **Completed:** Standardize the remaining descriptions; package layout is now standardized.
4. **Completed:** Flatten references and add missing tables of contents.
5. **Definitions completed; execution pending:** Run all 39 cases across Pi's supported model profiles: fast/economical, balanced/default, and highest-reasoning. Use fresh sessions with equivalent tools and settings, record the actual provider, model ID, thinking level, Pi version, and relevant configuration, and test every model intended for production use.

---

## Audit of ten additional global skills (2026-08-28)

### Scope and evidence

This read-only pass covers the ten installed packages not included in the original 13-skill review:

- `animation-vocabulary`
- `apple-design`
- `emil-design-eng`
- `find-animation-opportunities`
- `find-skills`
- `improve-animations`
- `karpathy-guidelines`
- `review-animations`
- `shadcn-vue`
- `unslop`

Evidence collected locally:

- Read every file in all ten packages.
- Loaded the complete `~/.agents/skills/` collection with Pi `0.84.3`: 23 skills, zero diagnostics.
- Checked package names, directory-name matches, frontmatter fields, description lengths, Markdown links, file inventories, line counts, reference tables of contents, and Windows-style paths.
- Confirmed all ten names match their directories, all descriptions are under 1,024 characters, every local Markdown link resolves, and no Windows-style resource paths are present.
- Findings below do not rely on model evaluations, network-dependent commands, package installs, or mutating skill workflows.
- A strict cross-harness `agentskills` validator is not installed locally. Cross-harness findings below are schema reviews, not claimed validator runs.

No file inside these ten skill packages was changed.

### Package metrics

| Skill | `SKILL.md` lines | Description chars | Supporting files | Priority |
| --- | ---: | ---: | --- | --- |
| `animation-vocabulary` | 173 | 424 | None | Medium |
| `apple-design` | 282 | 425 | None | High |
| `emil-design-eng` | 679 | 155 | None | Highest |
| `find-animation-opportunities` | 132 | 358 | None | Medium |
| `find-skills` | 142 | 303 | None | High |
| `improve-animations` | 101 | 447 | `AUDIT.md`, `PLAN-TEMPLATE.md` | High |
| `karpathy-guidelines` | 67 | 219 | None | Low |
| `review-animations` | 112 | 159 | `STANDARDS.md` | High |
| `shadcn-vue` | 231 | 393 | Seven Markdown references | High |
| `unslop` | 80 | 49 | None | High |

### Repository-wide findings

#### Working well

- All ten packages use the standard `<name>/SKILL.md` layout and load in Pi without diagnostics.
- Names, directory matches, description lengths, and local links are valid.
- `find-animation-opportunities`, `improve-animations`, and `review-animations` distinguish discovery, planning, and review better than most overlapping skill families.
- `improve-animations`, `review-animations`, and `shadcn-vue` use direct supporting references for their main workflows.
- `find-animation-opportunities` and `improve-animations` explicitly treat repository content as untrusted data.
- `shadcn-vue` requires confirmation before overwrite and asks for diff review when updating installed components.

#### Main gaps

1. **No behavioral evaluation coverage.** None of these ten packages includes durable cases, fixtures, grading records, or run evidence. Adding three cases per skill would add 30 cases and 90 minimum profile runs, taking the complete collection to 69 cases and 207 minimum runs.
2. **Motion-skill routing overlap is high.** `apple-design`, `emil-design-eng`, `find-animation-opportunities`, `improve-animations`, and `review-animations` share motion, animation, review, and implementation language. There is no routing confusion matrix or negative-case evidence.
3. **Progressive disclosure is uneven.** `emil-design-eng` is 679 lines and exceeds the recommended 500-line entry-file ceiling. `apple-design` and `animation-vocabulary` also keep reusable catalogs in the entry file.
4. **Motion doctrine is duplicated.** Exact durations, easing curves, frequency rules, and broad “never” claims recur across four packages, creating drift and making evidence hard to update consistently.
5. **Portability metadata is missing.** None of the ten declares `compatibility`, despite network, Node/package-runner, browser, subagent, worktree, or harness-specific assumptions.
6. **Two packages use harness-specific frontmatter.** `review-animations` uses Pi's `disable-model-invocation`; `shadcn-vue` uses unsupported `user-invocable` plus experimental `allowed-tools` with Claude-style `Bash(...)` patterns. These choices need explicit portability documentation.
7. **Safety gates need strengthening.** `find-skills` recommends global non-interactive installation; `shadcn-vue` can fetch registries and mutate projects. Both should require capability checks, package/content inspection, explicit approval immediately before mutation, and post-action verification.
8. **Long references need navigation.** `improve-animations/AUDIT.md` is 116 lines, `review-animations/STANDARDS.md` is 188 lines, and `shadcn-vue/rules/icons.md` is 111 lines; none has a contents section. Other long `shadcn-vue` references already do.
9. **Provenance is incomplete.** Eight packages retain installer provenance in `.skill-lock.json`; `karpathy-guidelines` and `unslop` do not. Only `karpathy-guidelines` declares a license in frontmatter.
10. **Time-sensitive claims are embedded.** Install counts, download counts, leaderboards, mutable `@latest` commands, and dated platform guidance can become stale without a source version or verification step.

### Per-skill findings

#### `animation-vocabulary`

**Working well:** Precise reverse-lookup trigger, clear non-goal, bounded answer format, and no execution risk.

**Findings:** The entire 173-line glossary loads for each lookup. Its “mirrored snapshot” claim names an unavailable project `/vocabulary` page but records no source revision or synchronization check.

**Recommendation:** Before splitting, compare the current monolith with a short router plus glossary reference. Evaluate ambiguous pairs, out-of-glossary requests, top-1 accuracy, acceptable-alternate recall, invented-term rate, and token cost.

#### `apple-design`

**Working well:** Concrete interaction guidance, accessibility coverage, and useful web translations of platform design concepts.

**Findings:** The 282-line entry file spans gestures, springs, materials, typography, accessibility, and general design foundations, causing overlap with motion skills and `ux-design`. It contains dated and platform-specific claims without bundled sources or compatibility notes. Some absolute implementation advice needs browser and library qualification.

**Recommendation:** Split durable theory from task routing only after traces show which sections are used. Add separate gesture, reduced-motion, typography, and general-review cases, including negative routing against `ux-design` and the motion-review skills.

#### `emil-design-eng`

**Working well:** Numerous concrete examples, an explicit review format, and substantial edge-case coverage.

**Findings:** At 679 lines and 27.3 KB, this is the clearest progressive-disclosure problem. The description says what knowledge it contains but not when it should load. A canned first response delays work and promotes an external course. Large sections duplicate the animation audit and review packages. No license, source revision, compatibility contract, or eval evidence is included.

**Recommendation:** Make this the first refactor target: create a concise router, move focused topics into one-level references, remove the canned greeting, state routing boundaries, and test against general UI, animation implementation, and code-review prompts.

#### `find-animation-opportunities`

**Working well:** Strong routing boundaries, explicit read-only behavior, output cap, rejected-candidate requirement, and an untrusted-content rule.

**Findings:** It duplicates exact motion doctrine instead of routing to one maintained source. “Whole app” completion lacks a concrete coverage record. Its handoff to `improve-animations` crosses from read-only discovery into a workflow that writes plans.

**Recommendation:** Add fixtures with too little, appropriate, and excessive motion, plus a zero-opportunity case. Grade suggestion precision, rejection quality, source citation accuracy, cap compliance, and unauthorized mutation count.

#### `find-skills`

**Working well:** Practical search flow and a quality-check step before recommendation.

**Findings:** The description can capture broad “how do I” questions that Pi can answer directly. Popularity and stars are treated as trust proxies. The global `npx skills add ... -g -y` step lacks an immediate approval and package-inspection gate. Node, network, GitHub, and package-runner requirements are undeclared.

**Recommendation:** Narrow discovery to explicit skill-search or capability-extension intent. Require inspection of `SKILL.md`, scripts, assets, license, provenance, network behavior, and tool permissions before recommendation or installation. Evaluate direct-help false positives, no-result behavior, malicious packages, and install requests without approval.

#### `improve-animations`

**Working well:** Concise entry file, direct references, source-code protection, phased workflow, evidence requirements, and clear separation from single-diff review.

**Findings:** “Read-only” applies only to source code because the skill writes plan files, and `execute` delegates mutations. Subagents and isolated worktrees are harness capabilities without compatibility or fallback guidance. `AUDIT.md` needs a contents section. Plan numbering, stale commit checks, and plan-index consistency are prose-only.

**Recommendation:** Clarify artifact-writing and execution boundaries in discovery metadata. Add capability fallbacks and deterministic plan validation. Evaluate audit-only, plan creation, no-subagent fallback, stale-plan reconciliation, and approval before execution.

#### `karpathy-guidelines`

**Working well:** Small, licensed, self-contained, third-person description, explicit tradeoff, and no unnecessary references.

**Findings:** Its scope covers most coding work, so routing may overlap nearly every implementation skill. Subjective caution rules lack examples of legitimate exceptions beyond the opening tradeoff.

**Recommendation:** Keep the package compact. Evaluate trivial fixes, ambiguous requirements, hidden scope traps, and required adjacent changes. Measure unrelated edits, requirement coverage, clarification churn, solution size, and task success against a no-skill baseline.

#### `review-animations`

**Working well:** Focused review scope, direct standards reference, evidence-oriented verdict format, and deliberate manual invocation in Pi.

**Findings:** `disable-model-invocation` is Pi-specific and should be documented as a portability choice. `STANDARDS.md` needs a contents section. Standards duplicate other motion packages and rely on broad technical absolutes. The package should state its no-modification boundary more directly.

**Recommendation:** Verify manual `/skill:review-animations` behavior in Pi and define behavior for other intended harnesses. Evaluate clean diffs, subtle regressions, non-motion diffs, and intentional exceptions; grade precision, severity agreement, citation accuracy, and refusal correctness.

#### `shadcn-vue`

**Working well:** Specific ecosystem routing, project-context awareness, direct references, substantial examples, diff-first updates, overwrite confirmation, and registry import checks.

**Findings:** Pi ignores `user-invocable`, so the field does not enforce its apparent intent. `allowed-tools` is experimental and uses harness-specific command patterns. Claude-style ``!`...` `` interpolation in “Current Project Context” is inert in Pi, yet later instructions assume injected JSON. Network, Node, package runner, mutable `@latest`, and registry requirements are undeclared. `mcp.md` is orphaned from `SKILL.md`; `rules/icons.md` needs a contents section. Mutating CLI operations need a single explicit approval policy.

**Recommendation:** Replace assumed interpolation with an explicit capability-checked context command, document supported runners and offline behavior, link or remove `mcp.md`, and define preview/approval/verify steps for every mutation. Test Vite/Nuxt, package runners, aliases, Tailwind versions, icon libraries, existing-component merges, preset refusal, registry ambiguity, and offline failure using pinned CLI versions in eval records.

#### `unslop`

**Working well:** Small, self-contained, and free of runtime dependencies or side effects.

**Findings:** The 49-character description says “Must always apply” instead of defining a routing condition. Blanket punctuation and style bans can damage quoted text, legal copy, code-adjacent prose, house style, accessibility text, or explicit preservation requests. No examples demonstrate semantic or protected-span preservation.

**Recommendation:** Narrow routing to explicit prose-editing requests and make preservation constraints primary. Evaluate marketing copy, technical docs, terse chat, quotations, legal text, Markdown, exact strings, and “do not rewrite” cases. Grade semantic preservation, unwanted-edit rate, protected-span changes, and human preference.

### Recommended implementation order

1. Add provider-neutral routing and boundary eval definitions for all ten skills: three cases each across fast/economical, balanced/default, and highest-reasoning profiles.
2. Harden approval and package-inspection workflows in `find-skills` and `shadcn-vue` before using their mutating paths.
3. Refactor `emil-design-eng` for progressive disclosure, then measure whether `apple-design` and `animation-vocabulary` benefit from similar splits.
4. Clarify Pi-only and cross-harness behavior in `review-animations` and `shadcn-vue`.
5. Add missing reference contents sections and deterministic validation for animation plans.
6. Consolidate duplicated motion doctrine only after evaluations identify which shared rules improve outcomes.
7. Add or restore provenance and license metadata for globally tracked third-party packages.
