# Animation implementation plan template

Load only when umbrella `improve plan` writes or validates a plan.

## Contents

- [Required structure](#required-structure)
- [Plan template](#plan-template)
- [Plan-set index](#plan-set-index)

## Required structure

Every plan needs:

1. Imperative title and metadata: status, source commit, severity, category, and estimated scope.
2. Problem statement with exact `file:line` locations and current code quoted verbatim.
3. Target state with exact code, values, and required media queries.
4. Existing repository conventions and one exemplar.
5. Ordered edit steps.
6. Boundaries, prohibited changes, and a stop-on-drift rule.
7. Mechanical checks, observable feel checks, reduced-motion checks, and an exact done condition.

## Plan template

````markdown
# NNN — <Imperative title>

- **Status**: TODO
- **Commit**: <current short commit>
- **Severity**: HIGH | MEDIUM | LOW
- **Category**: <motion category>
- **Estimated scope**: <files and rough size>

## Problem

Explain the observed problem and why it matters. Cite each location and quote current code:

```css
/* src/components/dropdown.css:14 — current */
.dropdown { transition: all 400ms ease-in; }
```

## Target

State the exact result. Use project tokens or label house values as starting points:

```css
.dropdown {
  transition: transform 200ms var(--ease-out), opacity 200ms var(--ease-out);
  transform-origin: var(--radix-dropdown-menu-content-transform-origin);
}
```

## Repository conventions

- Name the token, primitive, and file-placement conventions.
- Cite one existing `file:line` exemplar.

## Steps

1. <One concrete edit with file and resulting behavior.>
2. <Next edit.>

## Boundaries

- Do not touch <out-of-scope files or behavior>.
- Do not add dependencies unless separately approved.
- If current code differs from the quoted commit, stop and report drift.

## Verification

- **Mechanical**: <commands and expected results>.
- **Browser**: <interaction and observable behavior, or `not run`>.
- **Reduced motion**: <expected alternative, or `not run`>.
- **Performance/device**: <trace or hardware check when material, otherwise `not run`>.
- **Done when**: <objective completion condition>.
````

## Plan-set index

Maintain `plans/README.md` with plan number, title, severity, status, execution order, dependencies, and source commit. Numbers must be unique and monotonic. A completed plan is not proof of implementation; verify the target code and checks before marking it done.
