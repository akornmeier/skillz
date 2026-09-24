# Skill authoring review

This review began with 23 skills installed under `~/.agents/skills/`: 13 locally maintained skills and 10 additional global skills. After consolidating the overlapping motion family and adding three more packages, the current repository contains 20 discoverable skills. It compares them with Anthropic's [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices), with emphasis on discoverability, context efficiency, progressive disclosure, portability, safety, deterministic workflows, and evaluation coverage.

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
- [x] Migrated the original 39-case suite from `pi-harness`, merged it with later per-skill coverage, and colocated 74 cases across the 17 packages present at migration time. Shared profiles, run records, and dynamic definition validation now live under `evals/` (222 minimum fresh runs).
- [x] Reworked `diagram-design` for concise discovery, immutable project-local styling, offline assets, accessible SVG, deterministic validation, and provider-neutral evaluation coverage.
- [x] Updated the four remaining packages identified by the follow-up audit: `find-skills`, `karpathy-guidelines`, `shadcn-vue`, and `unslop`.
- [x] Added third-person routing metadata, compatibility boundaries, scoped workflows, and 18 provider-neutral evaluation cases across those four packages.
- [x] Removed inert or harness-specific shadcn-vue frontmatter, replaced assumed command interpolation with explicit context discovery, pinned-version guidance, mutation approval, and verification loops, and linked every long reference directly.
- [x] Completed a read-only audit of the newly added `meta-skill`, `thermo-nuclear-code-quality-review`, and `voyage-embeddings` packages; implementation and repository-schema evaluation migration remain pending.

## Repository-wide findings

### Already working well

- Pi 0.84.3 loads all 20 current skills with zero diagnostics.
- Every skill name satisfies the 64-character lowercase-letter, number, and hyphen rules.
- Every description is below the 1,024-character limit.
- Every `SKILL.md` body is below the recommended 500-line limit.
- No Windows-style paths were found.
- All 20 current skills use standard `<name>/SKILL.md` packaging.
- `bowser`, `d3-viz`, `diagram-design`, `emil-design-eng`, `gauntlet-loop`, `infographic-builder`, `meta-skill`, `planf3`, `shadcn-vue`, `ux-design`, and `voyage-embeddings` use progressive disclosure.

### Highest-priority improvements

1. **Harden `voyage-embeddings` before use.** Its ingest path can disclose full local source and paths, incur paid API and Pinecone writes, and retry permanent failures without a dry run, cost estimate, data-classification gate, or immediate approval.
2. **Resolve the thermo-nuclear review contract.** Define read-only review versus approval-gated repair and document the Pi-specific explicit-only routing fallback before use in other harnesses.
3. **Repair `meta-skill` portability.** Its scanner misses this repository by default and its vendored root-relative web links currently block repository evaluation validation.
4. **Restore and execute the evaluation matrix.** Add repository-schema suites for the three new packages, then run every case across Pi's fast/economical, balanced/default, and highest-reasoning profiles with fresh sessions, equivalent tools, and complete reproducibility records.

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

**Evaluation coverage:** The package suite replaces the dependent historical scenarios with independent create, update, and build fixtures plus reproducibility requirements. Execute them across all configured profiles.

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
5. **Original definitions completed; execution pending:** Preserve the existing 74 cases, add repository-schema coverage for packages introduced later, then run the expanded matrix across Pi's fast/economical, balanced/default, and highest-reasoning profiles. Use fresh sessions with equivalent tools and settings, record provider, model ID, thinking level, Pi version, skill and fixture revisions, and relevant configuration, and test every model intended for production use.

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

The initial audit was read-only. The motion-family consolidation and the four-package follow-up below subsequently implemented the actionable authoring changes.

### Current package metrics

| Skill                 | `SKILL.md` lines | Description chars | Supporting files                       | Status   |
| --------------------- | ---------------: | ----------------: | -------------------------------------- | -------- |
| `find-skills`         |               69 |               261 | Four provider-neutral evaluation cases | Updated  |
| `karpathy-guidelines` |               56 |               291 | Four provider-neutral evaluation cases | Updated  |
| `shadcn-vue`          |              102 |               364 | Seven references and six eval cases    | Updated  |
| `unslop`              |               63 |               324 | Four provider-neutral evaluation cases | Updated  |

### Follow-up status

