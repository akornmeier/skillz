#!/usr/bin/env python3
"""Self-test for scripts/trace_skill_use.py. Run: python3 evals/fixtures/test_trace.py

Checks the two fixture transcripts and the shell-command classifier. The fixtures
were recorded with absolute skill paths from one machine; they are rewritten to
this checkout's skill directory before parsing, so the test runs anywhere.
Python 3 standard library only. Exit 0 when every check passes, 1 otherwise.
"""
import io
import json
import os
import sys
import tempfile
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.realpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(SKILL, "scripts"))
import trace_skill_use as t  # noqa: E402

# The skill paths the fixtures were recorded with.
RECORDED = ("/Users/tk/.claude/skills/authoring-skills", "/Users/tk/.agents/skills/authoring-skills")
failures = []


def check(label, cond, got=None):
    print(("ok   " if cond else "FAIL ") + label + ("" if cond else f"  (got {got})"))
    if not cond:
        failures.append(label)


def trace_fixture(name):
    text = open(os.path.join(HERE, name), encoding="utf-8").read()
    for old in RECORDED:
        text = text.replace(old, SKILL)
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as fh:
        fh.write(text)
    out = io.StringIO()
    with redirect_stdout(out):
        t.main([SKILL, fh.name, "--json"])
    os.unlink(fh.name)
    return json.loads(out.getvalue())


d = trace_fixture("trace-sample.jsonl")
check("stream-json fixture: format", d["format"] == "stream-json", d["format"])
check("stream-json fixture: fired at step 1", d["fired"] and d["fired_step"] == 1, d["fired_step"])
check("stream-json fixture: four reads", len(d["reads"]) == 4, len(d["reads"]))
check("stream-json fixture: one partial read", sum(r["partial"] for r in d["reads"]) == 1)
check("stream-json fixture: linter counted as a run", [r["path"] for r in d["runs"]] == ["scripts/lint_skill.py"])

d = trace_fixture("trace-sample-pi.jsonl")
check("pi-json fixture: format detected", d["format"] == "pi-json", d["format"])
check("pi-json fixture: three reads, one partial",
      len(d["reads"]) == 3 and sum(r["partial"] for r in d["reads"]) == 1, d["reads"])
check("pi-json fixture: one run", len(d["runs"]) == 1)

# Shell classifier: (command, expected) where expected is (path, partial), "run", or None for no read.
CASES = [
    ("cat {D}/references/review-rubric.md", ("references/review-rubric.md", False)),
    ("sed -n '34,68p;110,220p' {D}/references/authoring-guidelines.md", ("references/authoring-guidelines.md", True)),
    ('echo "=== templates/SKILL.md ===" && cat {D}/templates/SKILL.md', ("templates/SKILL.md", False)),
    ("B={D}; cat $B/references/review-rubric.md", ("references/review-rubric.md", False)),
    ("cat ${{B}}/x; B={D}; cat ${{B}}/workflows/create-skill.md", ("workflows/create-skill.md", False)),
    ("cat {D}/references/tuning-diagnostics.md | head -40", ("references/tuning-diagnostics.md", True)),
    ("grep -n '^#' {D}/references/authoring-guidelines.md", ("references/authoring-guidelines.md", True)),
    ("wc -c {D}/SKILL.md", None),
    ("python3 {D}/scripts/lint_skill.py target", "run"),
    ("head -5 {D}/scripts/lint_skill.py", ("scripts/lint_skill.py", True)),
]
for cmd, want in CASES:
    cmd = cmd.format(D=SKILL)
    tr = t.Trace(t.Resolver(SKILL, t.bundled_files(SKILL)))
    tr.tool_use("Bash", {"command": cmd})
    if tr.runs:
        got = "run"
    elif len(tr.reads) == 1:
        got = (tr.reads[0]["path"], tr.reads[0]["partial"])
    else:
        got = None if not tr.reads else [(r["path"], r["partial"]) for r in tr.reads]
    check("shell: " + cmd.replace(SKILL, "<skill>"), got == want, got)

print(f"\n{'all checks passed' if not failures else str(len(failures)) + ' check(s) failed'}")
sys.exit(1 if failures else 0)
