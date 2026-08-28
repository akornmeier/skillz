# Project Style Onboarding

Create project-local diagram tokens without modifying the installed skill.

## Contents

- [Target and precedence](#target-and-precedence)
- [Choose an onboarding mode](#choose-an-onboarding-mode)
- [Website-derived tokens](#website-derived-tokens)
- [Validate the proposal](#validate-the-proposal)
- [Write atomically](#write-atomically)
- [Project style format](#project-style-format)
- [Failure handling](#failure-handling)

## Target and precedence

Persistent configuration belongs at:

```text
.pi/diagram-design/style-guide.md
```

Never write project branding into the installed package at `~/.agents/skills/diagram-design/`. Apply explicit current-request tokens first, then project-local tokens, then bundled defaults. Do not persist a current-request override unless the user asks.

## Choose an onboarding mode

When the project file is absent, ask the user to choose:

1. **Website-derived:** inspect an approved website and propose tokens.
2. **Pasted tokens:** map user-provided colors and font stacks.
3. **Accepted defaults:** copy the bundled defaults into the project file with `status: accepted-default`.

Website inspection requires explicit network approval. Do not install browser or scraping tools. Use whatever existing browser or HTTP capability can inspect rendered CSS; if none exists, request pasted tokens or use accepted defaults.

## Website-derived tokens

Inspect only approved pages. One representative page is usually enough; sample additional product or documentation pages only when the first page does not expose the visual system.

Prefer rendered CSS custom properties. Otherwise inspect computed styles and a screenshot:

- dominant page background → `paper`;
- primary text → `ink`;
- secondary text → `muted`;
- most intentional focal or action color → `accent`;
- card or elevated surface → `paper-2`;
- border color → `rule`;
- external-link or protocol color → `link`.

Read font stacks from headings, body text, and code. Preserve complete system fallbacks. Do not download or embed web fonts.

Record source URL and access date. Mark uncertain mappings and ask for confirmation rather than guessing.

## Validate the proposal

Before writing:

- verify `ink` and body-sized `muted` text meet WCAG AA on `paper`;
- verify dark tokens have sufficient contrast independently rather than relying on mechanical inversion;
- ensure accent remains distinguishable but is not used as the only status signal;
- keep one accent and demote extra brand colors to secondary roles or omit them;
- preserve complete sans, serif, and mono fallback stacks;
- preview the exact proposed file and obtain approval.

If the source site uses pure white, dark-first design, paid fonts, or imagery instead of a usable token system, preserve the source faithfully when accessibility allows or ask the user which adaptation they prefer. Do not silently impose the bundled aesthetic.

## Write atomically

After approval:

1. Create `.pi/diagram-design/` if needed.
2. Write the complete content to a sibling temporary file.
3. Validate frontmatter status and required token rows.
4. Rename the temporary file to `style-guide.md` atomically.
5. Generate one representative diagram and inspect both intended theme and system-font fallback.

Do not rewrite bundled examples as part of onboarding.

## Project style format

```markdown
---
schema: 1
status: customized
source: https://example.com
accessed: YYYY-MM-DD
---

# Diagram Design Style Guide

## Light tokens
| Role | Value |
|---|---|
| paper | `#f8f6f0` |
| paper-2 | `#ffffff` |
| ink | `#111111` |
| muted | `#66645f` |
| soft | `#817e77` |
| rule | `rgba(17,17,17,0.12)` |
| rule-solid | `#d7d3cb` |
| accent | `#c73a2b` |
| accent-tint | `rgba(199,58,43,0.08)` |
| link | `#245da8` |

## Dark tokens
[Define the same roles for the dark theme.]

## Font stacks
- sans: `system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`
- serif: `ui-serif, Georgia, Cambria, "Times New Roman", serif`
- mono: `ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`
```

Use `status: accepted-default` and `source: bundled-default` when freezing bundled defaults for the project.

## Failure handling

- No network approval or browser capability: accept pasted tokens or defaults.
- Inaccessible or image-only site: ask for a design-token file or a text-heavy approved page.
- Unreplicable paid font: retain its name only when licensed and always provide system fallbacks.
- Ambiguous palette: present candidates and confidence; do not choose silently.
- Failed contrast: propose an adjusted value and show both original and adjusted values before writing.