- The overlapping motion packages were consolidated into the 52-line `emil-design-eng` router with direct references, deterministic package validation, and 20 evaluation cases.
- All four remaining packages now use specific third-person descriptions with what-and-when routing language and compatibility metadata.
- Every current entry file is below 500 lines; all shadcn-vue references over 100 lines have contents sections and direct links from `SKILL.md`.
- `find-skills` now separates ordinary direct help from explicit capability discovery, treats packages as untrusted, and requires inspect, approve, install, and verify steps.
- `shadcn-vue` no longer uses unsupported `user-invocable`, experimental command-pattern frontmatter, inert interpolation, mutable `@latest` examples, or assumed network access. Registry and preset workflows use explicit preview, approval, and verification loops.
- `karpathy-guidelines` now scales ceremony to task risk and permits minimal adjacent changes required to keep the repository valid.
- `unslop` now routes only for requested prose editing and prioritizes semantic, factual, formatting, quotation, legal-text, and exact-string preservation over blanket style bans.
- At completion of that follow-up, Pi 0.84.3 loaded the then-current 17 packages with zero diagnostics and all local Markdown links resolved.
- Those 17 packages own `evals/evals.json`; shared profiles, the run-record schema, and a validator that dynamically discovers packages live under repository-root `evals/`. The three packages added later are audited separately below and do not yet meet that contract.
- Remaining work is behavioral: execute the 74 defined cases across every production model profile and record results. Provenance or license metadata should not be invented where upstream evidence is unavailable.

### Per-skill findings

#### `find-skills` — authoring and safety update complete

**Implemented:** Narrowed routing to explicit discovery or capability-extension intent; added runtime compatibility and pinned-version guidance; replaced popularity-based trust with inspection of package code, dependencies, permissions, license, and provenance; removed global non-interactive installation defaults; and added explicit approval plus post-install verification.

**Evaluation coverage:** Four cases cover a direct-help near miss, read-only candidate search, a malicious package, and global installation without sufficient approval. Execute them across all configured profiles.

#### `karpathy-guidelines` — authoring update complete

**Implemented:** Kept the entry file compact, made routing risk-specific, scaled planning and clarification to task complexity, clarified that project instructions take precedence, and defined when adjacent edits are required rather than unrelated scope.

**Evaluation coverage:** Four cases cover trivial edits, material ambiguity, required call-site changes, and speculative architecture. Execute them against a no-skill baseline across all configured profiles.

#### `shadcn-vue` — authoring and safety update complete

**Implemented:** Replaced harness-specific frontmatter and inert command interpolation with an explicit project-context preflight; added installed-or-approved CLI version resolution and offline fallback; condensed `SKILL.md` into a 102-line router; linked all seven references including MCP; added the missing icons contents section; made MCP names fully qualified; and standardized inspect, preview, approve, mutate, diff, validate, and report loops for registry, component, and preset changes.

**Evaluation coverage:** Six cases cover local offline composition, untrusted registry installation, local-change-preserving updates, destructive preset choices, network failure, and a React routing boundary. Execute them with representative Vite and Nuxt fixtures across all configured profiles.

#### `unslop` — authoring update complete

**Implemented:** Replaced “Must always apply” with explicit prose-editing triggers and negative boundaries; made semantic and protected-span preservation the first quality gate; converted punctuation, voice, and formatting bans into contextual heuristics; and added concrete rewrite and preservation examples.

**Evaluation coverage:** Four cases cover marketing prose, protected technical Markdown, legal-text refusal boundaries, and house-style exceptions. Grade protected-span changes, semantic preservation, and human preference across all configured profiles.

### Recommended implementation order

1. **Completed:** Consolidate the motion family under `emil-design-eng` and add direct progressive routing, validation, and evaluations.
2. **Completed:** Harden package and registry mutation workflows in `find-skills` and `shadcn-vue`.
3. **Completed:** Clarify shadcn-vue portability, remove unsupported frontmatter, eliminate stale mutable-version examples, and add missing reference navigation.
4. **Completed:** Tighten `karpathy-guidelines` scope and make `unslop` preserve meaning and protected text.
5. **Definitions completed; execution pending:** Run every evaluation with fresh sessions across fast/economical, balanced/default, and highest-reasoning profiles.
6. **Evidence pending:** Restore license or provenance metadata only when authoritative upstream evidence is available.

---

## Focused consolidation review: Emil design engineering family

