#!/usr/bin/env python3
"""Run one fresh, non-interactive agent session on a prompt and save its transcript.

usage: run_fresh_session.py <workdir> "<prompt>" --out <transcript.jsonl>
                            [--harness claude|pi] [--model M] [--effort E]
                            [--trace <skill-dir>] [--in-place] [--timeout SECONDS]
                            [-- <extra harness flags>]

The session runs in a disposable copy of <workdir> (printed on the first line), so
an observed run cannot change the user's files; --in-place runs in <workdir> itself.
The working directory is set by this script, so no `cd` or environment prefix is
needed in the command that calls it.

claude runs `claude -p <prompt> --output-format stream-json --verbose`; pi runs
`pi --no-session --mode json -p <prompt>`. --model, --effort, and anything after
`--` are passed through. Without extra flags a claude session uses its default
permission mode, in which tools that need approval are denied; pass, for example,
`-- --permission-mode acceptEdits` when the observed task must edit files.

After the session ends the script prints its exit status, model, turns, and cost,
and with --trace runs scripts/trace_skill_use.py on the transcript. For claude it
also copies the session's own log to <out>.session.jsonl: the stream transcript
omits a slash-command skill load, and the session log records it, so --trace reads
both. Before starting, it warns when a skill under test in <workdir>/.claude/skills
has the same name as an installed one, because the installed copy can load instead.

Exit 0 when the session completed, 2 when it could not start (the message is the
reason to report as "observation skipped: <reason>"), 3 when it timed out (the
partial transcript is kept). Python 3 standard library only.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

# A skill-tuning session rarely needs more than this; past it the run is stuck, not slow.
DEFAULT_TIMEOUT = 1800
# Directories never copied into the scratch workspace: large, generated, or unrelated to the task.
COPY_IGNORE = shutil.ignore_patterns("node_modules", ".venv", "__pycache__", ".DS_Store")
HARNESSES = {
    "claude": lambda prompt: ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose"],
    "pi": lambda prompt: ["pi", "--no-session", "--mode", "json", "-p", prompt],
}
# Where installed skills live; a same-named one there can shadow the copy under test.
GLOBAL_SKILL_ROOTS = ("~/.claude/skills", "~/.agents/skills")
# Where Claude Code keeps each session's own log, one directory per working directory.
CLAUDE_PROJECTS = "~/.claude/projects"
# Result text Claude Code prints when it cannot reach a model; the run never started.
NOT_STARTED = ("Not logged in", "hit your session limit", "Invalid API key", "credit balance")


def die(code, msg):
    print(f"run_fresh_session: {msg}", file=sys.stderr)
    sys.exit(code)


def parse(argv):
    opts = {"harness": "claude", "model": None, "effort": None, "trace": None, "out": None,
            "in_place": False, "timeout": DEFAULT_TIMEOUT, "extra": []}
    if "--" in argv:
        i = argv.index("--")
        argv, opts["extra"] = argv[:i], argv[i + 1:]
    pos, it = [], iter(argv)
    for a in it:
        if a in ("-h", "--help"):
            print(__doc__.strip())
            sys.exit(0)
        elif a in ("--harness", "--model", "--effort", "--trace", "--out", "--timeout"):
            val = next(it, None)
            if val is None:
                die(2, f"{a} needs a value")
            opts[a[2:]] = val
        elif a == "--in-place":
            opts["in_place"] = True
        elif a.startswith("--"):
            die(2, f"unknown option {a}; put harness flags after a bare --")
        else:
            pos.append(a)
    if len(pos) != 2:
        die(2, f'expected <workdir> "<prompt>", got {len(pos)} positional argument(s). ' + __doc__.strip().split("\n")[2].strip())
    if not opts["out"]:
        die(2, "--out <transcript.jsonl> is required; save it outside <workdir> so the run cannot overwrite it")
    if opts["harness"] not in HARNESSES:
        die(2, f"unknown --harness '{opts['harness']}'; valid: {', '.join(HARNESSES)}")
    try:
        opts["timeout"] = int(opts["timeout"])
    except ValueError:
        die(2, f"--timeout must be whole seconds, got '{opts['timeout']}'")
    return pos[0], pos[1], opts


def shadowed(workdir):
    """Project skills whose name is also installed globally; the global copy may load instead."""
    local = os.path.join(workdir, ".claude", "skills")
    if not os.path.isdir(local):
        return []
    out = []
    for name in sorted(os.listdir(local)):
        for root in GLOBAL_SKILL_ROOTS:
            g = os.path.join(os.path.expanduser(root), name)
            if os.path.isfile(os.path.join(g, "SKILL.md")) and os.path.realpath(g) != os.path.realpath(os.path.join(local, name)):
                out.append((name, os.path.realpath(g)))
                break
    return out


def session_log(transcript):
    """Claude Code's own log for the session in this transcript, or None."""
    sid = None
    with open(transcript, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if isinstance(e, dict) and e.get("session_id"):
                sid = e["session_id"]
                break
    if not sid:
        return None
    base = os.path.expanduser(CLAUDE_PROJECTS)
    for d in os.listdir(base) if os.path.isdir(base) else []:
        f = os.path.join(base, d, sid + ".jsonl")
        if os.path.isfile(f):
            return f
    return None


def summarize(path):
    model = turns = cost = result = None
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if not isinstance(e, dict):
                continue
            if e.get("type") == "system" and e.get("subtype") == "init":
                model = e.get("model")
            elif e.get("type") == "result":
                turns, cost, result = e.get("num_turns"), e.get("total_cost_usd"), e.get("result") or ""
            elif e.get("type") == "message_end" and isinstance(e.get("message"), dict):
                model = e["message"].get("model") or model  # pi names the model on each assistant message
    return model, turns, cost, result


def main(argv):
    workdir, prompt, o = parse(argv)
    if not os.path.isdir(workdir):
        die(2, f"workdir not found: {workdir}")
    binary = HARNESSES[o["harness"]](prompt)[0]
    if shutil.which(binary) is None:
        die(2, f"{binary} is not installed or not on PATH, so no fresh session can run")
    out = os.path.abspath(o["out"])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if o["in_place"]:
        cwd = os.path.abspath(workdir)
    else:
        cwd = os.path.join(tempfile.mkdtemp(prefix="fresh-session-"), os.path.basename(os.path.abspath(workdir)))
        shutil.copytree(workdir, cwd, symlinks=True, ignore=COPY_IGNORE)
    print(f"workspace: {cwd}" + ("" if o["in_place"] else " (disposable copy)"))
    if o["harness"] == "claude":
        for name, g in shadowed(cwd):
            print(f"warning: skill '{name}' is also installed at {g}; that copy may load instead of the one under test. "
                  f"Rename the copy under test (directory and name field) for the run.")

    cmd = HARNESSES[o["harness"]](prompt)
    if o["model"]:
        cmd += ["--model", o["model"]]
    if o["effort"]:
        cmd += ["--effort", o["effort"]] if o["harness"] == "claude" else ["--thinking", o["effort"]]
    cmd += o["extra"]
    err_path = out + ".err"
    with open(out, "w") as fo, open(err_path, "w") as fe:
        try:
            code = subprocess.run(cmd, cwd=cwd, stdout=fo, stderr=fe, stdin=subprocess.DEVNULL,
                                  timeout=o["timeout"]).returncode
        except subprocess.TimeoutExpired:
            print(f"transcript: {out} (partial)")
            die(3, f"session exceeded {o['timeout']}s and was stopped; the partial transcript is kept")
    print(f"transcript: {out}")
    model, turns, cost, result = summarize(out)
    if result and any(s in result for s in NOT_STARTED):
        die(2, f"the session could not reach a model: {result.strip()[:200]}")
    if os.path.getsize(out) == 0:
        tail = open(err_path, encoding="utf-8", errors="replace").read().strip()[-300:]
        die(2, f"{binary} exited {code} with an empty transcript" + (f": {tail}" if tail else ""))
    print(f"exit: {code} · model: {model or 'unknown'} · turns: {turns if turns is not None else 'n/a'}"
          + (f" · cost: ${cost:.2f}" if isinstance(cost, (int, float)) else ""))
    log = session_log(out) if o["harness"] == "claude" else None
    if log:
        shutil.copyfile(log, out + ".session.jsonl")
        print(f"session log: {out}.session.jsonl")
    if o["trace"]:
        tracer = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trace_skill_use.py")
        print("--- trace: transcript ---", flush=True)
        subprocess.run([sys.executable, tracer, o["trace"], out])
        if log:
            print("--- trace: session log (records slash-command loads) ---", flush=True)
            subprocess.run([sys.executable, tracer, o["trace"], out + ".session.jsonl", "--format", "stream-json"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
