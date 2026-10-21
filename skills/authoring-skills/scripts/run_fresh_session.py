#!/usr/bin/env python3
"""Capture one fresh agent session, with truthful process outcomes and identity.

usage: run_fresh_session.py <workdir> "<prompt>" --out <transcript.jsonl> [options]

Real launches require --allow-live AFTER human approval of model, spend/time,
permissions, and run count. This flag records intent; it cannot enforce approval.
Default: copied files, fresh harness context, maximum depth one, one launch.
A copy is NOT a security sandbox or isolated skill discovery. This runner has no
verified containment/discovery adapter: requested guarantees and --qualification
fail closed. External shell/network/MCP effects are not restricted by this script.
Contained symlinks are rejected too, rather than copied back into the source.

--trace requires an exact skill directory. A manifest digest is recorded; same-name
conflicting project/global copies block launch. No config or credentials are copied
from the user's home to make a test pass. Transcript/stderr remain primary evidence;
<out>.summary.json records capture facts, NOT behavioral assertions or a task pass.

Exit 0 completed capture, 1 harness/capture/trace failure, 2 blocked preflight/startup,
3 timed out. SIGTERM and keyboard interruptions stop/reap the child and propagate
the termination after recording capture state; prior signal handlers are restored. Partial evidence is retained. Outputs must be new, outside the fixture.
--in-place is explicitly mutating and never valid for qualification. A separately
approved nested run may use --max-depth 2 and a shared --run-budget; depth/count
sentinels coordinate cooperative runners, not untrusted children. Standard library;
process-group timeout and locked budgets require POSIX. No paid calls in tests.
"""
import argparse
from contextlib import ExitStack
from copy import deepcopy
import fcntl
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

from trace_skill_use import manifest_digest, raise_walk_error

# Per-child ceiling; operator must approve the actual time/spend limit before launch.
DEFAULT_TIMEOUT = 1800
COPY_IGNORE = shutil.ignore_patterns("node_modules", ".venv", "__pycache__", ".DS_Store")
HARNESSES = {
    "claude": lambda prompt: ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose"],
    "pi": lambda prompt: ["pi", "--no-session", "--mode", "json", "-p", prompt],
}
# Preserve Claude's supplemental session evidence; never copy home configuration.
CLAUDE_PROJECTS = "~/.claude/projects"
GLOBAL_SKILL_ROOTS = ("~/.claude/skills", "~/.agents/skills", "~/.pi/agent/skills")
PROJECT_SKILL_ROOTS = (".claude/skills", ".agents/skills", ".pi/skills")
NOT_STARTED = ("not logged in", "hit your session limit", "invalid api key", "credit balance")
DEPTH_ENV = "AUTHORING_SKILLS_RUN_DEPTH"
MAX_DEPTH_ENV = "AUTHORING_SKILLS_MAX_DEPTH"
BUDGET_ENV = "AUTHORING_SKILLS_BUDGET_FILE"


class Blocked(Exception):
    """Preflight/startup prerequisites are not satisfied."""


class Terminated(BaseException):
    """Unwind capture cleanup before forwarding a termination signal."""
    def __init__(self, signum):
        super().__init__(signum)
        self.signum = signum


def terminate_capture(signum, frame):
    raise Terminated(signum)


def parse(argv):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("workdir")
    p.add_argument("prompt")
    p.add_argument("--out", required=True)
    p.add_argument("--harness", choices=HARNESSES, default="claude")
    p.add_argument("--model")
    p.add_argument("--effort")
    p.add_argument("--trace")
    p.add_argument("--invocation-mode", choices=("automatic", "explicit", "unknown"), default="unknown")
    p.add_argument("--timeout", default=str(DEFAULT_TIMEOUT))
    p.add_argument("--max-depth", default="1")
    p.add_argument("--run-budget", default="1")
    for flag in ("allow-live", "in-place", "qualification", "require-skill-isolation", "require-containment"):
        p.add_argument("--" + flag, action="store_true")
    extra = []
    if "--" in argv:
        index = argv.index("--")
        argv, extra = argv[:index], argv[index + 1:]
    o = p.parse_args(argv)
    o.extra = extra
    return o


def within(path, root):
    return path == root or root in path.parents