**Implemented:** `emil-design-eng` is now a 52-line router and the sole family skill. Thirteen direct one-level references and workflows cover all approved modes, including the folded `improve` workflow; duplicated absolutes were normalized into requirements, measured constraints, house defaults, preferences, and verification-dependent judgments. The six temporary compatibility aliases were subsequently removed. Consolidated installer entries remain absent from `.skill-lock.json`; 20 provider-neutral eval definitions and deterministic package validation live under the umbrella.

### Requested family

This review treats `emil-design-eng` as the umbrella and evaluates folding these five packages into it:

- `animation-vocabulary`
- `apple-design`
- `find-animation-opportunities`
- `prototype`
- `review-animations`

Together, the six packages contain 1,790 Markdown lines. The current split creates repeated automatic-routing candidates and duplicates motion doctrine: `scale(0)` guidance appears in four packages, reduced-motion guidance in five, the same custom easing in three, and the Raycast keyboard-motion example in three.

### Anthropic-guidance interpretation

The correct goal is **one discoverable router, not one giant skill file**.

- Keep `emil-design-eng/SKILL.md` concise and action-oriented.
- Put durable knowledge and task workflows in directly linked, one-level leaf files.
- Load only the leaf files needed for the selected mode.
- Use one automatic discovery description for the family; do not keep six overlapping descriptions active.
- Do not say the skill “always applies.” Route when motion, interaction behavior, animation quality, or an interactive UI prototype is materially part of the task.
- Preserve explicit boundaries with `ux-design`, static visual design, `d3-viz`, and general code prototyping.
- Test discovery and non-discovery separately from output quality.

### Consolidation verdict by package

| Package                        | Verdict                                                       | Content retained in umbrella                                                                                            | Important boundary                                                                                                                                                                                                               |
| ------------------------------ | ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `animation-vocabulary`         | Fold completely                                               | Focused terminology glossary and short disambiguation behavior                                                          | Naming mode must not load implementation standards.                                                                                                                                                                              |
| `apple-design`                 | Fold completely, then deduplicate                             | Gesture continuity, velocity handoff, momentum, rubber-banding, materials, typography, and platform-inspired principles | Apple-inspired guidance extends shared standards; it does not own all UX or static visual design.                                                                                                                                |
| `find-animation-opportunities` | Fold completely                                               | Read-only opportunity workflow, rejection gate, evidence format, and suggestion cap                                     | Opportunity mode never edits source and must allow “nothing should animate.”                                                                                                                                                     |
| `prototype`                    | Fold UI and interaction prototyping; keep logic explicit-only | UI variants, interaction-state experiments, isolation, cleanup, and promotion boundaries                                | General business-logic or data-shape prototypes should not automatically trigger a design skill. Preserve them only as `/skill:emil-design-eng prototype logic ...` or later split them into a separate `logic-prototype` skill. |
| `review-animations`            | Fold completely                                               | Read-only motion-review workflow, evidence table, severity, verdict, and truthful visual-verification rules             | Review mode reports findings and does not silently implement them.                                                                                                                                                               |
| `emil-design-eng`              | Rewrite as router                                             | Shared craft principles plus build, tune, and debug routing                                                             | Remove the promotional canned greeting and the 679-line manual from the entry file.                                                                                                                                              |

### Proposed package architecture

```text
skills/emil-design-eng/
├── SKILL.md
├── references/
│   ├── motion-principles.md
│   ├── motion-standards.md
│   ├── apple-design.md
│   └── animation-vocabulary.md
├── workflows/
│   ├── apply-motion.md
│   ├── find-opportunities.md
│   ├── review-motion.md
│   └── prototype.md
└── evals/
    └── evals.json
```

Content ownership:

- `motion-principles.md`: purpose, frequency, restraint, spatial continuity, cohesion, and design judgment.
- `motion-standards.md`: canonical durations, easing defaults, springs, performance, accessibility, and verification.
- `apple-design.md`: unique gesture, momentum, material, typography, and platform-inspired guidance without repeating shared standards.
- `animation-vocabulary.md`: glossary only.
- `apply-motion.md`: implementation, tuning, debugging, and browser verification.
- `find-opportunities.md`: read-only search and rejection workflow.
- `review-motion.md`: read-only diff or code review and output contract.
- `prototype.md`: UI/interaction variants by default; logic mode only through explicit invocation.

Every leaf should be linked directly from `SKILL.md` and usable without reading another leaf. A vocabulary lookup should not load Apple guidance; a review should not load the full glossary; an opportunity scan should not preload prototype instructions.

