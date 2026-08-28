# Skill authoring review

This review compares the 13 locally maintained skills installed under `~/.agents/skills/` with Anthropic's [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices). It focuses on discoverability, context efficiency, progressive disclosure, deterministic workflows, and evaluation coverage.

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
