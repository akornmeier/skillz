#!/usr/bin/env python3
"""Mechanical pre-pass for a skills health check. Flags what a grep can prove.

usage: scan.py [SKILLS_DIR ...]     default: ~/.claude/skills and ./.claude/skills

Prints three groups: BROKEN (does not load at all), FLAGGED (loads, has at least
one provable defect), CLEAN. Judgment dimensions are not attempted here — this
narrows the field so graders only run where there is something to grade.
"""
import os
import re
import sys

UNPROMPTED = re.compile(
    r"required reading|chmod \+x|git (add|commit|push)|ls -la|head -10"
    r"|ultrathink|think (hard|step by step)|consider edge cases|where appropriate",
    re.I,
)
TRIGGER = re.compile(
    r"use\s+(this\s+|it\s+)?when(ever)?|when(ever)? the (user|prompt)|triggers?\s+on", re.I
)
SKIP_ORPHAN = {"evals.md", ".DS_Store", "README.md"}  # deliberately unlinked by convention:
# repo-facing docs for humans browsing GitHub, not a route SKILL.md is expected to link


def bundled(d):
    for root, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x not in (".git", "node_modules", "__pycache__")]
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), d)
            if rel == "SKILL.md" or f in SKIP_ORPHAN:  # skip skill-root SKILL.md and SKIP_ORPHAN names; nested SKILL.md files (e.g. templates/SKILL.md) are NOT skipped
                continue
            if rel.split(os.sep)[0] == "evals":  # unlinked by convention, same as evals.md
                continue
            yield rel


def referenced(f, text):
    """A bundled file counts as referenced if SKILL.md mentions its basename,
    its relative path, or its containing directory (only when it has one —
    top-level files have dirname '' and must match on basename/path alone)."""
    if os.path.basename(f) in text or f in text:
        return True
    d = os.path.dirname(f)
    return bool(d) and (d + "/") in text


def scan(d, name):
    """-> (state, flags, lines) where state is broken | flagged | clean."""
    md = os.path.join(d, "SKILL.md")
    if os.path.islink(d) and not os.path.exists(d):
        return "broken", [f"dangling symlink -> {os.readlink(d)}"], 0
    if not os.path.isfile(md):
        return "broken", ["no SKILL.md"], 0

    with open(md, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    lines = text.count("\n") + 1
    fm = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not fm:
        return "broken", ["no frontmatter — cannot load"], lines

    front = fm.group(1)
    m = re.search(r"^name:\s*(.+)$", front, re.M)
    declared = m.group(1).strip() if m else ""
    m = re.search(r"^description:\s*(.+(?:\n\s+.+)*)$", front, re.M)
    desc = " ".join(m.group(1).split()) if m else ""

    flags = []
    if not declared:
        flags.append("no name")
    elif declared != name:
        flags.append(f"name '{declared}' != dir '{name}'")
    # This flag hides the skill from the model entirely, which makes every
    # description check moot — report the cause, not the symptom.
    no_autofire = re.search(r"^disable-model-invocation:\s*true", front, re.M | re.I)
    if no_autofire:
        flags.append("disable-model-invocation: true — can never fire from its description")
    if not desc:
        flags.append("no description")
    elif not no_autofire and not TRIGGER.search(desc):
        flags.append("description states what, not when")
    elif not no_autofire and len(desc) < 80:
        flags.append(f"description {len(desc)} chars — thin trigger surface")
    if lines > 500:
        flags.append(f"{lines} lines > 500")
    n = len(UNPROMPTED.findall(text))
    if n:
        flags.append(f"{n} step(s) Claude does unprompted")

    files = list(bundled(d))
    orphans = [f for f in files if not referenced(f, text)]
    if orphans:
        flags.append(f"{len(orphans)}/{len(files)} bundled files unreferenced")

    return ("flagged" if flags else "clean"), flags, lines


def main():
    roots = sys.argv[1:] or [
        p for p in (os.path.expanduser("~/.claude/skills"), ".claude/skills")
        if os.path.isdir(p)
    ]
    out = {"broken": [], "flagged": [], "clean": []}
    for root in roots:
        for name in sorted(os.listdir(root)):
            d = os.path.join(root, name)
            if name.startswith(".") or not (os.path.isdir(d) or os.path.islink(d)):
                continue
            state, flags, lines = scan(d, name)
            out[state].append((d, name, flags, lines))

    for state in ("broken", "flagged"):
        if out[state]:
            print(f"\n{state.upper()} ({len(out[state])})")
            for d, name, flags, lines in sorted(out[state], key=lambda r: -len(r[2])):
                print(f"  {name:34} {lines or '':>5}  {'; '.join(flags)}")
                print(f"  {'':34} {'':>5}  {d}")
    print(f"\nCLEAN ({len(out['clean'])})")
    print("  " + ", ".join(n for _, n, _, _ in out["clean"]))
    total = sum(len(v) for v in out.values())
    print(f"\n{total} scanned · {len(out['broken'])} broken · "
          f"{len(out['flagged'])} flagged · {len(out['clean'])} clean")
    print("Grade the flagged ones against references/skill-review-rubric.md; "
          "the flags above are evidence, not verdicts.")


if __name__ == "__main__":
    main()