### Discovery design

Recommended umbrella description:

> Design-engineering guidance for UI motion, interaction polish, gesture physics, Apple-style fluid interfaces, animation terminology, motion opportunity audits, animation code reviews, and throwaway interaction prototypes. Use whenever animation or transition behavior is being designed, built, reviewed, debugged, named, or evaluated in UI/UX work, including popovers, drawers, drag/swipe interactions, springs, reduced motion, and perceived performance. Also use when the user asks what should animate or requests an interactive UI prototype. Do not use for static visual styling, general UX research, or unrelated code prototypes unless explicitly invoked.

Recommended modes:

| Intent                                                | Mode                                     | Minimum context                                          |
| ----------------------------------------------------- | ---------------------------------------- | -------------------------------------------------------- |
| Build, fix, tune, or debug motion                     | `apply`                                  | Principles, standards, apply workflow                    |
| Review animation code or a motion diff                | `review`                                 | Standards, review workflow                               |
| Find places where motion would help                   | `opportunities`                          | Principles, opportunity workflow                         |
| Name an animation effect                              | `name`                                   | Vocabulary only                                          |
| Design Apple-style gestures, materials, or typography | `apple`                                  | Apple reference; standards only when implementing motion |
| Explore UI or interaction variants                    | `prototype ui` / `prototype interaction` | Prototype workflow                                       |
| Explore business logic explicitly                     | `prototype logic`                        | Prototype workflow, explicit invocation only             |
| Broad design-engineering advice                       | `advise`                                 | Smallest relevant leaf set                               |

Examples:

```text
/skill:emil-design-eng review this motion diff
/skill:emil-design-eng opportunities src/pages/settings
/skill:emil-design-eng name the iOS overscroll effect
/skill:emil-design-eng prototype ui three onboarding variants
/skill:emil-design-eng prototype logic model undo and redo
```

### Ownership boundaries

- `emil-design-eng` owns motion, interaction craft, animation review, and interaction prototypes.
- `ux-design` owns comprehension, usability, flows, information architecture, and decision load. It may use Emil motion guidance when motion is material.
- Static visual-design skills own color, typography systems, composition, and art direction when interaction is not central.
- `d3-viz` owns data-driven D3 implementation; Emil guidance may supply motion criteria.
- Browser tooling owns execution and visual evidence, not design judgment.
- General parser, API, data-model, or state-machine prototypes should not auto-route to Emil.

This makes the skill broadly useful in design and UX work without turning every design mention into a false-positive trigger.

### Guidance that must be normalized during consolidation

The current family mixes requirements, defaults, preferences, and technical claims. The merged references should label each rule as one of: accessibility requirement, measured technical constraint, house default, craft preference, or visual-test-dependent judgment.

Specifically:

- “Animate only transform and opacity” is a strong default, not a universal law.
- CSS or WAAPI does not automatically guarantee compositor execution.
- `clip-path`, filters, blur, and promoted layers can have real paint, memory, or GPU costs.
- Framer Motion shorthand performance depends on library version, generated transforms, browser, and workload.
- “Never animate keyboard actions” is useful frequency and latency guidance, not a universal accessibility rule.
- Built-in easing being “too weak” is an aesthetic preference, not a technical fact.
- Spring interruption and velocity carry-over depend on the implementation and must be verified.
- Browser-specific media queries and APIs need capability checks and fallbacks.
- Visual quality, reduced-motion behavior, touch feel, and frame performance must not be claimed without actual verification.

### Migration plan

1. Snapshot the six current packages and preserve upstream attribution, license, and source revisions.
2. Build the umbrella leaf structure and deduplicate contradictory guidance.
3. Add umbrella evaluations before removing discovery from the old packages.
4. Compare umbrella routing and output against the current family using fresh sessions.
5. Replace the five subordinate packages with explicit-only compatibility aliases during one transition period. Each alias should route to one umbrella mode and use Pi's `disable-model-invocation: true`.
6. Remove the retired packages from `.skill-lock.json` so an installer update cannot overwrite the locally consolidated versions.
7. Search global and project configuration, prompts, agents, and evals for old names. Migrate the existing three `prototype` cases to umbrella modes.
8. Remove aliases after the transition period and keep migration history in Git rather than discoverable packages.

### Adjacent unresolved collision