def safe_outputs(out, source):
    """Never write even an error sidecar through a link or into the source tree."""
    paths = [Path(str(out) + suffix) for suffix in ("", ".err", ".summary.json", ".trace.json", ".session.jsonl", ".budget.json")]
    for path in paths:
        resolved = path.resolve()
        if within(resolved, source) or path.is_symlink():
            raise Blocked("output or sidecar collides with source or uses a symlink; choose an external real path")
        if path.exists():
            raise Blocked("output artifacts already exist; choose a new --out path")
    return paths


def check_fixture(root):
    if root.is_symlink():
        raise Blocked("symlinked workspace roots are unsupported")
    if not root.is_dir():
        raise Blocked("workdir is not a directory")
    for base, dirs, files in os.walk(root, onerror=raise_walk_error):
        for name in dirs + files:
            path = Path(base) / name
            if path.is_symlink():
                raise Blocked("workspace symlinks are unsupported (including contained, escaping, and dangling links)")
            if not path.is_dir() and not path.is_file():
                raise Blocked("workspace contains a special file")


def check_target(target, source, digest):
    """Known locations are a collision check, never proof of full discovery isolation."""
    if not (target / "SKILL.md").is_file():
        raise Blocked("--trace requires an exact directory containing SKILL.md")
    roots = [Path(p).expanduser() for p in GLOBAL_SKILL_ROOTS]
    for ancestor in (source, *source.parents):
        roots.extend(ancestor / p for p in PROJECT_SKILL_ROOTS)
    for root in roots:
        candidate = root / target.name
        if candidate.resolve() != target and (candidate / "SKILL.md").is_file():
            if manifest_digest(candidate) != digest:
                raise Blocked("a conflicting same-name skill copy is discoverable; isolate configuration before evaluation")


def positive_int(value, label):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise Blocked(f"{label} must be a positive integer") from None
    if number < 1:
        raise Blocked(f"{label} must be positive")
    return number


def consume_budget(path):
    """Reserve one attempted launch across cooperating nested/sibling runners."""
    with open(path, "r+", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        budget = json.load(fh)
        if not isinstance(budget.get("remaining"), int) or budget["remaining"] < 1:
            raise Blocked("approved shared launch budget exhausted")
        budget["remaining"] -= 1
        fh.seek(0)
        json.dump(budget, fh)
        fh.truncate()
        return budget


def run_child(cmd, cwd, out, err, timeout, env):
    """Stop the owned group when its harness ends; preserve parent status and output."""
    with open(out, "x", encoding="utf-8") as fo, open(err, "x", encoding="utf-8") as fe:
        child = None
        pending = {}
        def defer_signal(signum, frame):
            pending[signum] = frame
        # Do not unwind Popen before it returns the child handle needed for
        # cleanup. Preserve ignored SIGINT in the child too; exec resets caught handlers.
        previous = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT)}
        try:
            try:
                with ExitStack() as restore:
                    for sig, handler in previous.items():
                        if sig == signal.SIGINT and handler == signal.SIG_IGN:
                            continue
                        restore.callback(signal.signal, sig, handler)
                        signal.signal(sig, defer_signal)
                    child = subprocess.Popen(cmd, cwd=cwd, stdout=fo, stderr=fe, stdin=subprocess.DEVNULL,
                                             env=env, start_new_session=True)
            finally:
                if signal.SIGTERM in pending:
                    raise Terminated(signal.SIGTERM)
                if signal.SIGINT in pending:
                    handler = previous[signal.SIGINT]
                    if callable(handler):
                        handler(signal.SIGINT, pending[signal.SIGINT])
                    else:
                        raise KeyboardInterrupt
            return child.wait(timeout=timeout)
        finally:
            # Parent exit, success or failure, does not imply its workers exited.
            if child is not None:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                child.wait()


def session_log(transcript):
    """Locate only the Claude log named by this capture's validated session ID."""
    sid = None
    for line in Path(transcript).read_text(encoding="utf-8").split("\n"):
        if not line.strip():
            continue
        event = json.loads(line)
        if isinstance(event, dict) and isinstance(event.get("session_id"), str):
            sid = event["session_id"]
            break
    if not sid or not re.fullmatch(r"[A-Za-z0-9-]+", sid):
        return None
    base = Path(CLAUDE_PROJECTS).expanduser()
    if base.is_dir():
        for project in sorted(base.iterdir()):
            log = project / (sid + ".jsonl")
            if log.is_file() and not log.is_symlink():
                return log
    return None


