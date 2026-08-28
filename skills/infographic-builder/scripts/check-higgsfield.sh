#!/usr/bin/env bash
set -uo pipefail

if ! command -v higgsfield >/dev/null 2>&1; then
  echo "Higgsfield CLI: not found (optional; local SVG/HTML remains available)"
  exit 1
fi

echo "Higgsfield CLI: $(command -v higgsfield)"
if ! higgsfield version; then
  echo "Unable to read Higgsfield CLI version." >&2
  exit 2
fi

echo
echo "No authentication, account, upload, cost, or generation command was run."
echo "Inspect current syntax with: higgsfield --help"