`improve-animations` was not in the requested fold list, but it overlaps the proposed umbrella's `apply`, `opportunities`, and review behavior. Leaving it automatically discoverable would preserve the main routing collision. Before implementation, choose one:

1. Fold its audit, planning, reconcile, and execute workflows into `emil-design-eng`; or
2. Keep it as an explicit-only planning/execution alias with `disable-model-invocation: true`.

The first option produces the cleanest ownership model. The second preserves a specialized command while keeping it out of automatic routing.

### Evaluation requirements

At minimum, cover every mode and every boundary across Pi's fast/economical, balanced/default, and highest-reasoning profiles:

- vocabulary lookup and ambiguous terminology;
- build/fix motion with reduced-motion and performance constraints;
- read-only review with clean and defective diffs;
- opportunity search with positive, excessive-motion, and zero-opportunity fixtures;
- Apple-style gesture interruption and velocity handoff;
- UI and interaction prototypes with production isolation and cleanup;
- explicit-only logic prototype behavior;
- negative routing for static visual design, UX flow review, backend code, general logic prototypes, and D3 implementation.

Use fresh sessions and equivalent tooling. Record provider, model ID, thinking level, Pi version, loaded leaf files, total tokens, tool calls, routing outcome, task assertions, unauthorized mutation count, and human visual preference where applicable. The consolidation is successful only if it improves routing precision while reducing loaded context and preserving or improving artifact quality.

### Focused recommendation

Proceed with a single discoverable `emil-design-eng` router. The five subordinate packages and `improve-animations` were folded into the umbrella; their temporary hidden aliases were later removed. Auto-route only UI/interaction prototyping and keep logic prototyping explicit.


---

## Audit of newly added skill packages (2026-08-28)

### Scope and evidence

This read-only package audit covers the three new, untracked skill directories: `meta-skill`, `thermo-nuclear-code-quality-review`, and `voyage-embeddings`. No skill package source was changed.

Evidence:

- Compared every bundled file with Anthropic's [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) supplied for this review, the Agent Skills guidance vendored by `meta-skill`, and current Pi skill-loading behavior.
- Pi `0.84.3` loaded all 20 discoverable packages through `DefaultResourceLoader` with zero diagnostics. Pi's current behavior is lenient: most schema violations warn but still load; malformed skills or declared skills without `description` do not load; unknown fields are ignored; collisions warn and keep the first skill found.
- `meta-skill/scripts/scan.py skills` reported 20 packages, zero broken, 8 flagged, and 12 mechanically clean. Its no-argument invocation from a directory without `.claude/skills` reported zero scanned because it defaults only to Claude Code locations. Scanner flags are evidence, not behavioral grades.
- AST parsing passed for all three bundled Python scripts. No model evaluation, API call, package installation, Pinecone mutation, or paid Voyage request was run.
- Repository evaluation validation currently stops on a web-root link inside `meta-skill`'s vendored docs; additional root-relative and illustrative example links would also need snapshot-aware handling. Even after that blocker, the three packages do not satisfy the repository's current per-skill evaluation contract.
- None of the three packages has installer provenance in `.skill-lock.json` or a declared package license; do not infer either without authoritative upstream evidence.

### Package metrics

| Skill | `SKILL.md` lines | Body lines | Description chars | Supporting files | Priority |
| --- | ---: | ---: | ---: | --- | --- |
| `meta-skill` | 49 | 44 | 545 | 11 files, including vendored docs and legacy `evals.md` | High |
| `thermo-nuclear-code-quality-review` | 192 | 186 | 253 | None | High |
| `voyage-embeddings` | 176 | 171 | 678 | One reference, two scripts, one legacy eval file | Highest |

All three names match their directories, satisfy the portable name grammar, and avoid reserved words. Their descriptions are non-empty, free of XML tags, and below 1,024 characters. Every entry body is below 500 lines, and no Windows-style resource path was found.

### Concise current audit checklist

