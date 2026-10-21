# Compatibility and authority

Reviewed 2026-10-19. Separate portable format, named client behavior, repository policy, and authoring heuristics. A client accepting a file does not prove portability, discovery, or safe execution.

## Portable format

Source: [Agent Skills specification](https://agentskills.io/specification).

| Field | Portable contract |
| --- | --- |
| `name` | Required string, 1–64 characters, lowercase Unicode alphanumerics and single hyphens; no leading/trailing hyphen; matches directory name. ASCII names are easiest across clients. |
| `description` | Required non-empty string, at most 1,024 characters. Describe capability, intent, and boundaries; no required trigger phrase or grammatical person. |
| `license` | Optional string identifying license or bundled license text. Do not invent a license. |
| `compatibility` | Optional environment-requirements string, 1–500 characters. |
| `metadata` | Optional string-to-string map; quote numbers and boolean-like values. |
| `allowed-tools` | Experimental space-separated string. Support and permission effects are client-specific, not a portable sandbox. |

Start YAML on line 1 with `---`, close it on its own line, then write Markdown instructions. Duplicate explicit keys are rejected by this linter to avoid ambiguous contracts. YAML quotes, folded/literal blocks, Unicode content, CRLF, and safe merges are supported; unsafe tags are not.

Keep instructions below 500 lines/about 5,000 tokens as a **recommendation**, not format validity. The 150-line router and 100-line Contents thresholds are **house/navigation heuristics**. Third-person descriptions are an Anthropic/house preference, not a universal format requirement. Anthropic authoring guidance reserves `anthropic`/`claude` name substrings and XML tags in descriptions; portable validation reports compatibility advice, while `--target claude-code` selects those additional authoring constraints.

Source: [Anthropic authoring guidance](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices). The linter is not a full emulator of permissive client loaders or every extension schema.

## Pi 1.3.0

Sources: installed Pi `docs/skills.md`, `docs/cli.md`, `docs/configuration.md`, `docs/settings.md`, `docs/packages.md`; published [skills documentation](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/skills.md).

- Conventional user roots include `~/.agents/skills/` and `<agent-dir>/skills/` (default `~/.pi/agent/skills/`). Project roots include `.agents/skills/` and `.pi/skills/`. Project `.agents/skills/` discovery walks ancestors to the repository root; project `.pi` resources depend on trust. Packages, settings, explicit paths, and custom agent directories add more sources.
- Recursive `SKILL.md` discovery means fixture packages must live outside an active skills tree. On name collision Pi keeps the first discovered skill and warns. Do not infer project precedence from filesystem location; inspect startup diagnostics and the actual loaded path/digest.
- Pi tolerates some invalid fields and directory/name mismatches; malformed declared skills or absent descriptions may not load. Portable checks remain stricter.
- `disable-model-invocation: true` hides metadata from automatic selection; `/skill:name` explicitly injects instructions. `--skill <path>` registers a skill resource, not necessarily a forced body load. `--no-skills` disables ordinary discovery but explicit paths still load. Check installed semantics before designing a discovery experiment.
- Pi's loader does not enforce `allowed-tools` as a security boundary. Tool selection, codemode/MCP reach, filesystem permissions, external containment, and model-call authorization need separate inspection. Disabling built-in shell tools alone does not prove all side effects are blocked.

## Claude Code

Source: [Claude Code skills](https://code.claude.com/docs/en/skills), especially locations, collision resolution, frontmatter, and tool permissions. Verify the installed version; this source describes evolving behavior, not live qualification here.

- Personal skills use `~/.claude/skills/`; project skills use `.claude/skills/`, with parent/nested discovery and additional plugin/enterprise/synced sources.
- Documented same-name precedence among ordinary locations is enterprise, then personal, then project. Nested/plugin/synced variants have additional rules. A project copy does **not** universally win. Confirm the loaded file; renaming a test copy changes the experiment rather than proving identity.
- Extensions include `disable-model-invocation`, `user-invocable`, `argument-hint`, `arguments`, `when_to_use`, `model`, `effort`, `context`, `agent`, `background`, `hooks`, `paths`, `shell`, and `disallowed-tools`. Other clients may ignore them; uploads and packaging may reject fields accepted by Claude Code.
- `disable-model-invocation: true` disables automatic selection. `user-invocable: false` controls direct user invocation. These are routing controls, not authorization for shell/network/model calls.
- `allowed-tools` accepts space/comma-separated strings or YAML string lists. It pre-approves listed tools for the invoking turn; it is **not an allowlist denying every other tool**. Other tools remain governed by permission rules. Managed policy can suppress grants. Never recommend permission bypass to make an eval pass.
- Malformed YAML may leave a body invocable with empty metadata in Claude Code. A lenient load is not successful portable validation or automatic discovery evidence.

## This repository and installation

- This installation keeps shared global source in `~/.agents/skills/`, exposed to Claude Code through a `~/.claude/skills` symlink. That is local setup, not a standard every client implements. Never create/change that link or another installed copy without approval.
- Locate the intended **editing target** separately from the **loaded target**. Resolve supplied paths first; otherwise inspect relevant conventional/configured roots and ask if copies are ambiguous. Do not search the whole disk or assume project precedence.
- Repository release policy: schema-1 `evals/evals.json`, at least three execution cases, all three `requiredProfiles`, and evidence for every expected/forbidden behavior. This is not the Agent Skills format. Static files do not prove they were authored first or that evaluations ran.
- Keep a portable core by default. Declare client-only syntax/features, intended runtime, limitations, and a safe fallback when a client ignores them. Permit shared references and short safety reminders when they help; selective reads are valid if essential information was delivered.

## Script runtime and commands

Resolve `<base>` to this skill's absolute directory, not the process working directory. Supply the intended `<skill-dir>` explicitly for narrow checks.

The linter requires Python 3.9+, uv, and pinned PyYAML 6.0.3. With operator approval, bootstrap once:

```bash
uv run --script <base>/scripts/lint_skill.py --help
```

Then verify without downloads:

```bash
uv run --offline --script <base>/scripts/lint_skill.py <skill-dir> --target portable
```

`--target pi|claude-code` adds supported named client checks, not discovery permissions. JSON findings include authority. Exit 1 means selected format/local-contract errors; exit 0 can still include advice and proves neither task success nor behavioral qualification. Metadata/body and route figures are **static byte/4 estimates**, not actual context use or quality scores. Missing dependency cache blocks offline setup; never silently use an old parser.

Run capture/trace with Python 3 standard library; runner process groups and budget locks require POSIX. Execute scripts normally; inspect source when debugging, auditing security, or changing their interfaces. A named MCP tool must use the actual fully qualified name exposed by the client, not an assumed universal spelling.

Runner requires explicit human approval plus `--allow-live`; the flag cannot enforce human authorization. Fresh context, copied files, isolated discovery, and external security containment are independent. The current runner has no verified discovery/containment adapter: `--qualification`, `--require-skill-isolation`, and `--require-containment` block. Its ordinary capture path is not a qualification workaround. A missing guarantee remains blocked, never a sandbox claim.
