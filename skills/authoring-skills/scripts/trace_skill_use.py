#!/usr/bin/env python3
"""Turn a saved fresh-session transcript into a skill navigation report.

usage: trace_skill_use.py <skill-dir> <transcript> [--format stream-json|pi-json|text] [--json]

Prints the four facts the tuning loop watches: whether the skill fired and at which
tool step, every bundled file read in order with partial reads marked, the bundled
files never opened, and the format that was parsed. Scripts that were executed are
listed apart from reads, since running a script is not reading it. Judgment supplies
the fifth fact, whether the files read were the right ones.

stream-json is Claude Code's `--output-format stream-json --verbose` output, one JSON
event per line; tool_use blocks are classified by tool and input. pi-json is Pi's
`--mode json -p` output, one event per line; each tool_execution_start event is one
call. text is any printed transcript (`pi -p` without --mode json, or a pasted
session): every path under the skill dir is taken in order of appearance, and order
and partiality are approximate. With no --format the script picks pi-json when the
first event is Pi's session header, stream-json for any other JSON, and text, with a
printed note, when the first non-empty line is not JSON. The skill dir is resolved to its real path, so the
~/.claude/skills symlink and ~/.agents/skills match, and a copy of the skill elsewhere
(a disposable eval root) matches when its directory name contains the skill name.

Exit 0 on a report, 2 on an input the script cannot read. Python 3 standard library only.
"""
import json
import os
import re
import sys

# Shell commands that show part of a file; a path after one of these is a partial read.
PARTIAL_SHELL_RE = re.compile(r"\b(head|tail|sed\s+-n|awk\s+'NR)\b")
# Shell searches print matching lines only, never the whole file.
SEARCH_SHELL_RE = re.compile(r"\b(grep|egrep|rg|ag)\b")
# Shell commands that report on a file without putting its content in context.
STAT_SHELL_RE = re.compile(r"^\s*(wc|ls|stat|test|du|file|echo|printf|\[)\b")
# A pipe into one of these after the path also cuts the read short.
PIPE_PARTIAL_RE = re.compile(r"\|\s*(head|tail|grep|rg|sed\s+-n)\b")
# Splits a shell line into the simple commands it chains.
SEGMENT_SPLIT_RE = re.compile(r"&&|\|\||;|\|")
# NAME=value or export NAME=value; the value is substituted for $NAME and ${NAME}.
ASSIGN_RE = re.compile(r"(?:^|[\s;&(])(?:export\s+)?([A-Za-z_]\w*)=(\"[^\"]*\"|'[^']*'|[^\s;&|]+)")
# Read-tool inputs that window the file; either one makes the read partial.
PARTIAL_READ_KEYS = ("offset", "limit")
# A path-like token: at least one slash, no spaces or quotes; ~ and . allowed so
# ~/.claude/skills/... and ./references/x.md both match.
PATH_TOKEN_RE = re.compile(r"[~./\w-]*/[~./\w-]+")
# An interpreter right before a path means the script was executed, not read.
RUN_RE = re.compile(r"(?:^|[;&|(\s])(?:python3?|node|bash|sh|zsh|deno|bun)\s+(?:-\S+\s+)*$")
# The line Claude Code prints when a skill loads; the path after it is the skill dir.
SKILL_LOAD_RE = re.compile(r"Base directory for this skill:\s*(\S+)")
# Directories under a skill that are never loaded at run time, matching the linter.
SKIP_DIRS = {"evals", ".git", "node_modules", "__pycache__"}
# Tools whose input names one file; the key holding the path.
FILE_TOOLS = {"Read": "file_path", "Edit": "file_path", "Write": "file_path",
              "Grep": "path", "Glob": "path", "read": "path", "edit": "path", "write": "path"}
# Tools whose input is a shell command to scan for paths.
SHELL_TOOLS = {"Bash", "bash", "shell"}


def die(msg):
    print(f"trace_skill_use: {msg}", file=sys.stderr)
    sys.exit(2)