def inspect_capture(path, harness):
    """Classify final capture state, retaining unrecovered errors and incomplete retries."""
    terminal = False
    observed_model = turns = cost = None
    pi_error = None
    retry_open = False
    for line in Path(path).read_text(encoding="utf-8").split("\n"):
        if not line.strip():
            continue
        e = json.loads(line)
        if not isinstance(e, dict):
            raise ValueError("capture contains a non-object event")
        kind = e.get("type")
        if kind == "result":
            turns, cost = e.get("num_turns"), e.get("total_cost_usd")
            text = e.get("result", "")
            error = e.get("is_error", False)
            if error is not True and error is not False:
                raise ValueError("harness result status is not boolean")
            failed = error or e.get("subtype") not in (None, "success")
            if failed:
                if isinstance(text, str) and any(s in text.lower() for s in NOT_STARTED):
                    raise Blocked("harness authentication/quota preflight failed; inspect primary evidence securely")
                raise ValueError("harness reported an error result")
            terminal = harness == "claude" or terminal
        if harness == "pi":
            if kind in ("agent_start", "turn_start", "message_start", "message_end", "turn_end",
                        "tool_execution_start", "tool_execution_end"):
                terminal = False
            if kind == "agent_end" and "willRetry" in e:
                if e["willRetry"] is not True and e["willRetry"] is not False:
                    raise ValueError("harness retry intent is not boolean")
            if kind == "auto_retry_start" or (kind == "agent_end" and e.get("willRetry") is True):
                retry_open = True
                terminal = False
                pi_error = pi_error or "retry has no successful response"
            elif kind == "auto_retry_end":
                success = e.get("success")
                if success is not True and success is not False:
                    raise ValueError("harness retry status is not boolean")
                if not retry_open:
                    raise ValueError("harness retry completion has no pending retry")
                retry_open = False
                if success is False:
                    error = e.get("finalError")
                    pi_error = error if isinstance(error, str) and error else pi_error or "retry failed"
            elif kind == "agent_settled":
                aborted = e.get("aborted", False)
                if aborted is not True and aborted is not False:
                    raise ValueError("harness settlement status is not boolean")
                if aborted:
                    raise ValueError("harness session was aborted")
                terminal = True
        msg = e.get("message")
        if isinstance(msg, dict) and msg.get("role") == "assistant":
            observed_model = msg.get("model") or observed_model
            # Partial streaming snapshots cannot supersede a completed response.
            authoritative = harness != "pi" or kind in {"message_end", "turn_end", "message"}
            if authoritative:
                stop = msg.get("stopReason")
                if stop == "aborted":
                    raise ValueError("assistant response was aborted")
                if stop == "error":
                    error = msg.get("errorMessage")
                    error = error if isinstance(error, str) else "assistant response failed"
                    if harness == "pi":
                        pi_error = error
                    elif any(s in error.lower() for s in NOT_STARTED):
                        raise Blocked("harness authentication/quota preflight failed; inspect primary evidence securely")
                    else:
                        raise ValueError("assistant response failed")
                elif harness == "pi" and stop in ("stop", "toolUse", "length"):
                    # Recovery can be automatic retry, compaction, or continuation.
                    # Completion still requires a settled session and closed retry.
                    pi_error = None
        if kind == "system" and e.get("subtype") == "init":
            observed_model = e.get("model") or observed_model
    if pi_error is not None:
        if any(s in pi_error.lower() for s in NOT_STARTED):
            raise Blocked("harness authentication/quota preflight failed; inspect primary evidence securely")
        raise ValueError("assistant response failed or retry did not recover")
    if retry_open:
        raise ValueError("harness retry did not complete")
    if not terminal:
        raise ValueError("capture is empty or lacks a supported terminal event")
    return {"observedModel": observed_model, "turns": turns, "costUSD": cost}


