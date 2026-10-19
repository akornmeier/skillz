#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["PyYAML==6.0.3"]
# ///
"""Validate skill format, then report local-policy checks and heuristic advice.

usage: uv run --script lint_skill.py [--json] [--target portable|pi|claude-code] [SKILL_DIR ...]

Provision the pinned dependency once with approval; add --offline to subsequent uv
runs. No implicit fallback parser. Directory arguments and --json remain supported.
No arguments scans conventional local roots, not a client's complete discovery set.
--target adds named client checks to portable validation; it is not a client emulator.

FAIL: malformed portable fields, selected client contracts, broken bundled links,
or malformed repository-local schema-1 eval definitions. WARN: compatibility gaps,
missing local evals, wording, size, navigation, dates, or other heuristics. Findings
carry authority=portable|platform|local|heuristic. Exit 1 on FAIL, 0 for advice only,
2 for invalid CLI/no targets. Static checks prove neither task quality nor live use.

Costs: UTF-8 bytes / 4 estimates, not model tokenization. Raw YAML metadata and body
are separate. Route figures are static referenced-material scenarios, including
conditional references, excluding executed scripts/evals; never measured loading.
"""
import argparse
import json
import os
import re
import sys

import yaml

# Portable limits: https://agentskills.io/specification
NAME_MAX = 64  # Portable name character limit.
DESC_MAX = 1024  # Portable description character limit.
COMPAT_MAX = 500  # Portable optional environment-description limit.
# Recommendations/house heuristics, not format limits.
BODY_RECOMMENDED = 500  # Agent Skills recommendation, not a body format restriction.
BODY_HOUSE = 150  # Repository preference for a small router.
TOC_LINES = 100  # Anthropic navigation recommendation.
BYTES_PER_TOKEN = 4  # Rough English-text estimate; no tokenizer or runtime measurement.
RESERVED = ("anthropic", "claude")  # Anthropic authoring restrictions, not portable format.
TAG_RE = re.compile(r"<[a-zA-Z/][^>]*>")
PERSON_RE = re.compile(r"^(i|i'm|i'll|i've|we|we'll|you|you'll|you're|your)\b", re.I)
TRIGGER_RE = re.compile(r"use\s+(this\s+|it\s+)?when|when|triggers?\s+on|use for", re.I)
DATE_RE = re.compile(r"\b(before|after|until|as of|since)\s+(?:[A-Za-z]+\s+)?(?:19|20)\d\d\b", re.I)
BACKSLASH_PATH_RE = re.compile(r"\b[\w.-]+\\[\w.-]+\.[a-z0-9]+\b")
EXT = r"(?:md|py|sh|js|ts|json|ya?ml|txt|html|csv|toml|cfg|ini)"
TICK_RE = re.compile(r"`([^`\s]+?\." + EXT + r")`")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+?\." + EXT + r")\)")
INTENT_RE = re.compile(r"\b(run|execute|invoke|python3?|uv|bash|node|see|read|inspect)\b", re.I)
SCRIPT_EXT = (".py", ".sh", ".js", ".ts")
CONSTANT_RE = re.compile(r"^[A-Z][A-Z0-9_]*\s*=\s*-?\d+(\.\d+)?\s*$")
SKIP_ORPHAN = {"README.md", "LICENSE", ".DS_Store", "evals.md", "package.json",
               "package-lock.json", "requirements.txt", "pyproject.toml"}
SKIP_DIRS = {"evals", ".git", "node_modules", "__pycache__"}
DEFAULT_ROOTS = ("~/.agents/skills", "~/.pi/agent/skills", "~/.claude/skills",
                 "./.agents/skills", "./.pi/skills", "./.claude/skills")
PROFILES = ["fast/economical", "balanced/default", "highest-reasoning"]
PORTABLE_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
# Named, supported extensions only. Unknown fields are advice, never invented contracts.
CLIENT_FIELDS = {"pi": {"disable-model-invocation"}, "claude-code": {
    "disable-model-invocation", "user-invocable", "argument-hint", "arguments", "when_to_use",
    "model", "effort", "context", "agent", "background", "hooks", "paths", "shell", "disallowed-tools"}}


