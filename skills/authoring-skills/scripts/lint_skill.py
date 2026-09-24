#!/usr/bin/env python3
"""Lint one or many Agent Skill directories for mechanically provable defects.

usage: lint_skill.py [--json] [SKILL_DIR ...]

With no SKILL_DIR, scans every skill under ~/.agents/skills and ./.claude/skills.
A SKILL_DIR may be a single skill (contains SKILL.md) or a directory of skills.

Every finding is one line:  <skill> · <check> — FAIL|WARN: <what>. Fix: <edit>
Then a summary block per skill with the bytes and approximate tokens (bytes / 4,
an estimate) forced on every trigger, and the same per route. Exit 1 on any FAIL.

Python 3 standard library only. Frontmatter is parsed by hand, so no PyYAML.
Reference detection is heuristic: paths in backticks or markdown links whose first
segment is a directory that exists in the skill. Prose mentions without either are
missed; findings are evidence for a grader, not verdicts.
"""
import json
import os
import re
import sys

# --- limits ---------------------------------------------------------------
NAME_MAX = 64            # spec: name is at most 64 characters
DESC_MAX = 1024          # spec: description is at most 1,024 characters
DESC_THIN = 80           # under ~80 chars a description rarely states both what and when
BODY_FAIL = 500          # spec: keep SKILL.md under 500 lines
BODY_WARN = 150          # above ~150 lines the router is carrying depth that belongs in references
TOC_LINES = 100          # spec: reference files over 100 lines need a table of contents
ROUTE_SHARE = 0.5        # a route paying for more than half the bundle is paying for other routes
BYTES_PER_TOKEN = 4      # rough English-text ratio; stated as an estimate wherever printed

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
RESERVED = ("anthropic", "claude")  # spec: reserved words the name cannot contain
TAG_RE = re.compile(r"<[a-zA-Z/][^>]*>")  # XML tags are not allowed in name or description
PERSON_RE = re.compile(r"^(i|i'm|i'll|i've|we|we'll|you|you'll|you're|your)\b", re.I)
WHEN_ONLY_RE = re.compile(r"^use\s+(this\s+|it\s+)?when", re.I)
TRIGGER_RE = re.compile(
    r"use\s+(this\s+|it\s+)?when(ever)?|when(ever)?\s+(the\s+)?(user|prompt|working|you)"
    r"|triggers?\s+on|for use when|use for", re.I)
# Phrases the model follows unprompted; each costs tokens and adds nothing.
UNPROMPTED_RE = re.compile(
    r"required[ ]reading|read[ ]these[ ]files[ ]first|chmod \+x|git (add|commit|push)\b|ls -la|head -10"
    r"|ultrathink|think (hard|step by step)|consider edge cases|where appropriate|be thorough",
    re.I)
DATE_RE = re.compile(
    r"\b(before|after|until|as of|since|prior to|starting)\s+"
    r"((jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+)?(19|20)\d\d\b", re.I)
BACKSLASH_PATH_RE = re.compile(r"\b[\w.-]+\\[\w.-]+\.[a-z0-9]+\b")
# `path/in/backticks` or [text](path); a path needs a known file extension to count.
EXT = r"(?:md|py|sh|js|ts|json|ya?ml|txt|html|csv|toml|cfg|ini)"
TICK_RE = re.compile(r"`([^`\s]+?\." + EXT + r")`")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+?\." + EXT + r")\)")
INTENT_RE = re.compile(r"\b(run|runs|running|execute|executes|invoke|invokes|python3?|bash|node|sh|see|read|reads|reading)\b", re.I)
SCRIPT_EXT = (".py", ".sh", ".js", ".ts")
SKIP_ORPHAN = {"README.md", "LICENSE", ".DS_Store", "evals.md",  # human-facing or noise, never routed
               "package.json", "package-lock.json", "requirements.txt", "pyproject.toml"}  # manifests scripts need
SKIP_DIRS = {"evals", ".git", "node_modules", "__pycache__"}  # evals are unlinked by convention
DEFAULT_ROOTS = ("~/.agents/skills", "./.claude/skills")