def bundled_files(skill_dir):
    out = []
    for root, dirs, files in os.walk(skill_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in files:
            if f.startswith("."):
                continue
            out.append(os.path.relpath(os.path.join(root, f), skill_dir))
    return sorted(out)


class Resolver:
    """Maps a path token to a bundled file's relative path, or None."""

    def __init__(self, skill_dir, files):
        self.real = os.path.realpath(skill_dir)
        self.name = os.path.basename(self.real)
        self.files = set(files)

    def rel(self, tok):
        tok = tok.strip("\"'`()[]{}<>,;:")
        if not tok or "/" not in tok:
            return None
        expanded = os.path.expanduser(tok)
        if os.path.isabs(expanded):
            real = os.path.realpath(expanded)
            if real == self.real:
                return None  # the directory itself is not a file read
            if real.startswith(self.real + os.sep):
                r = os.path.relpath(real, self.real)
                return r if r in self.files else None
            clean = real  # elsewhere on disk: match a copy of the skill by its <name>/<rel> suffix below
        else:
            clean = tok[2:] if tok.startswith("./") else tok
        if clean in self.files:
            return clean
        # <dir>/<rel> where <dir> names the skill (a copy such as authoring-skills-copy or _authoring-skills-ref).
        for f in self.files:
            if clean == f or clean.endswith("/" + f):
                holder = os.path.basename(clean[: -len(f) - 1]) if clean != f else self.name
                if self.name in holder:
                    return f
        return None

    def is_skill_dir(self, tok):
        expanded = os.path.expanduser(tok.strip("\"'`()[]{}<>,;:"))
        return os.path.isabs(expanded) and os.path.realpath(expanded) == self.real


class Trace:
    def __init__(self, resolver):
        self.r = resolver
        self.step = 0            # count of tool_use blocks seen; the "when" of every fact
        self.fired = None        # (step, reason) once the skill is known to have loaded
        self.reads = []
        self.runs = []           # bundled scripts executed; an execution is not a read
        self.skipped = 0
        self.available = None    # whether the session listed the skill at start (stream-json init only)
        self.other_copy = None   # a same-named skill dir that loaded instead of this one

    def fire(self, reason, step=None):
        if self.fired is None:
            self.fired = (self.step if step is None else step, reason)

    def add_read(self, rel, tool, partial, detail=""):
        self.reads.append({"path": rel, "tool": tool, "partial": bool(partial), "step": self.step, "detail": detail})
        if rel == "SKILL.md":
            self.fire(f"{tool} SKILL.md")

    def skill_load(self, path):
        if self.r.is_skill_dir(path):
            self.fire("skill loaded", step=self.step + 1)
        elif os.path.basename(path.rstrip("/")) == self.r.name and self.other_copy is None:
            self.other_copy = path

    def scan_text(self, text, tool="text", approximate=False):
        """Paths under the skill dir in free text or a shell command, in order."""
        for m in SKILL_LOAD_RE.finditer(text):
            self.skill_load(m.group(1))
        if tool != "text":
            text = expand_vars(text)
        for line in text.split("\n"):
            for m in PATH_TOKEN_RE.finditer(line):
                rel = self.r.rel(m.group(0))
                if rel is None:
                    continue
                before = line[:m.start()]
                # Split on the masked line so a ; or | inside quotes (sed -n '1,9p;20,30p') does not cut the command.
                masked = mask_quotes(line)
                cuts = [x.end() for x in SEGMENT_SPLIT_RE.finditer(masked[:m.start()])]
                segment = before[cuts[-1]:] if cuts else before  # the simple command this path belongs to
                if RUN_RE.search(segment):
                    self.runs.append({"path": rel, "tool": tool, "step": self.step})
                    continue
                if STAT_SHELL_RE.search(segment):
                    continue  # sizes and listings put no file content in context
                ends = [x.start() for x in re.finditer(r"&&|\|\||;", masked[m.end():])]
                rest = line[m.end():m.end() + ends[0]] if ends else line[m.end():]
                hit = (PARTIAL_SHELL_RE.search(segment) or SEARCH_SHELL_RE.search(segment)
                       or PIPE_PARTIAL_RE.search(rest)
                       or (approximate and re.search(r"offset|limit", segment)))
                detail = ("search" if SEARCH_SHELL_RE.search(segment) else hit.group(0).lstrip("| ")) if hit else ""
                self.add_read(rel, tool, bool(hit), detail)

    def tool_use(self, name, inp):
        self.step += 1
        inp = inp if isinstance(inp, dict) else {}
        if name == "Skill" or name == "skill":
            skill = str(inp.get("skill", inp.get("name", "")))
            if skill.split(":")[-1] == self.r.name:
                self.fire("Skill tool")
                self.add_read("SKILL.md", name, False)  # the Skill tool loads the whole body into context
            return
        if name in FILE_TOOLS:
            path = inp.get(FILE_TOOLS[name])
            if isinstance(path, str):
                rel = self.r.rel(path)
                if rel:
                    partial = any(k in inp and inp[k] not in (None, "", 0) for k in PARTIAL_READ_KEYS)
                    detail = ",".join(f"{k}={inp[k]}" for k in PARTIAL_READ_KEYS if k in inp and inp[k] not in (None, "", 0))
                    if name in ("Grep", "Glob") and not partial:
                        partial, detail = True, "search"  # a search returns matching lines, never the file
                    self.add_read(rel, name, partial, detail)
            return
        if name in SHELL_TOOLS:
            cmd = inp.get("command", inp.get("cmd", ""))
            if isinstance(cmd, str):
                self.scan_text(cmd, tool=name)


def mask_quotes(text):
    """Same length as text, with every quoted span replaced by underscores."""
    return re.sub(r"'[^']*'|\"[^\"]*\"", lambda q: "_" * len(q.group(0)), text)


def expand_vars(cmd):
    """Substitute shell variables assigned in the same command, so `B=<skill>; cat $B/x.md` resolves."""
    for name, value in ASSIGN_RE.findall(cmd):
        value = value.strip("\"'")
        cmd = re.sub(r"\$\{" + name + r"\}|\$" + name + r"\b", lambda _m: value, cmd)
    return cmd


def iter_blocks(event):
    """Yield content blocks from one stream-json event, whatever wraps them."""
    msg = event.get("message") if isinstance(event.get("message"), dict) else event
    content = msg.get("content")
    if isinstance(content, str):
        yield {"type": "text", "text": content}
    elif isinstance(content, list):
        for b in content:
            if isinstance(b, dict):
                yield b
                if b.get("type") == "tool_result":
                    inner = b.get("content")
                    if isinstance(inner, str):
                        yield {"type": "text", "text": inner}
                    elif isinstance(inner, list):
                        for ib in inner:
                            if isinstance(ib, dict):
                                yield ib


def parse_stream_json(lines, trace):
    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            event = json.loads(raw)
        except ValueError:
            trace.skipped += 1
            continue
        if not isinstance(event, dict):
            trace.skipped += 1
            continue
        if event.get("type") == "system" and event.get("subtype") == "init" and isinstance(event.get("skills"), list):
            trace.available = trace.r.name in event["skills"]
        for block in iter_blocks(event):
            kind = block.get("type")
            if kind == "tool_use":
                trace.tool_use(str(block.get("name", "")), block.get("input"))
            elif kind == "text":
                text = block.get("text")
                if isinstance(text, str):
                    for m in SKILL_LOAD_RE.finditer(text):
                        trace.skill_load(m.group(1))


def parse_pi_json(lines, trace):
    """Pi emits one tool_execution_start per call; message_end and turn_end repeat the
    same toolCall, so only the start event is counted."""
    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            event = json.loads(raw)
        except ValueError:
            trace.skipped += 1
            continue
        if not isinstance(event, dict):
            trace.skipped += 1
            continue
        if event.get("type") == "tool_execution_start":
            trace.tool_use(str(event.get("toolName", "")), event.get("args"))


def parse_text(lines, trace):
    for line in lines:
        trace.step += 1  # each line is one step; order is approximate in this mode
        trace.scan_text(line, approximate=True)


def main(argv):
    as_json = "--json" in argv
    fmt = None
    args = []
    it = iter(a for a in argv if a != "--json")
    for a in it:
        if a == "--format":
            fmt = next(it, None)
        elif a.startswith("--format="):
            fmt = a.split("=", 1)[1]
        elif a in ("-h", "--help"):
            print(__doc__.strip())
            return 0
        else:
            args.append(a)
    if len(args) != 2:
        die(f"expected <skill-dir> <transcript>, got {len(args)} argument(s). " + __doc__.strip().split("\n")[2])
    skill_dir, transcript = args
    if fmt not in (None, "stream-json", "pi-json", "text"):
        die(f"unknown --format '{fmt}'; valid: stream-json, pi-json, text")
    if not os.path.isfile(os.path.join(skill_dir, "SKILL.md")):
        die(f"no SKILL.md in {skill_dir}; pass the skill directory, the one holding SKILL.md")
    if not os.path.exists(transcript):
        die(f"transcript not found: {transcript}. Expected a file saved from "
            "`claude -p \"<prompt>\" --output-format stream-json --verbose > run.jsonl`, "
            "`pi --no-session --mode json -p \"<prompt>\" > run.jsonl`, or a printed text transcript")
    with open(transcript, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().split("\n")
    if not any(l.strip() for l in lines):
        die(f"transcript is empty: {transcript}. Expected one JSON event per line (stream-json) or a printed text transcript")
    note = None
    if fmt is None:
        first = next(l for l in lines if l.strip()).lstrip()
        if first.startswith("{"):
            try:
                head = json.loads(first)
            except ValueError:
                head = {}
            # Pi's first event is {"type": "session", "version": N, ...}; Claude Code's is never "session".
            fmt = "pi-json" if isinstance(head, dict) and head.get("type") == "session" else "stream-json"
        else:
            fmt = "text"
            note = "first non-empty line is not JSON; reading as text, so read order and partiality are approximate"

    files = bundled_files(skill_dir)
    trace = Trace(Resolver(skill_dir, files))
    {"stream-json": parse_stream_json, "pi-json": parse_pi_json, "text": parse_text}[fmt](lines, trace)

    touched = {r["path"] for r in trace.reads} | {r["path"] for r in trace.runs}
    unread = [f for f in files if f not in touched]
    if as_json:
        out = {"fired": trace.fired is not None,
               "fired_step": trace.fired[0] if trace.fired else None,
               "fired_by": trace.fired[1] if trace.fired else None,
               "reads": [{k: r[k] for k in ("path", "tool", "partial", "step")} for r in trace.reads],
               "runs": trace.runs, "unread": unread, "format": fmt, "available": trace.available,
               "other_copy_loaded": trace.other_copy, "skipped_lines": trace.skipped, "note": note}
        print(json.dumps(out, indent=2))
        return 0
    print(f"format: {fmt}" + (f" ({trace.skipped} unparseable line(s) skipped)" if trace.skipped else "")
          + (" · approximate" if fmt == "text" else ""))
    if note:
        print(f"note: {note}")
    if trace.available is not None:
        print("available: " + ("yes (listed in the session's skills at start)" if trace.available
                               else "no (not in the session's skills at start; it could not fire)"))
    if trace.fired:
        print(f"fired: yes (step {trace.fired[0]}, {trace.fired[1]})")
    else:
        print("fired: no (no Skill call, SKILL.md read, or skill-load line named this skill"
              + ("; a slash-command or --skill load leaves no event in stream-json, so an explicitly invoked run reads as not fired)"
                 if fmt == "stream-json" else ")"))
    if trace.other_copy:
        print(f"warning: a different copy of '{trace.r.name}' loaded: {trace.other_copy}; "
              "the copy under test was shadowed, so this run says nothing about it")
    partial_n = sum(1 for r in trace.reads if r["partial"])
    print(f"reads: {len(trace.reads)} ({partial_n} partial)")
    for i, r in enumerate(trace.reads, 1):
        flag = f"  partial ({r['detail']})" if r["partial"] else ""
        print(f"  {i}. step {r['step']}  {r['path']}  {r['tool']}{flag}")
    print(f"runs: {len(trace.runs)}")
    for i, r in enumerate(trace.runs, 1):
        print(f"  {i}. step {r['step']}  {r['path']}  {r['tool']}")
    print(f"unread: {len(unread)} of {len(files)} bundled files (read or run counts as opened)")
    for f in unread:
        print(f"  {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
