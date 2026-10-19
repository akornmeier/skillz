#!/usr/bin/env python3
"""Report skill delivery from Claude stream/session JSON, Pi JSON, or uncertain text.

usage: trace_skill_use.py <skill-dir> <transcript> [--format stream-json|pi-json|text] [--json]

Correlate requests with results. Writes, edits, failed reads, and script execution
are not loading. Missing results and opaque codemode calls remain unknown. A
successful read proves delivery, not automatic discovery or task success. Read
windows record navigation, not whether the needed information was sufficient.
Copies match only when their complete file manifests match the explicit target.
Digests describe files at analysis time, not historical transcript-time bytes.
Exit 0 for a report, 2 for unreadable inputs. Python standard library only.
"""
import argparse
import hashlib
import json
import os
import re
import shlex
import sys
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", "__pycache__"}
SKILL_LOAD_RE = re.compile(r"Base directory for this skill:[ \t]*([^\r\n]+)")
FILE_TOOLS = {"Read": "read", "read": "read", "Write": "write", "write": "write",
              "Edit": "edit", "edit": "edit", "Grep": "search", "Glob": "search"}
SHELL_TOOLS = {"Bash", "bash", "shell"}
# These commands report names/metadata, not file instruction content.
METADATA_COMMANDS = {"stat", "wc", "ls", "test", "du", "file", "echo", "printf"}


def manifest_digest(root):
    """Hash relative names and bytes, including eval definitions; reject unsafe links."""
    root = Path(root).resolve(strict=True)
    entries = []
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in dirs + sorted(files):
            path = Path(base) / name
            if path.is_symlink():
                raise ValueError(f"skill manifest contains a symlink: {path}")
        for name in sorted(files):
            path = Path(base) / name
            entries.append((path.relative_to(root).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()))
    return hashlib.sha256(json.dumps(sorted(entries), ensure_ascii=False).encode()).hexdigest()


def bundled_files(skill_dir):
    return sorted(str(p.relative_to(skill_dir)) for p in Path(skill_dir).rglob("*")
                  if p.is_file() and not any(x in SKIP_DIRS | {"evals"} or x.startswith(".")
                                             for x in p.relative_to(skill_dir).parts))


class Resolver:
    def __init__(self, skill_dir, files):
        self.root = Path(skill_dir).resolve(strict=True)
        self.name = self.root.name
        self.files = set(files)
        self.digest = manifest_digest(self.root)
        content = (self.root / "SKILL.md").read_text(encoding="utf-8-sig")
        header = re.match(r"\A---\n.*?\n---[ \t]*(?:\n|$)", content, re.S)
        # Extract the frozen instructions for delivery comparison, not YAML validation.
        self.instructions = content[header.end():].strip() if header else content.strip()
        self.cwd = None

    def match(self, token):
        """Return (relative path, identity): (None, None) is unrelated/unresolved;
        (path, None) identifies a plausible copy whose manifest is unavailable.
        """
        if not isinstance(token, str):
            return None, None
        path = Path(token).expanduser()
        if not path.is_absolute():
            if self.cwd is None:
                return None, None
            path = self.cwd / path
        path = path.resolve()
        try:
            rel = path.relative_to(self.root).as_posix()
            return (rel, True) if rel in self.files else (None, None)
        except ValueError:
            pass
        for parent in path.parents:
            rel = path.relative_to(parent).as_posix()
            if rel not in self.files:
                continue
            same_name = parent.name == self.name
            if (parent / "SKILL.md").is_file():
                try:
                    if manifest_digest(parent) == self.digest:
                        return rel, True
                    if same_name:
                        return rel, False
                except (OSError, ValueError):
                    if same_name:
                        return rel, None
            elif same_name:
                return rel, None  # Saved evidence may outlive its temporary workspace.
        return None, None

    def directory(self, token):
        return self.match(str(Path(token) / "SKILL.md"))


def result_text(result):
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        return result_text(result.get("content", []))
    if isinstance(result, list):
        return "\n".join(b.get("text", "") for b in result
                         if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str))
    return ""