class UniqueSafeLoader(yaml.SafeLoader):
    """Safe YAML, rejecting duplicate explicit keys while preserving merge semantics."""
    def construct_mapping(self, node, deep=False):
        keys = set()
        for key_node, _ in node.value:
            if key_node.tag == "tag:yaml.org,2002:merge":
                continue
            key = self.construct_object(key_node, deep=deep)
            try:
                if key in keys:
                    raise yaml.constructor.ConstructorError("mapping", node.start_mark,
                                                            f"duplicate key {key!r}", key_node.start_mark)
                keys.add(key)
            except TypeError:
                raise yaml.constructor.ConstructorError("mapping", node.start_mark,
                                                        "mapping keys must be scalar", key_node.start_mark) from None
        return super().construct_mapping(node, deep=deep)


class Finding:
    def __init__(self, skill, check, level, what, fix, authority="heuristic"):
        self.skill, self.check, self.level = skill, check, level
        self.what, self.fix, self.authority = what, fix, authority

    def line(self):
        return f"{self.skill} · {self.check} — {self.level} [{self.authority}]: {self.what}. Fix: {self.fix}"

    def as_dict(self):
        return {"check": self.check, "level": self.level, "what": self.what,
                "fix": self.fix, "authority": self.authority}


def read(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def parse_frontmatter(text):
    """Return (safe mapping, body, raw metadata); errors retain YAML location details."""
    match = re.match(r"\A---\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", text, re.S)
    if not match:
        raise ValueError("start line 1 with --- and close YAML with a separate --- line")
    front = yaml.load(match.group(1), Loader=UniqueSafeLoader)
    if not isinstance(front, dict) or not all(isinstance(k, str) for k in front):
        raise ValueError("frontmatter must be a mapping with string field names")
    return front, text[match.end():], match.group(0)


def bundled_files(skill_dir):
    out = []
    for root, dirs, files in os.walk(skill_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        out.extend(os.path.relpath(os.path.join(root, f), skill_dir) for f in files
                   if f not in SKIP_ORPHAN and not f.startswith("."))
    return sorted(out)


def references_in(text, from_rel, skill_dir, top_dirs):
    refs = []
    for line in text.split("\n"):
        for token in TICK_RE.findall(line) + LINK_RE.findall(line):
            if token.startswith(("http", "~", "/", "$")) or any(c in token for c in "<*{"):
                continue
            clean = token.removeprefix("./")
            if "/" in clean and clean.split("/")[0] not in top_dirs:
                continue
            if "/" not in clean and clean != "SKILL.md":
                continue
            candidates = [clean, os.path.normpath(os.path.join(os.path.dirname(from_rel), clean))]
            hit = next((c for c in candidates if os.path.isfile(os.path.join(skill_dir, c))), None)
            refs.append((token, hit, line))
    return refs


def validate_fields(front, name, target, add):
    for field, maximum in (("name", NAME_MAX), ("description", DESC_MAX), ("compatibility", COMPAT_MAX)):
        if field not in front and field == "compatibility":
            continue
        value = front.get(field)
        if not isinstance(value, str) or not value.strip():
            add(f"{field}-type", "FAIL", f"{field} must be a non-empty string", f"quote or supply {field}", "portable")
        elif len(value) > maximum:
            add(f"{field}-length", "FAIL", f"{field} has {len(value)} characters; maximum {maximum}", f"shorten {field}", "portable")
    declared, desc = front.get("name"), front.get("description")
    if isinstance(declared, str) and declared:
        valid = (declared == declared.lower() and not declared.startswith("-") and not declared.endswith("-")
                 and "--" not in declared and all(c.isalnum() or c == "-" for c in declared))
        if not valid:
            add("name-format", "FAIL", "name must use lowercase alphanumerics and single hyphens", "use a lowercase hyphenated name", "portable")
        if declared != name:
            add("name-dir", "FAIL", f"name {declared!r} differs from directory {name!r}", "match name and directory for portability", "portable")
        if any(word in declared for word in RESERVED):
            add("name-reserved", "FAIL" if target == "claude-code" else "WARN",
                "Anthropic guidance reserves names containing anthropic or claude", "rename for Anthropic compatibility", "platform")
    if "license" in front and not isinstance(front["license"], str):
        add("license-type", "FAIL", "license must be a string", "use a license name or file reference", "portable")
    if "metadata" in front:
        value = front["metadata"]
        if not isinstance(value, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in value.items()):
            add("metadata-type", "FAIL", "metadata must map strings to strings", "quote numeric/boolean metadata values", "portable")
    if "allowed-tools" in front:
        value = front["allowed-tools"]
        cc_list = target == "claude-code" and isinstance(value, list) and all(isinstance(v, str) and v.strip() for v in value)
        if not isinstance(value, str) and not cc_list:
            add("allowed-tools-type", "FAIL", "allowed-tools requires a portable space-separated string (Claude Code also accepts a string list)",
                "use allowed-tools: Read Grep", "platform" if target == "claude-code" else "portable")
    supported = CLIENT_FIELDS.get(target, set())
    for field in front.keys() - PORTABLE_FIELDS:
        if field not in supported:
            add("field-compatibility", "WARN", f"{field!r} has no validated behavior for target {target}", "check named client support; do not rely on it for permission enforcement", "platform")
            continue
        value = front[field]
        if field in {"disable-model-invocation", "user-invocable", "background"}:
            cc_boolean = target == "claude-code" and (
                (isinstance(value, str) and value.lower() in {"true", "false", "yes", "no", "on", "off", "1", "0"})
                or (type(value) is int and value in (0, 1)))
            valid = isinstance(value, bool) or cc_boolean
            expected = "a YAML boolean (Claude Code also accepts documented boolean aliases)"
        elif field in {"disallowed-tools", "arguments", "paths"}:
            valid = isinstance(value, str) or (isinstance(value, list) and all(isinstance(v, str) for v in value))
            expected = "a string or string list"
        elif field == "hooks":
            valid, expected = isinstance(value, dict), "a mapping (hook contents need client validation)"
        else:
            valid, expected = isinstance(value, str), "a string"
        if not valid:
            add("field-type", "FAIL", f"{target} extension {field!r} requires {expected}", "use the named client's documented type", "platform")
    if isinstance(desc, str):
        if TAG_RE.search(desc):
            add("description-tags", "FAIL" if target == "claude-code" else "WARN", "Anthropic guidance disallows XML tags in descriptions", "use plain text for Anthropic compatibility", "platform")
        if PERSON_RE.match(desc):
            add("description-person", "WARN", "description uses first/second person; third person is an authoring preference", "prefer capability, intent and boundaries; verify discovery behavior", "heuristic")
        if not TRIGGER_RE.search(desc):
            add("description-trigger", "WARN", "no conventional trigger clause found; alternate wording may be sufficient", "review intent coverage, not keyword presence", "heuristic")


def validate_evals(path, name, add):
    if not os.path.isfile(path):
        add("evals-missing", "WARN", "no evals/evals.json (repository release policy)", "add at least three cases before release qualification", "local")
        return
    try:
        suite = json.loads(read(path))
        def require(condition, message):
            if not condition:
                raise ValueError(message)
        def nonempty(value):
            return isinstance(value, str) and bool(value.strip())
        require(isinstance(suite, dict), "root must be an object")
        require(type(suite.get("schema")) is int and suite["schema"] == 1, "schema must be 1")
        require(suite.get("skill") == name, "skill must equal the package name")
        require(suite.get("requiredProfiles") == PROFILES, "requiredProfiles must list all three repository profiles in order")
        cases = suite.get("cases")
        require(isinstance(cases, list) and len(cases) >= 3, "at least three cases are required")
        seen = set()
        for index, case in enumerate(cases):
            label = f"cases[{index}]"
            require(isinstance(case, dict), f"{label} must be an object")
            case_id = case.get("id")
            require(nonempty(case_id) and case_id.startswith(name + "-"), f"{label}.id must start with {name}-")
            require(case_id not in seen, f"{label}.id is duplicated")
            seen.add(case_id)
            for field in ("summary", "setup", "prompt"):
                require(nonempty(case.get(field)), f"{label}.{field} must be a non-empty string")
            for field in ("expectedBehavior", "forbiddenBehavior"):
                values = case.get(field)
                require(isinstance(values, list) and len(values) >= 2 and all(nonempty(v) for v in values),
                        f"{label}.{field} needs at least two non-empty strings")
    except (OSError, ValueError) as exc:
        add("evals-format", "FAIL", f"evals/evals.json: {exc}", "repair schema-1 definitions; validate definitions separately from executing them", "local")


def lint_skill(skill_dir, target="portable"):
    skill_dir = os.path.abspath(skill_dir)
    name = os.path.basename(skill_dir)
    findings = []
    def add(check, level, what, fix, authority="heuristic"):
        findings.append(Finding(name, check, level, what, fix, authority))
    summary = {"skill": name, "path": skill_dir, "target": target}
    try:
        text = read(os.path.join(skill_dir, "SKILL.md"))
    except (OSError, UnicodeError) as exc:
        add("skill-loads", "FAIL", f"cannot read SKILL.md: {exc}", "provide a readable UTF-8 SKILL.md", "portable")
        summary.update(fail=1, warn=0)
        return findings, summary
    try:
        front, body, raw_metadata = parse_frontmatter(text)
    except (ValueError, yaml.YAMLError) as exc:
        add("frontmatter", "FAIL", f"invalid YAML frontmatter: {exc}", "repair the mapping and delimiter lines", "portable")
        front, body, raw_metadata = {}, text, ""
    validate_fields(front, name, target, add)
    lines = len(text.split("\n")) - int(text.endswith("\n"))
    summary.update(lines=lines, bytes=len(text.encode()), tokens_est=len(text.encode()) // BYTES_PER_TOKEN,
                   metadata_bytes=len(raw_metadata.encode()), metadata_tokens_est=len(raw_metadata.encode()) // BYTES_PER_TOKEN,
                   body_bytes=len(body.encode()), body_tokens_est=len(body.encode()) // BYTES_PER_TOKEN,
                   estimate_basis="UTF-8 bytes/4; raw YAML metadata and instructions; client wrappers/advertised paths unknown; static, not observed")
    if lines > BODY_HOUSE:
        add("body-length", "WARN", f"SKILL.md has {lines} lines; {BODY_HOUSE} is a house heuristic, {BODY_RECOMMENDED}/about 5,000 tokens are recommendations",
            "measure useful context before splitting; neither threshold is a format error")
    top_dirs = {"scripts", "references", "assets", "workflows", "templates"} | {
        d for d in os.listdir(skill_dir) if os.path.isdir(os.path.join(skill_dir, d))}
    files = bundled_files(skill_dir)
    texts = {}
    for f in files:
        if f.endswith(".md"):
            try:
                texts[f] = read(os.path.join(skill_dir, f))
            except (OSError, UnicodeError) as exc:
                add("ref-unreadable", "FAIL", f"{f}: {exc}", "provide a readable UTF-8 reference", "local")
                texts[f] = ""
    refs = {f: references_in(content, f, skill_dir, top_dirs) for f, content in texts.items()}
    direct = {hit for _, hit, _ in refs.get("SKILL.md", []) if hit}
    for f, content in texts.items():
        if DATE_RE.search(content):
            add("body-dates", "WARN", f"{f} contains date-bound wording", "check provenance/version; retain valid historical or compatibility context")
        if BACKSLASH_PATH_RE.search(content):
            add("body-paths", "WARN", f"{f} uses backslash paths", "prefer portable forward slashes")
        if f != "SKILL.md" and len(content.split("\n")) > TOC_LINES and not re.search(r"^#{1,6}\s*(table of )?contents\b", content, re.I | re.M):
            add("ref-toc", "WARN", f"{f} exceeds {TOC_LINES} lines without a Contents heading", "add section navigation when helpful")
        for token, hit, line in refs[f]:
            if hit is None:
                add("ref-missing", "FAIL", f"{f} references missing {token!r}", "repair the bundled path or supply the file", "local")
            elif hit.endswith(SCRIPT_EXT) and not INTENT_RE.search(line):
                add("ref-intent", "WARN", f"{f} names {hit!r} without execute/read intent", "state how the script is used")
            elif f in direct and hit.endswith(".md") and hit not in direct | {"SKILL.md", f}:
                add("ref-depth", "WARN", f"{f} routes to {hit!r} indirectly", "prefer direct routing; keep necessary depth with explicit navigation")
    script_texts = []
    for f in files:
        if f.endswith(SCRIPT_EXT):
            try:
                script = read(os.path.join(skill_dir, f))
            except (OSError, UnicodeError):
                continue
            script_texts.append(script)
            script_lines = script.split("\n")
            for i, line in enumerate(script_lines):
                if CONSTANT_RE.match(line) and not (i and script_lines[i - 1].lstrip().startswith("#")):
                    add("script-constants", "WARN", f"{f}:{i + 1} numeric constant lacks rationale", "explain non-obvious configuration values")
    all_text = "\n".join(list(texts.values()) + script_texts)
    for f in files:
        base, directory = os.path.basename(f), os.path.dirname(f)
        whole_dir = bool(directory) and re.search(re.escape(directory + "/") + r"(?=[`\s*)\]])", all_text)
        if f != "SKILL.md" and f not in all_text and not (base != "SKILL.md" and base in all_text) and not whole_dir:
            add("ref-orphan", "WARN", f"{f} has no detected reference (heuristic)", "check conditional coverage before adding a route or deleting anything")
    sizes = {}
    for f in files:
        try:
            sizes[f] = os.path.getsize(os.path.join(skill_dir, f))
        except OSError:
            sizes[f] = 0
            add("ref-unreadable", "FAIL", f"cannot stat bundled file {f!r}", "repair the broken file or link", "local")
    summary["bundle_bytes"] = sum(sizes.values())
    workflows = sorted(f for f in direct if f.startswith("workflows/") and f.endswith(".md"))
    scenarios = {wf: {"SKILL.md", wf} | {h for _, h, _ in refs.get(wf, []) if h in files and not h.endswith(SCRIPT_EXT)} for wf in workflows}
    if not scenarios:
        scenarios = {"(single route)": {"SKILL.md"} | {h for h in direct if not h.endswith(SCRIPT_EXT)}}
    summary["routes"] = {route: {"bytes": sum(sizes.get(f, 0) for f in material),
                                 "tokens_est": sum(sizes.get(f, 0) for f in material) // BYTES_PER_TOKEN,
                                 "files": sorted(material), "kind": "static referenced-material estimate"}
                         for route, material in scenarios.items()}
    validate_evals(os.path.join(skill_dir, "evals", "evals.json"), name, add)
    summary.update(fail=sum(f.level == "FAIL" for f in findings), warn=sum(f.level == "WARN" for f in findings))
    return findings, summary


def expand_targets(args):
    roots = args or [os.path.expanduser(r) for r in DEFAULT_ROOTS if os.path.isdir(os.path.expanduser(r))]
    targets, seen = [], set()
    for root in roots:
        real = os.path.realpath(root)
        if real in seen:
            continue
        seen.add(real)
        if os.path.isfile(os.path.join(root, "SKILL.md")) or (os.path.islink(root) and not os.path.exists(root)):
            targets.append(root)
        elif os.path.isdir(root):
            children = [os.path.join(root, d) for d in sorted(os.listdir(root))
                        if not d.startswith(".") and os.path.isdir(os.path.join(root, d))]
            targets.extend(children if any(os.path.isfile(os.path.join(c, "SKILL.md")) for c in children) else [root])
        else:
            targets.append(root)  # explicit missing input produces a format failure, not silent omission
    return targets


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--target", choices=("portable", "pi", "claude-code"), default="portable")
    parser.add_argument("directories", nargs="*")
    args = parser.parse_args(argv)
    targets = expand_targets(args.directories)
    if not targets:
        print("no skill directories found", file=sys.stderr)
        return 2
    results = []
    for target in targets:
        findings, summary = lint_skill(target, args.target)
        results.append(dict(summary, findings=[f.as_dict() for f in findings]))
        if not args.json:
            for f in findings:
                print(f.line())
            print(f"{summary['skill']} · {'FAIL' if summary['fail'] else 'PASS'} · {summary['fail']} fail, {summary['warn']} advice/compatibility")
            if "metadata_bytes" in summary:
                print(f"    raw metadata: {summary['metadata_bytes']} bytes ≈{summary['metadata_tokens_est']} tokens; "
                      f"body: {summary['body_bytes']} bytes ≈{summary['body_tokens_est']} tokens (static estimates)")
                for route, scenario in summary["routes"].items():
                    print(f"    {route}: {scenario['bytes']} bytes ≈{scenario['tokens_est']} tokens (static referenced-material estimate)")
    code = int(any(s["fail"] for s in results))
    if args.json:
        print(json.dumps({"skills": results, "exit": code}, indent=2))
    else:
        worst = sorted(results, key=lambda s: (-s["fail"], -s["warn"]))
        print(f"{len(results)} skill(s) · {sum(bool(s['fail']) for s in results)} with FAIL · worst first: " + ", ".join(s["skill"] for s in worst[:5]))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