- **Frontmatter and discovery:** Require frontmatter at line 1, `name` and non-empty `description`; keep name at 64 characters or fewer using lowercase letters, numbers, and single hyphens; match directory name for Agent Skills portability; avoid reserved `anthropic` and `claude`; keep description at 1,024 characters or fewer and free of XML tags. Test both intended activation and near-miss non-activation.
- **Descriptions:** Write in third person. State what the skill does and when it should load using terms users actually type. Put implementation detail in the body, not discovery metadata.
- **Context and references:** Keep `SKILL.md` body under 500 lines. Link every needed reference directly from `SKILL.md`, attach a clear “read it when” condition, avoid nested reference chains, and add a contents section to references over 100 lines. Remove unreachable files and duplicated sources of truth.
- **Workflows and feedback:** Give complex tasks explicit ordered steps and decision points. For quality-critical or mutating work, use inspect/plan → validate → execute → verify, then repair and repeat until the validator passes. Never mark an unexecuted check complete.
- **Scripts, safety, and dependencies:** State whether each script should be executed or read. Document inputs, outputs, exit behavior, dependencies, supported versions, and environment limits. Preflight tools and credentials; inspect untrusted input; require approval immediately before installs, network calls, paid requests, destructive actions, publication, or external data writes; prefer dry runs, atomic output, idempotency, bounded retries, and actionable errors.
- **Portability:** Use relative forward-slash paths and capability checks. Avoid personal absolute paths, assumed home-directory config, missing sibling skills, harness-only tool names, and silent network/package assumptions. Document fallbacks, especially because Claude API Skills have no network access or runtime package installation.
- **Time-sensitive content:** Avoid mutable `latest` guidance, current model/catalog/status/pricing claims, and dated personal decisions in durable instructions. Put legacy behavior in an “old patterns” section; otherwise cite a source/version or require runtime verification before acting.
- **Evaluation coverage:** Create at least three representative evaluations before expanding instructions. Include baseline behavior without the skill, positive discovery, near misses, workflow outcomes, dependency/error paths, and safety boundaries. Run fresh sessions across every production model profile, capture loaded files/tool calls/diffs, and distinguish definitions from recorded run evidence.

### Pi loading and cross-harness notes

- Pi discovers recursive `<name>/SKILL.md` packages in `~/.agents/skills/`, `~/.pi/agent/skills/`, project equivalents, packages, settings, and explicit `--skill` paths. Root `.md` discovery differs by location. `--no-skills` disables discovery, while explicit `--skill` remains additive.
- Pi permits a declared name to differ from its directory, but the Agent Skills standard requires a match. Treat mismatch as a portability finding even when Pi loads it.
- Pi supports optional `license`, `compatibility`, `metadata`, experimental `allowed-tools`, and `disable-model-invocation`. Broad Anthropic Skill surfaces guarantee only `name` and `description`; Claude Code separately supports `allowed-tools`. Unknown fields may be ignored elsewhere, so any behavior that depends on an optional field needs an explicit compatibility note and a safe fallback.
- `disable-model-invocation: true` hides a skill from Pi's model metadata and requires `/skill:name`. Other harnesses may ignore it and auto-discover the skill, reversing the intended routing policy.
- For Pi debugging: run with `--verbose`, confirm the location and valid description, check duplicate names, and use `/skill:name` or explicit `--skill <path>` to separate discovery failure from instruction failure. Restart after package changes because metadata is loaded at startup.

### `meta-skill` — high priority

**Working well:** Valid portable core frontmatter, specific third-person discovery language, a 44-line body, direct one-level routing, focused workflows, and deterministic mechanical scanning.

**Findings:**

- The audit workflow is broken for this repository's global location. Its documented no-argument scan defaults to `~/.claude/skills` and `.claude/skills`; it scanned zero packages here. The workflow also says to pass directories only when the user names them, so it does not recover automatically for `~/.agents/skills`.
- The package claims Claude Code scope and hardcodes Claude locations, `claude doctor`, Claude-only fresh-session commands, and Claude 5 model assumptions without `compatibility` or Pi fallbacks.
- Direct reference depth is good, but `docs/claude_code_agent_skills.md` (603 lines) and `docs/claude_code_agent_skills_overview.md` (311 lines) lack contents sections. Their vendored web-root and illustrative example links are interpreted as broken local links by this repository's validator.
- Vendored guidance and the Claude 5 context reference are dated snapshots. They identify their dates, but authoring decisions can still drift unless the workflow refreshes or compares them with live guidance.
- `evals.md` contains two executable scenarios plus a measurement and historical run notes, not the repository's required `evals/evals.json` contract. Coverage lacks a third independent task, Pi/cross-harness behavior, the global-location scanner failure, current capability profiles, and fresh run records.
- The scanner's trigger regex produces false positives for valid wording such as “Use for” and treats intentional explicit-only routing as an automatic defect. Its output should not be presented as standards validation.

