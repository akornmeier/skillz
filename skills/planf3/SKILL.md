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

  For updates, preserve a temporary pre-edit copy and add `--previous <copy>` to check append-only metadata.

## Route to one workflow

Read only the matching workflow before acting:

| Workflow | Use when | File |
| --- | --- | --- |
| Create Plan | Planning or designing new work without a referenced plan | `workflows/create-plan.md` |
| Update Plan | Revising the content of an existing plan | `workflows/update-plan.md` |
| Update References | Refreshing metadata or back/forward references | `workflows/update-references.md` |
| Build Plan | Implementing an existing plan | `workflows/build-plan.md` |

`workflows/image-generation.md` is a subworkflow used only when figures must be created or updated.

## Resources

- `templates/plan.html` — read when creating a plan; update workflows edit the existing artifact instead.
- `scripts/validate_plan.py` — execute after every plan mutation and before build execution; do not read it for instructions.
- `scripts/generate_gpt_image.py` and `scripts/edit_gpt_image.py` — execute only through the image subworkflow after its approval gate.
- `workflows/*.md` — read only the routed workflow and any subworkflow it explicitly calls.
