# Playwright CLI command reference

Invoke every session-scoped command as:

```bash
playwright-cli -s=<session-name> <command> [arguments]
```

Element references come from `snapshot` and may become stale after navigation or DOM changes.

## Core commands

- Navigation: `open [url]`, `goto <url>`, `go-back`, `go-forward`, `reload`
- Inspection: `snapshot`, `screenshot [ref]`, `pdf`, `console`
- Elements: `click <ref>`, `fill <ref> <text>`, `type <text>`
- Keyboard: `press <key>`, `keydown <key>`, `keyup <key>`
- Mouse: `mousemove <x> <y>`, `mousedown`, `mouseup`, `mousewheel <dx> <dy>`

## Tabs and state

- Tabs: `tab-list`, `tab-new [url]`, `tab-close [index]`, `tab-select <index>`
- State: `state-save`, `state-load`
- Storage: `cookie-*`, `localstorage-*`, `sessionstorage-*`

Treat saved state as sensitive. Do not print authentication tokens or commit state files unless explicitly required and safe.

## Debugging and capture

- Network: `route <pattern>`, `route-list`, `unroute`, `network`
- Code: `run-code <code>`
- Tracing: `tracing-start`, `tracing-stop`
- Video: `video-start`, `video-stop`
- Browser options: `open --headed`, `open --browser=chrome`, `resize <width> <height>`

## Session management

These commands are not scoped to one active page:

```bash
playwright-cli list
playwright-cli -s=<session-name> close
playwright-cli -s=<session-name> delete-data
playwright-cli close-all
playwright-cli kill-all
```

Prefer closing only the session created for the current task. Use `close-all` or `kill-all` only when the user requests global cleanup or stale processes cannot be closed normally.