class Finding:
    def __init__(self, skill, check, level, what, fix):
        self.skill, self.check, self.level, self.what, self.fix = skill, check, level, what, fix

    def line(self):
        return f"{self.skill} · {self.check} — {self.level}: {self.what}. Fix: {self.fix}"

    def as_dict(self):
        return {"check": self.check, "level": self.level, "what": self.what, "fix": self.fix}


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def parse_frontmatter(text):
    """-> (front_dict, body) or (None, text) when the file has no frontmatter block."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end < 0:
        return None, text
    front, body = text[4:end], text[end + 4:]
    fields, key = {}, None
    for line in front.split("\n"):
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            key = m.group(1)
            fields[key] = m.group(2).strip().strip('"').strip("'")
        elif key and line.startswith((" ", "\t")):
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields, body


def bundled_files(skill_dir):
    out = []
    for root, dirs, files in os.walk(skill_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in files:
            if f in SKIP_ORPHAN or f.startswith("."):
                continue
            out.append(os.path.relpath(os.path.join(root, f), skill_dir))
    return sorted(out)


def references_in(text, from_rel, skill_dir, top_dirs):
    """Paths this markdown text references, resolved relative to the skill root.
    Returns a list of (raw_token, resolved_rel_or_None, line_text)."""
    refs = []
    for line in text.split("\n"):
        for tok in TICK_RE.findall(line) + LINK_RE.findall(line):
            if tok.startswith(("http", "~", "/", "$")) or "<" in tok or "*" in tok or "{" in tok:
                continue
            clean = tok[2:] if tok.startswith("./") else tok
            first = clean.split("/")[0]
            if "/" in clean and first not in top_dirs:
                continue  # a path outside this skill: not ours to resolve
            if "/" not in clean and clean != "SKILL.md":
                continue  # bare filenames are usually about the user's project
            candidates = [clean, os.path.normpath(os.path.join(os.path.dirname(from_rel), clean))]
            hit = next((c for c in candidates if os.path.isfile(os.path.join(skill_dir, c))), None)
            refs.append((tok, hit, line))
    return refs


def lint_skill(skill_dir):
    skill_dir = os.path.abspath(skill_dir.rstrip("/"))
    name = os.path.basename(skill_dir)
    F = []
    add = lambda check, level, what, fix: F.append(Finding(name, check, level, what, fix))
    summary = {"skill": name, "path": skill_dir}

    md_path = os.path.join(skill_dir, "SKILL.md")
    if os.path.islink(skill_dir) and not os.path.exists(skill_dir):
        add("skill-loads", "FAIL", f"dangling symlink -> {os.readlink(skill_dir)}",
            "point the symlink at an existing skill directory or delete it")
        return F, summary
    if not os.path.isfile(md_path):
        add("skill-loads", "FAIL", "no SKILL.md in the directory",
            "add a SKILL.md with name and description frontmatter, or remove the directory")
        return F, summary

    text = read(md_path)
    front, body = parse_frontmatter(text)
    lines = len(text.splitlines())
    summary.update({"lines": lines, "bytes": len(text.encode()),
                    "tokens_est": len(text.encode()) // BYTES_PER_TOKEN})

    # --- frontmatter -----------------------------------------------------
    if front is None:
        add("frontmatter", "FAIL", "file does not begin with a --- frontmatter block",
            "make line 1 exactly --- and close the block with --- before the body")
        front = {}
    declared = front.get("name", "")
    desc = " ".join(front.get("description", "").split())
    if not declared:
        add("name-missing", "FAIL", "no name field", f"add `name: {name}` to the frontmatter")
    else:
        if not 1 <= len(declared) <= NAME_MAX:
            add("name-length", "FAIL", f"name is {len(declared)} chars",
                f"shorten to at most {NAME_MAX} characters")
        if not NAME_RE.match(declared):
            add("name-format", "FAIL", f"name '{declared}' is not lowercase-hyphen",
                "use only a-z, 0-9 and single hyphens, e.g. "
                + re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", declared.lower())).strip("-"))
        for word in RESERVED:
            if word in declared.lower():
                add("name-reserved", "FAIL", f"name contains reserved word '{word}'",
                    "rename the skill and its directory without that word")
        if declared != name:
            add("name-dir", "FAIL", f"name '{declared}' != directory '{name}'",
                f"set `name: {name}` or rename the directory to {declared}")
    no_autofire = str(front.get("disable-model-invocation", "")).lower() == "true"
    if not desc:
        add("description-missing", "FAIL", "no description field",
            "add a description stating what the skill does and when to use it")
    else:
        if len(desc) > DESC_MAX:
            add("description-length", "FAIL", f"description is {len(desc)} chars",
                f"cut to at most {DESC_MAX} characters")
        if TAG_RE.search(desc):
            add("description-tags", "FAIL", "description contains an XML tag",
                "remove the angle-bracket tag; plain text only")
        if PERSON_RE.match(desc):
            add("description-person", "FAIL", f"description opens in first or second person: '{desc[:40]}'",
                "rewrite in third person, e.g. 'Processes X and produces Y. Use when ...'")
        if not no_autofire:
            if not TRIGGER_RE.search(desc):
                add("description-trigger", "FAIL", "description says what but not when to use it",
                    "append 'Use when <situation>, or when the user says \"<phrase>\"'")
            elif WHEN_ONLY_RE.match(desc):
                add("description-what", "WARN", "description says when but not what the skill does",
                    "open with what it does in third person, then the 'Use when' clause")
            if len(desc) < DESC_THIN:
                add("description-thin", "WARN", f"description is {len(desc)} chars",
                    "add the phrases a user actually types so it competes with other skills")
        if no_autofire:
            add("description-autofire", "WARN", "disable-model-invocation is true; the description never triggers it",
                "keep only if the skill is meant to be invoked by slash command alone")

    # --- body ------------------------------------------------------------
    if lines > BODY_FAIL:
        add("body-length", "FAIL", f"SKILL.md is {lines} lines (limit {BODY_FAIL})",
            "move depth into references/ or workflows/ files with a 'read it when' condition")
    elif lines > BODY_WARN:
        add("body-length", "WARN", f"SKILL.md is {lines} lines; every line is paid on every trigger",
            f"keep the router under {BODY_WARN} lines and put the rest behind a condition")
    top_dirs = {d for d in os.listdir(skill_dir) if os.path.isdir(os.path.join(skill_dir, d))}
    files = bundled_files(skill_dir)
    md_files = [f for f in files if f.endswith(".md")]
    route_files = ["SKILL.md"] + [f for f in md_files if f.startswith("workflows/")]
    texts = {f: read(os.path.join(skill_dir, f)) for f in md_files}
    for f in route_files:
        for m in BACKSLASH_PATH_RE.finditer(texts[f]):
            add("body-paths", "FAIL", f"{f} uses a backslash path '{m.group(0)}'",
                "use forward slashes: " + m.group(0).replace("\\", "/"))
        for m in DATE_RE.finditer(texts[f]):
            add("body-dates", "FAIL", f"{f} has a date-bound rule '{m.group(0)}'",
                "state the current method, and move the old one under an 'Old patterns' details block")
        hits = UNPROMPTED_RE.findall(texts[f])
        if hits:
            add("body-unprompted", "WARN", f"{f} has {len(hits)} instruction(s) the model follows unprompted",
                "delete them; keep only rules the model cannot derive from the files")

    # --- reference graph ---------------------------------------------------
    refs = {f: references_in(texts[f], f, skill_dir, top_dirs) for f in md_files}
    direct = {hit for _, hit, _ in refs["SKILL.md"] if hit}
    for f in md_files:
        for tok, hit, line in refs[f]:
            if hit is None:
                add("ref-missing", "FAIL", f"{f} references '{tok}' which does not exist",
                    "create the file or fix the path")
                continue
            if hit.endswith(SCRIPT_EXT) and not INTENT_RE.search(line):
                add("ref-intent", "WARN", f"{f} names '{tok}' without saying whether to run or read it",
                    "write 'Run `<script>` to ...' or 'See `<script>` for ...'")
    # Depth is checked markdown-to-markdown only: a doc that chains to another doc is what
    # causes partial reads. Assets a doc points at (html, json, csv) are leaves.
    for f in sorted(direct):
        if f.endswith(".md") and f in refs:
            for tok, hit, _ in refs[f]:
                if hit and hit.endswith(".md") and hit != "SKILL.md" and hit not in direct and hit != f:
                    add("ref-depth", "FAIL", f"{f} -> '{tok}' is two levels from SKILL.md",
                        f"link {hit} directly from SKILL.md, or fold it into {f}")
    # Scripts count as referrers too: a scaffold script that copies assets by name links them.
    script_text = "\n".join(read(os.path.join(skill_dir, f)) for f in files if f.endswith(SCRIPT_EXT))
    all_text = "\n".join(texts.values()) + "\n" + script_text
    for f in files:
        if f == "SKILL.md":
            continue
        base, d = os.path.basename(f), os.path.dirname(f)
        whole_dir = bool(d) and re.search(re.escape(d + "/") + r"(?=[`\s*)\]])", all_text)
        mentioned = (f in all_text) or (base != "SKILL.md" and base in all_text) or bool(whole_dir)
        if not mentioned:
            add("ref-orphan", "FAIL", f"{f} is referenced by nothing",
                "add it to the Files table with a 'read it when' condition, or delete it")
    for f in md_files:
        if f == "SKILL.md":
            continue
        n = len(texts[f].splitlines())
        if n > TOC_LINES and not re.search(r"^#{1,6}\s*(table of )?contents\b", texts[f], re.I | re.M):
            add("ref-toc", "FAIL", f"{f} is {n} lines with no Contents heading",
                "add a '## Contents' section at the top listing every H2")

    # --- token budget ------------------------------------------------------
    size = lambda f: len(read(os.path.join(skill_dir, f)).encode())
    bundle = sum(size(f) for f in files)
    routes = {}
    workflows = [f for f in direct if f.startswith("workflows/") and f.endswith(".md")]
    if workflows:
        for wf in sorted(workflows):
            loaded = {"SKILL.md", wf} | {h for _, h, _ in refs.get(wf, []) if h and not h.endswith(SCRIPT_EXT)}
            routes[wf] = sum(size(f) for f in loaded)
    else:
        loaded = {"SKILL.md"} | {h for h in direct if not h.endswith(SCRIPT_EXT)}
        routes["(single route)"] = sum(size(f) for f in loaded)
    summary["bundle_bytes"] = bundle
    summary["routes"] = {r: {"bytes": b, "tokens_est": b // BYTES_PER_TOKEN,
                             "share": round(b / bundle, 2) if bundle else 0} for r, b in routes.items()}
    for r, b in routes.items():
        # Only a multi-route skill can pay for another route's depth; a single route is the whole skill.
        if len(routes) > 1 and bundle and b / bundle > ROUTE_SHARE:
            add("budget-route", "WARN",
                f"route {r} loads {b} of {bundle} bundled bytes ({b * 100 // bundle}%)",
                "split what this route reads so no route pays for the others' depth")
    evals_path = os.path.join(skill_dir, "evals", "evals.json")
    if not os.path.isfile(evals_path):
        add("evals-missing", "WARN", "no evals/evals.json",
            "write three cases (prompt + expected and forbidden behaviours) before extending the body")
    summary["fail"] = sum(1 for x in F if x.level == "FAIL")
    summary["warn"] = sum(1 for x in F if x.level == "WARN")
    return F, summary


def expand_targets(args):
    roots = args or [os.path.expanduser(r) for r in DEFAULT_ROOTS if os.path.isdir(os.path.expanduser(r))]
    targets, seen = [], set()
    for r in roots:
        r = r.rstrip("/")
        real = os.path.realpath(r)
        if real in seen:
            continue  # ~/.claude/skills is often a symlink to ~/.agents/skills; scan it once
        seen.add(real)
        children = [os.path.join(r, d) for d in sorted(os.listdir(r))
                    if not d.startswith(".") and os.path.isdir(os.path.join(r, d))] if os.path.isdir(r) else []
        if os.path.isfile(os.path.join(r, "SKILL.md")) or (os.path.islink(r) and not os.path.exists(r)):
            targets.append(r)  # a skill, or a dangling symlink reported as not loading
        elif any(os.path.isfile(os.path.join(c, "SKILL.md")) for c in children):
            targets += children  # a directory of skills
        elif os.path.isdir(r):
            targets.append(r)  # a skill directory with no SKILL.md: reported as not loading
        else:
            print(f"{r}: not a directory", file=sys.stderr)
    return targets


def main(argv):
    as_json = "--json" in argv
    args = [a for a in argv if a != "--json"]
    if any(a in ("-h", "--help") for a in args):
        print(__doc__.strip())
        return 0
    targets = expand_targets(args)
    if not targets:
        print("no skill directories found", file=sys.stderr)
        return 2
    results, any_fail = [], False
    for t in targets:
        findings, summary = lint_skill(t)
        summary["findings"] = [f.as_dict() for f in findings]
        results.append(summary)
        any_fail |= any(f.level == "FAIL" for f in findings)
        if as_json:
            continue
        for f in findings:
            print(f.line())
        state = "FAIL" if summary.get("fail") else "PASS"
        if "lines" in summary:
            print(f"{summary['skill']} · {state} · {summary['fail']} fail, {summary['warn']} warn · "
                  f"SKILL.md {summary['lines']} lines, {summary['bytes']} bytes "
                  f"(≈{summary['tokens_est']} tokens, estimate) forced on every trigger")
            for r, v in summary["routes"].items():
                print(f"    route {r}: {v['bytes']} bytes ≈{v['tokens_est']} tokens, "
                      f"{int(v['share'] * 100)}% of {summary['bundle_bytes']} bundled")
        else:
            print(f"{summary['skill']} · FAIL · does not load")
        print()
    if as_json:
        print(json.dumps({"skills": results, "exit": 1 if any_fail else 0}, indent=2))
    else:
        worst = sorted(results, key=lambda s: (-s.get("fail", 99), -s.get("warn", 0)))
        print(f"{len(results)} skill(s) · {sum(1 for s in results if s.get('fail', 1))} with FAIL · worst first: "
              + ", ".join(s["skill"] for s in worst[:5]))
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