def trace_capture(target, out):
    tracer = Path(__file__).with_name("trace_skill_use.py")
    result = subprocess.run([sys.executable, str(tracer), str(target), str(out), "--json"],
                            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise ValueError("tracer failed; inspect transcript before making activation claims")
    report = json.loads(result.stdout)
    if not isinstance(report, dict) or "fired" not in report:
        raise ValueError("tracer returned an invalid report")
    return report


def main(argv):
    previous = signal.signal(signal.SIGTERM, terminate_capture)
    try:
        try:
            return capture(argv)
        finally:
            signal.signal(signal.SIGTERM, previous)
    except Terminated as exc:
        # Preserve native signal status after cleanup, or the shell convention
        # if a caller's restored handler handles/ignores the forwarded signal.
        signal.raise_signal(exc.signum)
        return 128 + exc.signum


def capture(argv):
    o = parse(argv)
    source = Path(o.workdir).expanduser().absolute()
    out = Path(o.out).expanduser().absolute()
    # Canonicalize parent aliases (e.g. macOS /var), not the root/file itself.
    source = source.parent.resolve() / source.name
    out = out.parent.resolve() / out.name
    # Unsafe output locations are the only attempted-capture failures without a
    # sidecar: writing that sidecar would itself violate the source boundary.
    try:
        safe_outputs(out, source.resolve())
        out.parent.mkdir(parents=True, exist_ok=True)
    except (OSError, Blocked) as exc:
        print(f"run_fresh_session: blocked: {exc}; no artifacts written", file=sys.stderr)
        return 2
    summary = {"schema": 1, "outcome": "blocked", "childExit": None, "reason": None,
               "harness": o.harness, "model": o.model, "thinking": o.effort,
               "invocationMode": o.invocation_mode, "targetPath": None, "targetDigest": None,
               "workspace": None, "depth": None, "approvedRunBudget": None,
               "limitations": ["Workspace copying is not a security sandbox.",
                               "Skill discovery and external shell/network/MCP effects are not isolated.",
                               "--allow-live and recursion sentinels do not enforce human authorization.",
                               "Capture completion is not a task pass; invocation mode records intended setup.",
                               "No verified harness-specific discovery/containment adapter is installed."]}
    scratch = None
    child_started = False
    code = 2
    try:
        timeout = positive_int(o.timeout, "--timeout")
        maximum = positive_int(o.max_depth, "--max-depth")
        budget = positive_int(o.run_budget, "--run-budget")
        parent_depth = int(os.environ.get(DEPTH_ENV, "0"))
        if parent_depth < 0:
            raise Blocked("invalid parent depth")
        depth = parent_depth + 1
        if maximum > 2:
            raise Blocked("--max-depth cannot exceed two, even with approval")
        maximum = min(maximum, positive_int(os.environ.get(MAX_DEPTH_ENV, str(maximum)), MAX_DEPTH_ENV))
        summary.update(depth=depth, approvedRunBudget=budget, timeoutSeconds=timeout, maximumDepth=maximum)
        if depth > maximum:
            raise Blocked("nested run exceeds approved depth cap")
        if not o.allow_live:
            raise Blocked("real harness launch requires human approval and --allow-live")
        check_fixture(source)
        source = source.resolve()
        if o.qualification or o.require_skill_isolation or o.require_containment:
            raise Blocked("required discovery isolation/security containment has no verified adapter; qualification blocked")
        # Extra flags may change context/permissions/discovery. Treat them as
        # operator-approved ordinary capture configuration, never qualification.
        if o.extra:
            summary["limitations"].append("Extra harness flags were supplied; their guarantees are unverified (values not persisted).")
        target = Path(o.trace).expanduser().resolve(strict=True) if o.trace else None
        if target:
            digest = manifest_digest(target)
            summary.update(targetPath=str(target), targetDigest=digest)
            check_target(target, source.resolve(), digest)
        cmd = HARNESSES[o.harness](o.prompt)
        if shutil.which(cmd[0]) is None:
            raise Blocked("harness executable is unavailable")
        if o.model:
            cmd += ["--model", o.model]
        if o.effort:
            cmd += ["--effort" if o.harness == "claude" else "--thinking", o.effort]
        cmd += o.extra
        if o.in_place:
            cwd = source
        else:
            scratch = Path(tempfile.mkdtemp(prefix="fresh-session-"))
            cwd = scratch / source.name
            if within(out.resolve(), scratch):
                raise Blocked("output collides with copied workspace")
            shutil.copytree(source, cwd, ignore=COPY_IGNORE)
            check_fixture(cwd)
        summary["workspace"] = str(cwd)
        if target and within(target, source.resolve()):
            copied_target = cwd / target.relative_to(source.resolve())
            if manifest_digest(copied_target) != summary["targetDigest"]:
                raise Blocked("copied target manifest does not match evaluated source")
        ledger = os.environ.get(BUDGET_ENV)
        if parent_depth and not ledger:
            raise Blocked("nested run has no inherited shared launch budget")
        if not ledger:
            # Kept beside primary artifacts so approved siblings share one counter.
            ledger = str(out) + ".budget.json"
            with open(ledger, "x", encoding="utf-8") as fh:
                json.dump({"remaining": budget, "approved": budget}, fh)
        remaining = consume_budget(ledger)
        summary["approvedRunBudget"] = remaining["approved"]
        summary["remainingRunBudget"] = remaining["remaining"]
        env = dict(os.environ, **{DEPTH_ENV: str(depth), MAX_DEPTH_ENV: str(maximum), BUDGET_ENV: ledger})
        print(f"workspace: {cwd} (not a sandbox)")
        child_started = True
        child_exit = run_child(cmd, str(cwd), str(out), str(out) + ".err", timeout, env)
        summary["childExit"] = child_exit
        # Detect known auth/quota failures before generic nonzero child handling.
        if out.exists():
            try:
                summary.update(inspect_capture(out, o.harness))
            except Blocked:
                raise
            except (OSError, ValueError):
                if child_exit == 0:
                    raise
        if child_exit != 0:
            raise ValueError(f"harness exited {child_exit}; partial evidence retained")
        if not out.exists():
            raise ValueError("harness produced no transcript")
        log = session_log(out) if o.harness == "claude" else None
        if log:
            saved_log = Path(str(out) + ".session.jsonl")
            shutil.copyfile(log, saved_log)
            summary["sessionLog"] = str(saved_log)
        elif o.harness == "claude":
            summary["limitations"].append("Supplemental session log unavailable; stream may omit explicit skill injection.")
        if target:
            try:
                summary["streamTrace"] = trace_capture(target, out)
                reports = {"stream": summary["streamTrace"]}
                if log:
                    summary["sessionTrace"] = trace_capture(target, saved_log)
                    reports["session"] = summary["sessionTrace"]
                # Validate every source before selecting positive confirmation.
                # A matching supplemental source must never hide a conflicting stream.
                for source, item in reports.items():
                    if item.get("targetDigest") != summary["targetDigest"]:
                        raise ValueError(f"{source} trace target revision differs from capture identity")
                    if item.get("targetMatch") is False or item.get("other_copy_loaded"):
                        raise ValueError(f"{source} trace identifies a mismatched target copy")
                    if item.get("fired") is True and item.get("targetMatch") is not True:
                        raise ValueError(f"{source} trace has unverified positive delivery")
                source = "stream"
                if log and reports["session"].get("fired") is True and reports["stream"].get("fired") is not True:
                    source = "session"
                report = deepcopy(reports[source])
                report.update(evidenceSource=source, evidencePath=str(saved_log if source == "session" else out))
            except OSError as exc:
                raise ValueError("tracer could not complete; capture is not qualified") from exc
            summary["trace"] = report
            if o.invocation_mode == "explicit" and report.get("fired") is False:
                report["fired"] = None
                report["loadMechanism"] = "unknown"
                report["limitations"].append("Explicit injection may be absent from harness stream; inspect session log.")
            Path(str(out) + ".trace.json").write_text(json.dumps(report, indent=2) + "\n")
        summary.update(outcome="completed", reason="capture completed; behavioral assertions not graded")
        code = 0
    except (KeyboardInterrupt, Terminated) as exc:
        cause = " by SIGTERM" if isinstance(exc, Terminated) else ""
        summary.update(outcome="failed" if child_started else "blocked",
                       reason=f"capture interrupted{cause}; partial evidence retained")
        raise
    except subprocess.TimeoutExpired:
        summary.update(outcome="timed_out", reason="child or tracer exceeded timeout; partial evidence retained")
        code = 3
    except Blocked as exc:
        summary.update(outcome="blocked", reason=str(exc))
        code = 2
    except OSError:
        code = 1 if summary["childExit"] is not None else 2
        summary.update(outcome="failed" if code == 1 else "blocked",
                       reason="capture I/O failed" if code == 1 else "workspace/process prerequisite failed; inspect local setup")
    except (ValueError, TypeError, KeyError) as exc:
        summary.update(outcome="failed" if child_started else "blocked", reason=str(exc))
        code = 1 if child_started else 2
    finally:
        if scratch and not child_started:
            shutil.rmtree(scratch, ignore_errors=True)
            summary["workspace"] = None
        Path(str(out) + ".summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"capture: {summary['outcome']} · child exit: {summary['childExit']} · {summary['reason']}")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