class Trace:
    def __init__(self, resolver):
        self.r = resolver
        self.step = 0
        self.pending = {}
        self.results = {}
        self.reads, self.runs, self.events = [], [], []
        self.fired = None
        self.mechanism = "none"
        self.target_match = None
        self.skipped = 0
        self.available = None
        self.other_copy = None
        self.complete = False
        self.recognized = False
        self.uncertain = False
        self.limitations = ["Delivery evidence is not proof of automatic discovery or task success.",
                            "Manifest identity describes files at analysis time; preserve revision snapshots."]

    def unknown(self, why):
        self.uncertain = True
        if why not in self.limitations:
            self.limitations.append(why)

    def fire(self, step, mechanism, reason):
        if self.fired is None:
            self.fired = (step, reason)
            self.mechanism = mechanism
        self.target_match = True

    def start(self, call_id, name, inp):
        if isinstance(call_id, str) and call_id in self.pending:
            if self.pending[call_id][1:] != (name, inp):
                self.pending[call_id] = (self.pending[call_id][0], "conflicting", {})
                self.unknown("Conflicting requests reuse a tool ID.")
            return
        self.step += 1
        if not isinstance(name, str) or not name.strip():
            self.unknown("Tool request name is malformed.")
            name = ""
        if not isinstance(inp, dict):
            self.unknown("Tool request arguments are malformed.")
            inp = {}
        if not isinstance(call_id, str) or not call_id:
            call_id = f"missing-id-{self.step}"
            self.unknown("Tool requests without valid IDs cannot be correlated.")
        self.pending[call_id] = (self.step, name, inp)
        if name.split(".")[-1] == "codemode":
            self.unknown("Opaque codemode source is not execution evidence; only visible nested events count.")

    def end(self, call_id, result, error):
        result = result_text(result)
        if not isinstance(call_id, str) or not call_id:
            self.unknown("Tool results without valid IDs cannot be correlated.")
        elif call_id not in self.results:
            self.results[call_id] = (result, error)
        elif self.results[call_id] != (result, error):
            self.results[call_id] = (None, None)
            self.unknown("Conflicting results reuse a tool ID.")

    def delivery(self, path, step, tool, outcome, requested=None, partial=False, mechanism="read"):
        rel, match = self.r.match(path)
        if rel is None:
            # Relative reads without a known cwd may have addressed the target.
            if not Path(path).is_absolute() and self.r.cwd is None:
                self.unknown("Relative tool paths lack a recorded working directory.")
            return
        item = {"path": rel, "tool": tool, "partial": partial, "step": step,
                "outcome": outcome, "requestedRange": requested or {}, "targetMatch": match}
        self.reads.append(item)
        if outcome == "unknown":
            self.unknown("A relevant read has no confirmed successful content result.")
        if match is None and outcome != "failed":
            self.unknown("Candidate copy manifest is unavailable; historical target identity is unknown.")
        if match is False:
            if outcome == "success":
                self.other_copy = str(Path(path).parent) if rel == "SKILL.md" else str(path)
                if self.target_match is not True:
                    self.target_match = False
            return
        if rel == "SKILL.md" and match and outcome == "success":
            self.fire(step, mechanism, f"{tool} SKILL.md")

    def injected(self, text, fmt):
        """Verify Pi 1.3.0's skill-expansion envelope and frozen instruction text."""
        if "<skill" not in text:
            return
        frame = re.match(r'\A<skill name="([^"]+)" location="([^"]+)">\n', text)
        if fmt == "pi-json" and frame:
            name, path = frame.groups()
            rel, match = self.r.match(path)
            if name == self.r.name and rel == "SKILL.md" and match is True and Path(path).is_absolute():
                # Matches agent-session._expandSkillCommand, including its optional request suffix.
                expected = (f'<skill name="{name}" location="{path}">\n'
                            f'References are relative to {Path(path).parent}.\n\n'
                            f'{self.r.instructions}\n</skill>')
                if text == expected or text.startswith(expected + "\n\n"):
                    self.delivery(path, 0, "injected", "success", mechanism="injected")
                    return
        self.unknown("Unverified skill markup is not confirmed client injection or target delivery.")

    def shell(self, command, step, tool, outcome):
        """Conservative classification, not shell interpretation or per-file proof."""
        if not isinstance(command, str):
            self.unknown("Shell command is not a string.")
            return
        try:
            parts = shlex.split(command)
        except ValueError:
            self.unknown("Unparseable shell command.")
            return
        if not parts:
            return
        cmd = Path(parts[0]).name
        read_command = cmd in {"cat", "head", "tail", "sed", "grep", "rg", "awk"}
        # Compound commands cannot attribute overall exit/output to any one file.
        compound = any(c in command for c in (";", "|", "&&", "$", ">", "<", "`", "\n"))
        if compound:
            self.unknown("Compound/expanded shell commands cannot prove absence of skill delivery.")
        for token in parts[1:]:
            rel, match = self.r.match(token)
            if rel is None:
                if read_command and self.r.cwd is None and not token.startswith("-") and not Path(token).is_absolute():
                    self.unknown("Relative shell-read operands lack a recorded working directory.")
                continue
            if cmd in {"python", "python3", "node", "bash", "sh", "zsh", "deno", "bun"}:
                self.runs.append({"path": rel, "tool": tool, "step": step, "outcome": outcome,
                                  "targetMatch": match})
            elif read_command:
                # A shell result alone does not prove which file's bytes were returned.
                read_outcome = "failed" if outcome == "failed" else "unknown"
                self.delivery(token, step, tool, read_outcome, partial=cmd != "cat")
                self.unknown("Shell file reads lack per-file content attribution" + (" (compound command)." if compound else "."))
            elif cmd not in METADATA_COMMANDS and outcome != "failed":
                self.unknown("Unclassified shell command references target files; content delivery is unresolved.")

    def finish(self):
        if self.results.keys() - self.pending.keys():
            self.unknown("Tool results lack matching requests; incomplete evidence cannot prove non-activation.")
        for call_id, (step, name, inp) in self.pending.items():
            result, error = self.results.get(call_id, (None, None))
            content = result_text(result)
            outcome = "failed" if error is True else "success" if error is False and content else "unknown"
            short = name.split(".")[-1]
            kind = FILE_TOOLS.get(short)
            if kind:
                path = inp.get("path", inp.get("file_path"))
                if not isinstance(path, str):
                    self.unknown("File tool request has no usable path.")
                    continue
                if kind == "read":
                    window = {k: inp[k] for k in ("offset", "limit") if inp.get(k) is not None}
                    self.delivery(path, step, name, outcome, window, bool(window))
                else:
                    rel, match = self.r.match(path)
                    self.events.append({"kind": kind, "path": rel, "step": step, "targetMatch": match,
                                        "outcome": outcome})
            elif short in SHELL_TOOLS:
                self.shell(inp.get("command", inp.get("cmd", "")), step, name, outcome)
            elif short.lower() == "skill":
                skill = inp.get("skill", inp.get("name", ""))
                if not isinstance(skill, str) or skill.split(":")[-1] != self.r.name:
                    continue
                roots = [root.strip() for root in SKILL_LOAD_RE.findall(content) if root.strip()]
                if outcome == "success" and roots:
                    for root in roots:
                        self.delivery(str(Path(root) / "SKILL.md"), step, name, outcome, mechanism="skill-tool")
                elif outcome != "failed":
                    self.unknown("Skill tool result does not confirm the loaded target path.")
        self.reads.sort(key=lambda r: r["step"])

    def report(self, fmt, files):
        self.finish()
        if not self.complete:
            self.unknown("Transcript lacks a terminal session event.")
        fired = True if self.fired else None if self.uncertain or self.skipped or not self.recognized else False
        touched = {r["path"] for r in self.reads + self.runs if r["outcome"] == "success" and r["targetMatch"]}
        return {"fired": fired, "fired_step": self.fired[0] if self.fired else None,
                "fired_by": self.fired[1] if self.fired else None, "reads": self.reads, "runs": self.runs,
                "events": self.events, "unread": [f for f in files if f not in touched], "format": fmt,
                "available": self.available, "other_copy_loaded": self.other_copy, "skipped_lines": self.skipped,
                "note": "text evidence is approximate" if fmt == "text" else None,
                "loadMechanism": self.mechanism if fired is not None else "unknown",
                "targetMatch": self.target_match, "targetDigest": self.r.digest, "limitations": self.limitations}


