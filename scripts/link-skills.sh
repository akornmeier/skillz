#!/usr/bin/env bash
# Symlink every skills/<name> into each agent's skills directory, and prune
# links left behind by skills that were removed or renamed in this repo.
#
# Usage: scripts/link-skills.sh [-n] [--install-hooks] [target-dir ...]
#   -n               dry run: print what would change
#   --install-hooks  install git hooks that rerun this script after pulls
#   target-dir       defaults to ~/.agents/skills (Pi) and ~/.claude/skills (Claude Code)

set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
src="$repo/skills"
dry_run=0
install_hooks=0
targets=()

for arg in "$@"; do
  case "$arg" in
    -n) dry_run=1 ;;
    --install-hooks) install_hooks=1 ;;
    -h|--help) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) echo "unknown option: $arg" >&2; exit 2 ;;
    *) targets+=("$arg") ;;
  esac
done
[ ${#targets[@]} -gt 0 ] || targets=("$HOME/.agents/skills" "$HOME/.claude/skills")

run() {
  echo "  $*"
  [ "$dry_run" -eq 1 ] || "$@"
}

if [ "$install_hooks" -eq 1 ]; then
  hooks="$(git -C "$repo" rev-parse --git-path hooks)"
  case "$hooks" in /*) ;; *) hooks="$repo/$hooks" ;; esac
  # post-merge fires on merge/fast-forward pulls; post-rewrite on rebase pulls.
  for hook in post-merge post-rewrite; do
    echo "hook: $hooks/$hook"
    if [ "$dry_run" -eq 0 ]; then
      mkdir -p "$hooks"
      printf '#!/bin/sh\nexec "$(git rev-parse --show-toplevel)/scripts/link-skills.sh"\n' > "$hooks/$hook"
      chmod +x "$hooks/$hook"
    fi
  done
fi

for target in "${targets[@]}"; do
  echo "$target"
  [ -d "$target" ] || run mkdir -p "$target"

  # Prune dangling links that point into this repo's skills directory.
  for link in "$target"/*; do
    [ -L "$link" ] || continue
    dest="$(readlink "$link")"
    case "$dest" in "$src"/*) [ -e "$link" ] || run rm "$link" ;; esac
  done

  for dir in "$src"/*/; do
    dir="${dir%/}"
    [ -f "$dir/SKILL.md" ] || continue
    link="$target/$(basename "$dir")"
    if [ -L "$link" ]; then
      [ "$(readlink "$link")" = "$dir" ] && continue
      echo "  skip $link: already links to $(readlink "$link")" >&2
    elif [ -e "$link" ]; then
      echo "  skip $link: exists and is not a symlink" >&2
    else
      run ln -s "$dir" "$link"
    fi
  done
done

# Skills with a package manifest keep their dependencies in their own directory.
for manifest in "$src"/*/package.json; do
  [ -f "$manifest" ] || continue
  dir="$(dirname "$manifest")"
  [ -d "$dir/node_modules" ] || echo "note: $(basename "$dir") has no node_modules; run: npm install --prefix $dir --ignore-scripts"
done
