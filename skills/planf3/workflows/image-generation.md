# Image Generation

Fill or update the embedded images in an existing plan `.html` file.

## Choose the backend first

- **`gpt-image`:** use only when `OPENAI_API_KEY` is available **and** the user has approved external, potentially paid image generation for this task. Then follow the script workflow below.
- **`inline-svg` (default):** create one simple accessible inline SVG per useful `{{...IMAGE` slot. Replace the placeholder comment with the `<svg>` element and keep its `<figure>` and `<figcaption>`. Do not create PNGs or `IMAGES_OUTPUT_DIR`.

For `inline-svg`:

- Reference the plan's custom properties, such as `fill="var(--accent)"` and `stroke="var(--ink)"`, instead of hard-coded colors.
- Confirm that `--bg`, `--ink`, `--muted`, `--soft`, `--accent`, and `--accent-tint` exist in `:root` before using them.
- Include an accessible `<title>` and `<desc>` in every SVG.
- Keep the page self-contained: no font links, external scripts, or external stylesheets. Use fallback font stacks.
- If a figure would add decoration rather than understanding, remove the unused figure instead of generating filler.

Pick the sub-workflow based on the incoming `USER_PROMPT`:

| Sub-workflow | When to call it |
| --- | --- |
| Create | The prompt asks to generate, fill, or add the plan's images from scratch (empty `{{...IMAGE` slots) |
| Update | The prompt asks to change, refine, regenerate, or replace images that already exist in the plan |

## Optional gpt-image scripts

These commands require `uv`, network access, `OPENAI_API_KEY`, and the approval gate above. The shell working directory may differ from the skill directory, so resolve the anchor inline with each command:

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>"

# Create image
uv run "$SKILL_DIR/scripts/generate_gpt_image.py" "<prompt>" <output.png> --size 1536x1024 --quality high

# Edit image
uv run "$SKILL_DIR/scripts/edit_gpt_image.py" "<instruction>" <output.png> <input.png> --size 1536x1024 --quality high
```

Shared rules for every image:
- use a wide composition that fits the plan's figure area;
- convey the one or two core ideas of that section for a professional software engineer;
- match the plan's synchronized visual identity;
- for `gpt-image`, keep total words shown in the image under 10 and save images to `IMAGES_OUTPUT_DIR` (create it if missing);
- for `inline-svg`, use as many concise labels as comprehension requires and keep text selectable.

## Create

1. Find slots - Grep the plan for `{{...IMAGE` placeholders (hero + per-phase). Each comment names the intended subject.
2. Define content - For each useful slot, describe the idea the figure must communicate.
3. Produce:
   - `gpt-image` - run `generate_gpt_image.py` once per slot, writing to `IMAGES_OUTPUT_DIR`.
   - `inline-svg` - author the accessible SVG directly in the figure using the plan's custom properties.
4. Embed:
   - `gpt-image` - replace the placeholder with `<img src="<plan-name>/<file>.png" alt="...">`.
   - `inline-svg` - replace the placeholder with the `<svg>` element.
   Keep the existing `<figure>` and `<figcaption>` in either case.
5. Verify - Inspect the rendered plan and confirm every figure is legible, relevant, and free of unresolved placeholders.
6. Report - List the figures produced and the slots filled or intentionally removed.

## Update

1. Identify targets - From the `USER_PROMPT`, determine which embedded images or SVGs need to change.
2. Define the change - Describe what must change and what existing meaning must remain.
3. Update:
   - `gpt-image` - run `edit_gpt_image.py` with the existing PNG as input; the script backs up an overwritten output.
   - `inline-svg` - edit the SVG structure, labels, title, description, and styles directly.
4. Verify - Render the plan, confirm the updated figure and its accessibility text, and check that `src`, `alt`, and `<figcaption>` remain accurate where applicable.
5. Report - List the figures updated and what changed.