def parse_json(lines, trace, fmt):
    for raw in lines:
        if not raw.strip():
            continue
        try:
            e = json.loads(raw)
        except ValueError:
            trace.skipped += 1
            continue
        if not isinstance(e, dict):
            trace.skipped += 1
            continue
        kind = e.get("type")
        if kind in {"session", "system", "tool_execution_start", "tool_execution_end", "assistant", "user", "message"}:
            trace.recognized = True
        if kind in {"session", "system"} and isinstance(e.get("cwd"), str):
            trace.r.cwd = Path(e["cwd"])
        if kind == "system" and e.get("subtype") == "init" and isinstance(e.get("skills"), list):
            trace.available = trace.r.name in e["skills"]
        if (fmt == "pi-json" and kind == "agent_settled") or (fmt == "stream-json" and kind == "result"):
            trace.complete = True
        if kind == "tool_execution_start":
            trace.start(e.get("toolCallId"), e.get("toolName"), e.get("args"))
        elif kind == "tool_execution_end":
            trace.end(e.get("toolCallId"), e.get("result"), e.get("isError"))
        if kind not in {"assistant", "user", "message", "message_end", "turn_end"}:
            continue
        msg = e.get("message", e)
        if not isinstance(msg, dict):
            trace.unknown("Supported message envelope is malformed.")
            continue
        role = msg.get("role", kind if kind in {"assistant", "user"} else None)
        if not isinstance(role, str) or role not in {"user", "assistant", "system", "toolResult"}:
            trace.unknown("Supported message role is malformed or unrecognized.")
            continue
        if role == "toolResult":
            trace.end(msg.get("toolCallId"), msg.get("content"), msg.get("isError", False))
        content = msg.get("content")
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        if not isinstance(content, list):
            trace.unknown("Supported message content is malformed or missing.")
            continue
        for b in content:
            if not isinstance(b, dict) or not isinstance(b.get("type"), str) or not b["type"].strip():
                trace.unknown("Supported message content block is malformed.")
                continue
            if b["type"] == "text" and not isinstance(b.get("text"), str):
                trace.unknown("Message text block is malformed.")
                continue
            if b.get("type") in {"tool_use", "toolCall"}:
                trace.start(b.get("id"), b.get("name"), b.get("input", b.get("arguments")))
            elif b.get("type") == "tool_result":
                trace.end(b.get("tool_use_id"), b.get("content"), bool(b.get("is_error", False)))
            elif b.get("type") == "text" and role == "user":
                trace.injected(b["text"], fmt)
            elif b["type"] not in {"text", "thinking", "redacted_thinking", "image"}:
                trace.unknown("Unrecognized message block cannot prove absence of delivery.")


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir")
    parser.add_argument("transcript")
    parser.add_argument("--format", choices=("stream-json", "pi-json", "text"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if not (Path(args.skill_dir) / "SKILL.md").is_file():
            raise ValueError(f"no SKILL.md in {args.skill_dir}")
        lines = Path(args.transcript).read_text(encoding="utf-8").split("\n")
        first = next((line for line in lines if line.strip()), None)
        if first is None:
            raise ValueError("transcript is empty")
        fmt = args.format
        if fmt is None:
            try:
                head = json.loads(first)
                fmt = "pi-json" if isinstance(head, dict) and head.get("type") == "session" else "stream-json"
            except ValueError:
                fmt = "text"
        files = bundled_files(args.skill_dir)
        trace = Trace(Resolver(args.skill_dir, files))
        if fmt == "text":
            trace.unknown("Text mentions do not prove successful reads, loads, identity, or absence of loading.")
        else:
            parse_json(lines, trace, fmt)
        report = trace.report(fmt, files)
    except (OSError, ValueError) as exc:
        print(f"trace_skill_use: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"format: {fmt}\nfired: {report['fired']} · mechanism: {report['loadMechanism']} · target match: {report['targetMatch']}")
        for r in report["reads"]:
            print(f"  step {r['step']}: {r['path']} · {r['outcome']} · range {r['requestedRange']}")
        print(f"runs: {len(report['runs'])} · unread/unconfirmed: {len(report['unread'])}")
        for limitation in report["limitations"]:
            print(f"limitation: {limitation}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
