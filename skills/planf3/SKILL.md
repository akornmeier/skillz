---
name: planf3
description: Creates, updates, and executes offline HTML implementation plans in specs/. Use when planning work, revising a saved plan, refreshing plan references, or implementing an existing plan.
compatibility: Requires Python 3 and a browser for optional visual inspection. Optional generated images require uv, network access, OPENAI_API_KEY, and explicit approval for potentially paid API use.
metadata:
  category: implementation-planning
---

# Plan F3

A plan is an offline, locally complete HTML package in `specs/`. The main page carries its styling and inline diagrams; generated raster images may live under `specs/<plan-name>/`.

## Inputs and paths

- `RAW_ARGS`: arguments supplied with the skill invocation.
- `USER_PROMPT`: `RAW_ARGS` without `--questionable`, trimmed.
- `QUESTIONABLE`: true when `RAW_ARGS` contains `--questionable`.
- `PLAN_OUTPUT_DIRECTORY`: `specs/`.
- `PLAN_FILE`: `specs/<descriptive-kebab-name>.html`.
- `IMAGES_OUTPUT_DIR`: `specs/<plan-name>/`.
- `TEMPLATE`: `<skill-directory>/templates/plan.html`.
- `AI_DOCS/` and `APP_DOCS/`: read only when present.

Resolve every relative skill path against the directory containing this `SKILL.md`, regardless of the current working directory. If no `USER_PROMPT` is available, ask for it.

## Before you write

Read the task and the code it touches. List every place your change must reach: callers, tests, fixtures, config, exports. Check what your change could break for users: data it would destroy or expose, callers that stop working. That is scope. Extra features are not.

## The smallest complete change

Take the first option that fully works:

1. Does it need to exist? Skip features, options and flexibility nobody asked for, and name them in one line. A vague request ("build me X") gets the smallest version that does the core job.
2. Already in this codebase (a helper, component, service, pattern)? Use it the way the surrounding code does.
3. Standard library or a platform feature? Use it, unless the project has its own. A house component beats a native widget.
4. An installed dependency? Use it. Never add a dependency for a few lines.
5. Can it be one line a reader gets at a glance? One line.
6. Otherwise: the minimum code that works.

- Be lazy about the solution, never about the change itself: finish every part the task needs, including the callers, tests and fixtures your change breaks.
- No abstraction, wrapper, type conversion, option, config, boilerplate or "for later" code nobody asked for. Keep values in the form the platform already gives you. Deletion beats addition. Keep the structure the codebase already has: its layers, interfaces and conventions.
- The shortest working diff wins, once you know everything it must touch. A one-liner that needs decoding is not short.
- Comment only the why the code cannot show, in one line.
- Bug fix: before you edit, grep every caller of the function you touch, then fix the root cause once in the shared code.
- Code you move or merge keeps its error handling and validation.
- Between options of equal size, take the one that is correct on edge cases.
- Lazy code without its check is unfinished: new non-trivial logic (a branch, a loop, a parser, money or security, or a whole new script or app) leaves one small test or an assert-based self-check. Trivial changes need none.
- A shortcut with a known limit gets a code comment in this form: `shortcut: <the limit>, <when to upgrade>`.

Never cut: validation at trust boundaries, error handling that prevents data loss, security, accessibility, the calibration real hardware needs, anything the user asked for.

## Contracts

- Author new plans from `TEMPLATE`. Read it fully, replace every `{{...}}` placeholder, duplicate repeat blocks as needed, and remove all template markers.
- Keep exactly one `<style>` block and no remote stylesheets, fonts, scripts, frames, or embedded objects. Local raster sidecars must remain beneath the plan directory.
- Preserve the template's required `:root` variable names and retune their values per plan.
- Treat every metadata field except `created` as append-only. Never change `created` after creation.
- Include the Questionables section only when `QUESTIONABLE` is true.
- Match plan depth to the requested work. Do not pad sections or silently widen scope.
- Validate every saved plan with the bundled validator and repair failures before opening or executing it:

  ```bash
  python3 <skill-directory>/scripts/validate_plan.py <plan.html>
  ```

  For updates, preserve a temporary pre-edit copy and add `--previous <copy>` to check append-only metadata. Structural success checks format and references, not semantic correctness or whether tests ran.

## Route to one workflow

Read only the matching workflow before acting:

| Workflow          | Use when                                                 | File                             |
| ----------------- | -------------------------------------------------------- | -------------------------------- |
| Create Plan       | Planning or designing new work without a referenced plan | `workflows/create-plan.md`       |
| Update Plan       | Revising the content of an existing plan                 | `workflows/update-plan.md`       |
| Update References | Refreshing metadata or back/forward references           | `workflows/update-references.md` |
| Build Plan        | Implementing an existing plan                            | `workflows/build-plan.md`        |

`workflows/image-generation.md` is a subworkflow used only when figures must be created or updated.

## Resources

- `templates/plan.html` — read when creating a plan or explicitly upgrading an older plan's format; ordinary updates edit the existing artifact instead.
- `references/engineering-review.md` — read when creating or updating plan content, or when a build deviation changes tasks, interfaces, or verification.
- `scripts/validate_plan.py` — execute after every plan mutation and before build execution; do not read it for instructions.
- `scripts/generate_gpt_image.py` and `scripts/edit_gpt_image.py` — execute only through the image subworkflow after its approval gate.
- `workflows/*.md` — read only the routed workflow and any subworkflow it explicitly calls.
