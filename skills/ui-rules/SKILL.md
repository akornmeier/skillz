---
name: ui-rules
description: Checks every screen against fixed UI rules for spacing, color, mobile, and dashboards before it is shown. Use for any UI work, including building or changing pages, components, forms, layouts, styles, charts, dashboards, HTML artifacts, and design mocks. Not for research-grounded UX critiques (ux-design) or motion and animation (emil-design-eng).
---

# UI Rules

Check every screen against these rules before showing it: a page, component, form, dashboard, artifact, mock, or screenshot you report on. Fix what fails, then show it.

## How to apply

1. Check every section that fits the screen. Mobile applies to any web UI that can render on a phone. Dashboards applies to any screen with metrics, charts, or data tables.
2. Rules marked (default) are starting points. Break them when the design needs it, and say which rule and why in one line. Rules without (default) are firm: fix every violation before showing.
3. A project's design system or the user's explicit instruction outranks a (default) rule. It does not outrank a firm rule; flag the conflict instead of shipping it silently.
4. Measure where a rule gives a number. Compute contrast from the actual colors, and read tap-target and input font sizes from the code or rendered page. If you could not check a rule, say so. Never report an unchecked rule as passing.
5. When you show the screen, list only exceptions: (default) rules you broke on purpose, firm-rule conflicts, and rules you could not check. Do not paste the whole checklist.

## Rules

### Spacing

- Use gaps from one scale only: 4, 8, 16, 24, 32. (default)
- Put a label closer to its own field than to the field above.
- More space between groups than within a group.
- Align everything on one edge. No mixed centering. (default)
- Pad cards with 16px or more. (default)
- Nested corners: inner radius = outer radius minus padding, never below 0.

### Color

- One accent color, for the main action only. Other buttons are neutral. (default)
- Never show an error with color alone. Add a message.
- Keep meanings fixed: red is danger, green is success.
- Check text contrast on colored buttons too (4.5:1 minimum).
- Soft tints for large areas, strong color only for small details. (default)
- Links get color and an underline.

### Mobile

- Tap targets at least 44x44.
- Main button at the bottom, where the thumb is. (default)
- Inputs use 16px text, or iPhone zooms in on focus.
- Set the right input type so the right keyboard opens.
- No hover-only actions.
- Bottom sheets instead of small centered dialogs. (default)

### Dashboards

- Lead with the one number that matters most. (default)
- Every number gets a period and a change ("+8.1% vs September").
- Bar charts start at zero.
- More than 3 parts? Sorted bars, not a pie. (default)
- Right-align numbers in tables.
- Highlight one line, gray out the rest. (default)

## Related skills

For a research-grounded critique of flows, forms, or decisions, use [ux-design](../ux-design/SKILL.md). For motion and interaction polish, use [emil-design-eng](../emil-design-eng/SKILL.md).