**Recommendation:** Make location discovery capability-based, pass the resolved skills root explicitly, declare supported harnesses, add ToCs or smaller snapshots, make link validation snapshot-aware for vendored web and example links, and migrate at least three cases to the repository evaluation schema with Pi and Claude Code fixtures.

### `thermo-nuclear-code-quality-review` — high priority

**Working well:** Valid matching name, specific trigger terms, no dependencies or references, and a 186-line body below the 500-line guidance.

**Findings:**

- Description opens with imperative “Run” rather than strict third-person “Runs.” More importantly, Pi never exposes that description for automatic discovery because `disable-model-invocation: true` makes the package explicit-only.
- `disable-model-invocation` is a Pi-specific routing dependency. A harness that ignores it may auto-load an intentionally extreme review persona for ordinary maintainability requests.
- Scope says “review,” but instructions say to “go for” ambitious restructuring. No read-only boundary, mutation approval, target/diff selection, repository-policy check, test loop, or output distinction between findings and applied edits exists.
- Repeated absolutes and the fixed 1,000-line blocker consume most of the body without evidence, exception handling, or a feedback mechanism. This risks aggressive over-refactoring and low-value duplication rather than high-conviction review.
- No `evals/evals.json`, baseline, discovery/explicit-invocation test, clean-diff case, false-positive case, behavior-preservation case, or unauthorized-mutation assertion exists.

**Recommendation:** Keep explicit-only intent but document cross-harness fallback, choose review-only versus approval-gated repair, turn the body into a concise evidence-based workflow, require behavior-preserving verification for edits, and add evaluations for clean, structurally poor, justified-large-file, and no-mutation scenarios.

### `voyage-embeddings` — highest priority

**Working well:** Valid matching frontmatter, strong trigger vocabulary, a 171-line body, direct one-level references, explicit document/query asymmetry, parallel migration guidance, stable IDs, bounded batches, and clear script entry points.

**Findings:**

- Portability is undeclared despite hard dependencies on network access, paid Voyage/Pinecone APIs, `voyageai`, `pinecone`, credentials, Pinecone CLI, Claude Code environment loading, Tony-specific config files, and an absent `pinecone-query` sibling skill. Claude API cannot satisfy runtime network or install assumptions.
- `references/models.md` is 141 lines without a contents section. Model generations, support status, dimensions, pricing ranges, storage cost, API behavior, “current index” state, and the dated personal migration decision are time-sensitive. Some claims are internally overbroad, such as saying all models support every output dimension while the same table lists fixed-dimension domain models.
- Upsert sends complete local source text and paths to external services and stores them in Pinecone metadata. The workflow lacks data-classification, repository-sensitivity, cost estimate, redaction, dry-run, and immediate approval gates.
- Dependencies are unpinned and only surfaced by an import failure suggesting global `pip install`. No lock/setup file, supported SDK versions, isolated environment, or API compatibility test exists.
- `embed_and_upsert.py` retries every exception, including permanent and potentially billable failures; does not preflight index dimension/metric; hashes text without source identity, so identical content from different files collides; loads whole files and all records into memory; and has no post-upsert count/sample verification. Migration instructions mention deleting the old index without a dedicated destructive-action gate.
- Three evaluation definitions exist, but they use an obsolete schema (`skill_name`, numeric IDs, `expected_output`) and fail the repository contract (`schema`, `skill`, profiles, setup, expected and forbidden behaviors). They test advice only, with no baseline, near miss, dependency failure, mock API, privacy/cost refusal, retry behavior, model mismatch, or recorded execution.

**Recommendation:** Separate durable provider guidance from Tony-specific migration state, add compatibility and runtime-verification notes, add a ToC, pin/test dependencies, require inspect/estimate/approve before external writes, add dry-run and index preflight/postflight checks, narrow retries, and replace the old eval definitions with mocked safety and workflow cases under the repository schema.

### Priority order

1. Harden `voyage-embeddings` before any real ingest or migration; current path can disclose source and incur paid external writes.
2. Resolve `thermo-nuclear-code-quality-review`'s review-versus-edit contract and explicit-only portability before using it outside Pi.
3. Repair `meta-skill`'s global-root discovery and evaluation-validator integration so future audits produce trustworthy coverage.
4. Run fresh evaluation matrices only after definitions validate; current package presence and syntax checks are not behavioral evidence.
