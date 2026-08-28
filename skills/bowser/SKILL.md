---
name: bowser
description: Automates browsers with Playwright CLI for UI testing, screenshots, navigation, scraping, and parallel browser sessions. Use when a task requires headless browser interaction or verification without a user-driven browser.
compatibility: Requires the playwright-cli executable, an installed supported browser, network access for remote pages, and writable local storage for screenshots and persistent profiles.
metadata:
  category: browser-automation
---

# Browser Automation with Playwright CLI

Use `playwright-cli` for background browser work without loading a browser-tool schema into context.

## Preflight

Before opening a browser, run:

```bash
command -v playwright-cli
playwright-cli --version
```

If either command fails, stop and report the missing dependency. Do not install packages or download browsers without approval.

## Workflow

1. **Choose a named session.** Derive a short kebab-case name from the task, such as `checkout-test` or `pricing-scrape`. Use `-s=<session-name>` on every session-scoped command.
2. **Open the target.** Use a reproducible desktop viewport by default; change it when the task specifies another device or size.

   ```bash
   PLAYWRIGHT_MCP_VIEWPORT_SIZE=1440x900 playwright-cli -s=<session-name> open <url> --persistent
   ```

   Add `--headed` only when a visible browser is useful. Add `PLAYWRIGHT_MCP_CAPS=vision` only when screenshots should be returned for visual analysis.
3. **Inspect the page.** Obtain current element references before interacting:

   ```bash
   playwright-cli -s=<session-name> snapshot
   ```
4. **Interact using current references.** Refresh the snapshot after navigation or major DOM changes.

   ```bash
   playwright-cli -s=<session-name> click <ref>
   playwright-cli -s=<session-name> fill <ref> "text"
   playwright-cli -s=<session-name> press Enter
   ```
5. **Verify the result.** Inspect the resulting state and capture evidence when useful:

   ```bash
   playwright-cli -s=<session-name> snapshot
   playwright-cli -s=<session-name> screenshot --filename=output.png
   ```
6. **Close the session even after failure.**

   ```bash
   playwright-cli -s=<session-name> close
   ```

Do not expose cookies, storage values, credentials, or private page content in the response. Delete persistent session data when the user requests cleanup:

```bash
playwright-cli -s=<session-name> delete-data
```

## Configuration

If `playwright-cli.json` exists in the working directory, let the CLI use it. If the user provides another configuration, pass `--config path/to/config.json`. Do not create or replace configuration unless the task requires it.

## Command reference

Read [references/commands.md](references/commands.md) when the task needs tabs, storage, network routing, tracing, video, mouse input, or other commands beyond the workflow above. For exact installed-version syntax, run `playwright-cli --help <command>`.
