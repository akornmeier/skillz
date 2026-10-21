#!/usr/bin/env python3
"""Runner contracts exercised with mocked children and temporary fixtures only."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

SKILL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL / "scripts"))
import run_fresh_session as r


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.source = self.base / "fixture"
        self.source.mkdir()
        self.target = self.source / ".agents" / "skills" / "target"
        self.target.mkdir(parents=True)
        (self.target / "SKILL.md").write_text("---\nname: target\ndescription: Test.\n---\nBody\n")
        self.out = self.base / "capture.jsonl"
        self.saved_env = patch.dict(os.environ, {}, clear=True)
        self.saved_env.start()
        self.addCleanup(self.saved_env.stop)
        self.child = patch.object(r, "run_child", side_effect=self.fake_child)
        self.launch = self.child.start()
        self.addCleanup(self.child.stop)
        self.which = patch.object(r.shutil, "which", return_value="/fake/pi")
        self.which.start()
        self.addCleanup(self.which.stop)
        self.globals = patch.object(r, "GLOBAL_SKILL_ROOTS", ())
        self.globals.start()
        self.addCleanup(self.globals.stop)
        self.captured = {}

    def fake_child(self, cmd, cwd, out, err, timeout, env):
        self.captured.update(cwd=cwd, env=env, cmd=cmd)
        Path(out).write_text(json.dumps({"type": "session", "cwd": str(cwd)}) + "\n" +
                             json.dumps({"type": "agent_settled"}) + "\n")
        Path(err).write_text("")
        return 0

    def run_capture(self, *args, live=True):
        flags = [str(self.source), "A test prompt", "--harness", "pi", "--out", str(self.out)]
        if live:
            flags.append("--allow-live")
        code = r.main(flags + list(args))
        summary = json.loads(Path(str(self.out) + ".summary.json").read_text())
        workspace = summary.get("workspace")
        if workspace and Path(workspace).resolve() != self.source.resolve():
            shutil.rmtree(Path(workspace).parent, ignore_errors=True)
        return code, summary

    def test_live_opt_in_required(self):
        code, s = self.run_capture(live=False)
        self.assertEqual((code, s["outcome"], s["childExit"]), (2, "blocked", None))
        self.launch.assert_not_called()

    def test_child_failure_and_partial_transcript(self):
        def failure(*args):
            self.fake_child(*args)
            return 7
        self.launch.side_effect = failure
        code, s = self.run_capture()
        self.assertEqual((code, s["outcome"], s["childExit"]), (1, "failed", 7))
        self.assertTrue(self.out.stat().st_size)

    def test_startup_and_auth_failure(self):
        self.launch.side_effect = OSError("cannot start")
        code, s = self.run_capture()
        self.assertEqual((code, s["outcome"]), (2, "blocked"))
        self.assertIsNone(s["childExit"])

    def test_auth_result_is_blocked(self):
        def auth(*args):
            Path(args[2]).write_text(json.dumps({"type": "result", "is_error": True, "result": "Invalid API key"}) + "\n")
            return 1
        self.launch.side_effect = auth
        code, s = self.run_capture()
        self.assertEqual((code, s["outcome"], s["childExit"]), (2, "blocked", 1))
        self.assertNotIn("Invalid API key", s["reason"])

    def test_pi_auth_and_aborted_or_unsettled_sessions(self):
        samples = [
            ('{"type":"message_end","message":{"role":"assistant","stopReason":"error","errorMessage":"Invalid API key"}}\n', 2),
            ('{"type":"agent_end","willRetry":true}\n', 1),
            ('{"type":"agent_settled","aborted":true}\n', 1),
        ]
        for index, (text, expected) in enumerate(samples):
            self.out = self.base / f"pi-error{index}.jsonl"
            def emit(*args):
                Path(args[2]).write_text(text)
                return 0
            self.launch.side_effect = emit
            code, s = self.run_capture()
            self.assertEqual(code, expected)
            self.assertNotEqual(s["outcome"], "completed")

    def retry_events(self, error="529 overloaded"):
        return [
            {"type": "session"},
            {"type": "message_end", "message": {"role": "assistant", "stopReason": "error", "errorMessage": error}},
            {"type": "agent_end", "willRetry": True},
            {"type": "auto_retry_start", "attempt": 1},
        ]

    def emit_events(self, events):
        def emit(*args):
            Path(args[2]).write_text("\n".join(json.dumps(event) for event in events) + "\n")
            return 0
        self.launch.side_effect = emit

    def test_recovered_pi_retry_completes_capture(self):
        for index, error in enumerate(("529 overloaded", "Invalid API key", "context overflow")):
            with self.subTest(error=error):
                self.out = self.base / f"recovered-{index}.jsonl"
                events = self.retry_events(error)
                if error == "context overflow":
                    events = events[:2] + [{"type": "agent_end", "willRetry": False},
                        {"type": "compaction_end", "reason": "overflow", "willRetry": True}, {"type": "agent_start"}]
                events.append({"type": "message_end", "message": {
                    "role": "assistant", "stopReason": "stop", "model": "fixture-model"}})
                if error != "context overflow":
                    events.append({"type": "auto_retry_end", "success": True, "attempt": 1})
                events.extend([{"type": "agent_end", "willRetry": False},
                               {"type": "agent_settled", "aborted": False}])
                self.emit_events(events)
                code, summary = self.run_capture()
                self.assertEqual((code, summary["outcome"], summary["childExit"]), (0, "completed", 0))
                self.assertEqual(summary["observedModel"], "fixture-model")

    def test_exhausted_pi_retry_keeps_unrecovered_error(self):
        for index, (error, expected) in enumerate((("529 overloaded", 1), ("Invalid API key", 2))):
            self.out = self.base / f"exhausted-{index}.jsonl"
            self.emit_events(self.retry_events(error) + [
                {"type": "message_end", "message": {"role": "assistant", "stopReason": "error", "errorMessage": error}},
                {"type": "agent_end", "willRetry": False},
                {"type": "auto_retry_end", "success": False, "finalError": error},
                {"type": "agent_settled", "aborted": False},
            ])
            code, summary = self.run_capture()
            self.assertEqual(code, expected)
            self.assertNotEqual(summary["outcome"], "completed")

    def test_retry_requires_completion_and_successful_response(self):
        good = {"type": "message_end", "message": {"role": "assistant", "stopReason": "stop"}}
        ack = {"type": "auto_retry_end", "success": True}
        samples = [[], [good], [ack], [good, ack, {"type": "message_end", "message": {
            "role": "assistant", "stopReason": "error", "errorMessage": "later failure"}}]]
        for index, suffix in enumerate(samples):
            self.out = self.base / f"incomplete-retry-{index}.jsonl"
            self.emit_events(self.retry_events() + suffix + [{"type": "agent_settled", "aborted": False}])
            self.assertEqual(self.run_capture()[0], 1)

    def test_latest_pi_work_requires_new_settlement(self):
        good = {"type": "message_end", "message": {"role": "assistant", "stopReason": "stop"}}
        self.emit_events(self.retry_events() + [good, {"type": "auto_retry_end", "success": True},
                         {"type": "agent_settled", "aborted": False}, good])
        self.assertEqual(self.run_capture()[0], 1)

    def test_capture_rejects_malformed_event_types(self):
        for index, kind in enumerate((None, [], {}, False, 0, "", " ")):
            with self.subTest(kind=kind):
                self.out = self.base / f"event-type-{index}.jsonl"
                self.emit_events([{"type": "session"}, {"type": kind}, {"type": "agent_settled"}])
                self.assertEqual(self.run_capture()[0], 1)

    def test_capture_rejects_work_after_old_settlement(self):
        for index, event in enumerate(({"type": "agent_start"}, {"type": "turn_start"},
                                       {"type": "message_update"}, {"type": "compaction_start"},
                                       {"type": "agent_end", "willRetry": False})):
            with self.subTest(event=event):
                self.out = self.base / f"late-work-{index}.jsonl"
                self.emit_events([{"type": "session"}, {"type": "agent_settled"}, event])
                self.assertEqual(self.run_capture()[0], 1)

    def test_capture_status_flags_are_strictly_boolean(self):
        for index, status in enumerate((None, 0, 1, [], "false")):
            for harness, event in (
                ("pi", {"type": "agent_settled", "aborted": status}),
                ("pi", {"type": "agent_end", "willRetry": status}),
                ("claude", {"type": "result", "is_error": status, "subtype": "success"}),
            ):
                with self.subTest(harness=harness, event=event):
                    self.out = self.base / f"malformed-status-{index}-{event['type']}.jsonl"
                    events = [event]
                    if event["type"] == "agent_end":
                        events.append({"type": "agent_settled", "aborted": False})
                    self.emit_events(events)
                    self.assertEqual(self.run_capture("--harness", harness)[0], 1)

    def test_successful_answer_can_mention_authentication_errors(self):
        def emit(*args):
            Path(args[2]).write_text(json.dumps({"type": "result", "subtype": "success", "is_error": False,
                "result": "Added handling for invalid API key errors."}) + "\n")
            return 0
        self.launch.side_effect = emit
        code, s = self.run_capture("--harness", "claude")
        self.assertEqual((code, s["outcome"], s["childExit"]), (0, "completed", 0))

    def test_timeout_keeps_partial_evidence(self):
        def timeout(*args):
            Path(args[2]).write_text('{"type":"session"}\n')
            raise subprocess.TimeoutExpired("fake", 1)
        self.launch.side_effect = timeout
        code, s = self.run_capture("--timeout", "1")
        self.assertEqual((code, s["outcome"]), (3, "timed_out"))
        self.assertTrue(self.out.exists())

    def test_interruption_records_failed_capture_before_reraising(self):
        self.launch.side_effect = KeyboardInterrupt
        with self.assertRaises(KeyboardInterrupt):
            self.run_capture()
        summary = json.loads(Path(str(self.out) + ".summary.json").read_text())
        if summary.get("workspace"):
            self.addCleanup(shutil.rmtree, Path(summary["workspace"]).parent, ignore_errors=True)
        self.assertEqual(summary["outcome"], "failed")
        self.assertIn("interrupt", summary["reason"])

    def test_sigterm_restores_prior_handler(self):
        received = []
        def prior(signum, frame):
            received.append(signum)
        original = r.signal.signal(r.signal.SIGTERM, prior)
        try:
            self.launch.side_effect = lambda *args: r.signal.raise_signal(r.signal.SIGTERM)
            code, summary = self.run_capture()
            self.assertIs(r.signal.getsignal(r.signal.SIGTERM), prior)
            self.assertEqual(received, [r.signal.SIGTERM])
            self.assertEqual(code, 128 + r.signal.SIGTERM)
            self.assertEqual(summary["outcome"], "failed")
            self.assertIn("SIGTERM", summary["reason"])
            self.out = self.base / "after-termination.jsonl"
            self.assertEqual(self.run_capture(live=False)[0], 2)
            self.assertIs(r.signal.getsignal(r.signal.SIGTERM), prior)
        finally:
            r.signal.signal(r.signal.SIGTERM, original)

    def test_signal_is_failure(self):
        self.launch.side_effect = lambda *args: (self.fake_child(*args), -15)[1]
        code, s = self.run_capture()
        self.assertEqual((code, s["outcome"], s["childExit"]), (1, "failed", -15))

    def test_empty_malformed_incomplete_and_api_error_are_failed(self):
        for index, text in enumerate(("", "not json", '{"type":"session"}\n',
                                      '{"type":"agent_end"}\n{"type":"message_end","message":{"role":"assistant","stopReason":"error"}}\n')):
            with self.subTest(text=text):
                self.out = self.base / f"bad{index}.jsonl"
                def bad(*args):
                    Path(args[2]).write_text(text)
                    return 0
                self.launch.side_effect = bad
                code, s = self.run_capture()
                self.assertEqual((code, s["outcome"]), (1, "failed"))

    def test_completed_negative_trigger_records_identity_not_task_pass(self):
        code, s = self.run_capture("--trace", str(self.target), "--invocation-mode", "automatic")
        self.assertEqual((code, s["outcome"], s["childExit"]), (0, "completed", 0))
        self.assertEqual(s["targetDigest"], r.manifest_digest(self.target))
        self.assertEqual(s["targetPath"], str(self.target.resolve()))
        self.assertEqual(s["invocationMode"], "automatic")
        self.assertEqual(s["depth"], 1)
        self.assertIs(s["trace"]["fired"], False)
        self.assertNotIn("passed", s)

    def test_claude_session_log_and_metrics_are_preserved(self):
        projects = self.base / "claude-projects"
        project = projects / "fixture"
        project.mkdir(parents=True)
        log = [
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "r", "name": "Read",
             "input": {"file_path": str(self.target / "SKILL.md")}}]}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "r", "content": "Body"}]}},
        ]
        (project / "fixture-session.jsonl").write_text("\n".join(json.dumps(e) for e in log))
        def emit(*args):
            events = [{"type": "system", "subtype": "init", "session_id": "fixture-session", "model": "exact-model"},
                      {"type": "result", "subtype": "success", "is_error": False, "result": "Done", "num_turns": 3, "total_cost_usd": 0.2}]
            Path(args[2]).write_text("\n".join(json.dumps(e) for e in events))
            return 0
        self.launch.side_effect = emit
        for mode in ("unknown", "automatic", "explicit"):
            with self.subTest(mode=mode):
                self.out = self.base / f"session-{mode}.jsonl"
                with patch.object(r, "CLAUDE_PROJECTS", str(projects)):
                    code, s = self.run_capture("--harness", "claude", "--trace", str(self.target), "--invocation-mode", mode)
                self.assertEqual(code, 0)
                self.assertEqual((s["observedModel"], s["turns"], s["costUSD"]), ("exact-model", 3, 0.2))
                self.assertTrue(Path(s["sessionLog"]).is_file())
                self.assertIs(s["sessionTrace"]["fired"], True)
                self.assertIs(s["trace"]["fired"], True)
                self.assertIs(s["streamTrace"]["fired"], False)
                self.assertEqual(s["trace"]["evidenceSource"], "session")
                self.assertEqual(s["trace"]["evidencePath"], s["sessionLog"])
                self.assertEqual(json.loads(Path(str(self.out) + ".trace.json").read_text()), s["trace"])

    def test_stream_delivery_and_explicit_fallback_preserve_raw_evidence(self):
        for loaded in (False, True):
            with self.subTest(loaded=loaded):
                self.out = self.base / f"stream-{loaded}.jsonl"
                events = [{"type": "session"}]
                if loaded:
                    events.extend([
                        {"type": "tool_execution_start", "toolCallId": "a", "toolName": "read",
                         "args": {"path": str(self.target / "SKILL.md")}},
                        {"type": "tool_execution_end", "toolCallId": "a", "isError": False,
                         "result": {"content": [{"type": "text", "text": "Body"}]}},
                    ])
                self.emit_events(events + [{"type": "agent_settled"}])
                code, summary = self.run_capture("--trace", str(self.target), "--invocation-mode", "explicit")
                self.assertEqual(code, 0)
                self.assertIs(summary["streamTrace"]["fired"], loaded)
                self.assertIs(summary["trace"]["fired"], True if loaded else None)
                self.assertEqual(summary["trace"]["evidenceSource"], "stream")
                self.assertEqual(summary["trace"]["evidencePath"], str(self.out.resolve()))
                self.assertFalse(any("Explicit injection" in note for note in summary["streamTrace"]["limitations"]))
                self.assertEqual(json.loads(Path(str(self.out) + ".trace.json").read_text()), summary["trace"])

    def test_delivery_selection_cannot_mask_identity_mismatches(self):
        saved = self.base / "fixture-session.jsonl"
        saved.write_text("{}\n")
        digest = r.manifest_digest(self.target)
        def emit(*args):
            Path(args[2]).write_text('{"type":"result","is_error":false,"subtype":"success"}\n')
            return 0
        self.launch.side_effect = emit
        for index, (source, field, value) in enumerate((
            ("stream", "targetMatch", False), ("session", "targetMatch", False),
            ("stream", "targetDigest", "wrong"), ("session", "targetDigest", "wrong"),
        )):
            with self.subTest(source=source, field=field):
                self.out = self.base / f"identity-{index}.jsonl"
                reports = {"stream": {"fired": False, "targetMatch": None, "targetDigest": digest},
                           "session": {"fired": True, "targetMatch": True, "targetDigest": digest}}
                reports[source][field] = value
                def traced(target, path):
                    return reports["session" if str(path).endswith(".session.jsonl") else "stream"].copy()
                with patch.object(r, "session_log", return_value=saved), patch.object(r, "trace_capture", side_effect=traced):
                    self.assertEqual(self.run_capture("--harness", "claude", "--trace", str(self.target))[0], 1)

    def test_failed_tracer_is_failure(self):
        with patch.object(r, "trace_capture", side_effect=ValueError("trace failed")):
            code, s = self.run_capture("--trace", str(self.target))
        self.assertEqual((code, s["outcome"]), (1, "failed"))

    def test_tracer_timeout_preserves_timeout_outcome(self):
        with patch.object(r, "trace_capture", side_effect=subprocess.TimeoutExpired("tracer", 60)):
            code, s = self.run_capture("--trace", str(self.target))
        self.assertEqual((code, s["outcome"], s["childExit"]), (3, "timed_out", 0))
        self.assertTrue(self.out.stat().st_size)

    def test_conflicting_target_copy_blocks_before_launch(self):
        global_root = self.base / "global"
        shutil.copytree(self.target, global_root / "target")
        (global_root / "target" / "SKILL.md").write_text("Different\n")
        with patch.object(r, "GLOBAL_SKILL_ROOTS", (str(global_root),)):
            code, s = self.run_capture("--trace", str(self.target))
        self.assertEqual((code, s["outcome"]), (2, "blocked"))
        self.launch.assert_not_called()

    def test_links_rejected_and_no_launch(self):
        for index, destination in enumerate((self.base / "outside", self.base / "missing", self.target)):
            with self.subTest(destination=str(destination)):
                self.out = self.base / f"link{index}.jsonl"
                if index == 0:
                    destination.write_text("outside")
                link = self.source / "link"
                link.symlink_to(destination)
                code, s = self.run_capture()
                self.assertEqual((code, s["outcome"]), (2, "blocked"))
                self.launch.assert_not_called()
                link.unlink()

    def test_fixture_scan_errors_are_not_silently_skipped(self):
        protected = self.source / "protected"
        protected.mkdir()
        native_scan = r.os.scandir
        def scan(path):
            if Path(path) == protected:
                raise PermissionError("fixture scan denied")
            return native_scan(path)
        with patch.object(r.os, "scandir", side_effect=scan):
            with self.assertRaises(PermissionError):
                r.check_fixture(self.source)

    def test_symlink_root_rejected(self):
        alias = self.base / "alias"
        alias.symlink_to(self.source, target_is_directory=True)
        self.source = alias
        code, s = self.run_capture()
        self.assertEqual((code, s["outcome"]), (2, "blocked"))
        self.launch.assert_not_called()

    def test_output_collision_never_writes_source(self):
        self.out = self.source / "capture.jsonl"
        code = r.main([str(self.source), "test", "--out", str(self.out), "--allow-live"])
        self.assertEqual(code, 2)
        self.assertFalse(self.out.exists())
        self.assertFalse(Path(str(self.out) + ".summary.json").exists())
        self.launch.assert_not_called()

    def test_sidecar_symlink_collision_never_writes_source(self):
        victim = self.source / "keep"
        victim.write_text("unchanged")
        Path(str(self.out) + ".summary.json").symlink_to(victim)
        code = r.main([str(self.source), "test", "--out", str(self.out), "--allow-live"])
        self.assertEqual(code, 2)
        self.assertEqual(victim.read_text(), "unchanged")
        self.launch.assert_not_called()

    def test_invalid_timeout_and_missing_binary_block(self):
        code, s = self.run_capture("--timeout", "0")
        self.assertEqual((code, s["outcome"]), (2, "blocked"))
        self.launch.assert_not_called()
        self.out = self.base / "unavailable.jsonl"
        with patch.object(r.shutil, "which", return_value=None):
            code, s = self.run_capture()
        self.assertEqual((code, s["outcome"]), (2, "blocked"))

    def test_required_restrictions_and_in_place_qualification_block(self):
        for index, flags in enumerate((("--require-skill-isolation",), ("--require-containment",),
                                       ("--qualification", "--in-place"))):
            self.out = self.base / f"restriction{index}.jsonl"
            code, s = self.run_capture(*flags)
            self.assertEqual((code, s["outcome"]), (2, "blocked"))
            self.launch.assert_not_called()

    def test_depth_cap_cannot_be_raised_in_child(self):
        with patch.dict(os.environ, {r.DEPTH_ENV: "1", r.MAX_DEPTH_ENV: "1"}):
            code, s = self.run_capture("--max-depth", "2", "--run-budget", "5")
        self.assertEqual((code, s["outcome"]), (2, "blocked"))
        self.launch.assert_not_called()

    def test_second_level_requires_shared_budget(self):
        with patch.dict(os.environ, {r.DEPTH_ENV: "1", r.MAX_DEPTH_ENV: "2"}):
            code, s = self.run_capture("--max-depth", "2")
        self.assertEqual((code, s["outcome"]), (2, "blocked"))
        self.launch.assert_not_called()

    def test_shared_budget_is_consumed_once_per_attempt(self):
        ledger = self.base / "budget.json"
        ledger.write_text(json.dumps({"remaining": 1, "approved": 2}))
        env = {r.DEPTH_ENV: "1", r.MAX_DEPTH_ENV: "2", r.BUDGET_ENV: str(ledger)}
        with patch.dict(os.environ, env):
            code, s = self.run_capture("--max-depth", "2")
            self.assertEqual((code, s["depth"]), (0, 2))
            self.out = self.base / "exhausted.jsonl"
            code, s = self.run_capture("--max-depth", "2")
        self.assertEqual((code, s["outcome"]), (2, "blocked"))
        self.assertEqual(self.launch.call_count, 1)

    def test_failed_scratch_setup_is_cleaned(self):
        scratch = self.base / "scratch"
        scratch.mkdir()
        with patch.object(r.tempfile, "mkdtemp", return_value=str(scratch)), \
             patch.object(r.shutil, "copytree", side_effect=OSError("copy failed")):
            code, s = self.run_capture()
        self.assertEqual((code, s["outcome"]), (2, "blocked"))
        self.assertFalse(scratch.exists())
        self.launch.assert_not_called()


class ProcessTests(unittest.TestCase):
    def test_sigterm_stops_fake_child_and_writes_summary(self):
        # Isolated Python-only supervisor/child. No authenticated CLI or credentials.
        with tempfile.TemporaryDirectory(prefix="capture-sigterm-") as tmp:
            base = Path(tmp).resolve()
            work, scratch = base / "workspace", base / "scratch"
            work.mkdir()
            scratch.mkdir()
            pid_path, out = base / "child.pid", base / "capture.jsonl"
            child_code = ("import os,time; from pathlib import Path; Path(" + repr(str(pid_path)) +
                          ").write_text(str(os.getpid())); time.sleep(60)")
            script = base / "supervisor.py"
            script.write_text(
                "import sys\nsys.path.insert(0," + repr(str(SKILL / "scripts")) + ")\n"
                "import run_fresh_session as r\n"
                "r.tempfile.mkdtemp = lambda **kwargs: " + repr(str(scratch)) + "\n"
                "r.HARNESSES['fixture'] = lambda prompt: [sys.executable, '-c', " + repr(child_code) + "]\n"
                "r.main([" + repr(str(work)) + ", 'Python fixture only', '--out', " + repr(str(out)) +
                ", '--harness', 'fixture', '--allow-live', '--timeout', '30'])\n")
            env = {"PATH": os.environ.get("PATH", ""), "HOME": str(base), "PYTHONDONTWRITEBYTECODE": "1"}
            child_pid = None
            with (base / "supervisor.err").open("w") as log:
                supervisor = subprocess.Popen([sys.executable, str(script)], env=env, stdin=subprocess.DEVNULL,
                                              stdout=subprocess.DEVNULL, stderr=log, start_new_session=True)
                try:
                    deadline = time.monotonic() + 10
                    while time.monotonic() < deadline:
                        if pid_path.exists() and pid_path.read_text().strip():
                            child_pid = int(pid_path.read_text())
                            break
                        if supervisor.poll() is not None:
                            break
                        time.sleep(0.02)
                    self.assertIsNotNone(child_pid, "fixture child did not start")
                    supervisor.terminate()
                    self.assertEqual(supervisor.wait(timeout=5), -r.signal.SIGTERM)
                    try:
                        os.kill(child_pid, 0)
                        alive = True
                    except ProcessLookupError:
                        alive = False
                    summary_path = Path(str(out) + ".summary.json")
                    self.assertTrue(summary_path.is_file(), f"missing summary; child alive={alive}")
                    self.assertFalse(alive, "terminated supervisor left its child running/unreaped")
                    summary = json.loads(summary_path.read_text())
                    self.assertEqual(summary["outcome"], "failed")
                    self.assertIn("SIGTERM", summary["reason"])
                finally:
                    if supervisor.poll() is None:
                        supervisor.kill()
                        supervisor.wait()
                    if child_pid:
                        try:
                            os.killpg(child_pid, r.signal.SIGKILL)
                        except ProcessLookupError:
                            pass

    def test_sigterm_during_spawn_waits_for_child_handle_before_cleanup(self):
        child = Mock(pid=12345)
        original = r.signal.signal(r.signal.SIGTERM, r.terminate_capture)
        def spawn(*args, **kwargs):
            # Model a signal after the child exists but before Popen returns it.
            r.signal.raise_signal(r.signal.SIGTERM)
            return child
        try:
            with tempfile.TemporaryDirectory() as tmp, \
                 patch.object(r.subprocess, "Popen", side_effect=spawn), \
                 patch.object(r.os, "killpg") as kill:
                with self.assertRaises(r.Terminated):
                    r.run_child(["fixture-only"], tmp, str(Path(tmp) / "out"), str(Path(tmp) / "err"), 1, {})
            kill.assert_called_once_with(12345, r.signal.SIGKILL)
            child.wait.assert_called_once_with()
            self.assertIs(r.signal.getsignal(r.signal.SIGTERM), r.terminate_capture)
        finally:
            r.signal.signal(r.signal.SIGTERM, original)

    def test_sigint_during_spawn_stops_real_python_child(self):
        native_popen = subprocess.Popen
        owned = []
        def spawn(*args, **kwargs):
            child = native_popen([sys.executable, "-c", "import time; time.sleep(30)"],
                                 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, start_new_session=True)
            owned.append(child)
            r.signal.raise_signal(r.signal.SIGINT)
            return child
        original = r.signal.signal(r.signal.SIGINT, r.signal.default_int_handler)
        try:
            with tempfile.TemporaryDirectory() as tmp, patch.object(r.subprocess, "Popen", side_effect=spawn):
                with self.assertRaises(KeyboardInterrupt):
                    r.run_child(["fixture-only"], tmp, str(Path(tmp) / "out"), str(Path(tmp) / "err"), 1, {})
            self.assertEqual(owned[0].poll(), -r.signal.SIGKILL, "spawn interruption left child running")
            self.assertIs(r.signal.getsignal(r.signal.SIGINT), r.signal.default_int_handler)
        finally:
            r.signal.signal(r.signal.SIGINT, original)
            for child in owned:
                if child.poll() is None:
                    os.killpg(child.pid, r.signal.SIGKILL)
                child.wait()

    def test_spawn_preserves_ignored_and_callable_sigint_handlers(self):
        received = []
        def handler(signum, frame):
            received.append((signum, frame))
        for previous in (r.signal.SIG_IGN, handler):
            with self.subTest(handler=previous):
                child = Mock(pid=12345)
                child.wait.return_value = 0
                def spawn(*args, **kwargs):
                    r.signal.raise_signal(r.signal.SIGINT)
                    return child
                original = r.signal.signal(r.signal.SIGINT, previous)
                try:
                    with tempfile.TemporaryDirectory() as tmp, \
                         patch.object(r.subprocess, "Popen", side_effect=spawn), \
                         patch.object(r.os, "killpg") as kill:
                        self.assertEqual(r.run_child(["fixture-only"], tmp, str(Path(tmp) / "out"),
                                                     str(Path(tmp) / "err"), 1, {}), 0)
                    kill.assert_called_once_with(12345, r.signal.SIGKILL)
                    self.assertEqual(child.wait.call_args_list, [call(timeout=1), call()])
                    self.assertIs(r.signal.getsignal(r.signal.SIGINT), previous)
                finally:
                    r.signal.signal(r.signal.SIGINT, original)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0][0], r.signal.SIGINT)
        self.assertIsNotNone(received[0][1])

    def test_interrupted_wait_kills_and_reaps_child_group(self):
        child = Mock(pid=12345)
        child.wait.side_effect = [KeyboardInterrupt, -9]
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(r.subprocess, "Popen", return_value=child), \
             patch.object(r.os, "killpg") as kill:
            with self.assertRaises(KeyboardInterrupt):
                r.run_child(["fixture-only"], tmp, str(Path(tmp) / "out"), str(Path(tmp) / "err"), 1, {})
        kill.assert_called_once_with(12345, r.signal.SIGKILL)
        self.assertEqual(child.wait.call_args_list, [call(timeout=1), call()])

    def test_parent_exit_stops_owned_worker_group(self):
        # Ready/release proves descendants cannot keep doing work after their
        # harness exits, without relying on orphan PID reaping timing.
        for ending, expected in (("raise SystemExit(7)", 7),
                                 ("os.kill(os.getpid(), signal.SIGTERM)", -r.signal.SIGTERM),
                                 ("raise SystemExit(0)", 0)):
            with self.subTest(ending=ending), tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp)
                ready, release, escaped = base / "ready", base / "release", base / "escaped"
                record, script = base / "owner.json", base / "parent.py"
                worker_code = ("import time;from pathlib import Path\n"
                    + f"Path({str(ready)!r}).write_text('ready')\n"
                    + f"while not Path({str(release)!r}).exists(): time.sleep(0.01)\n"
                    + f"Path({str(escaped)!r}).write_text('work escaped supervisor')\n")
                script.write_text("import os,sys,signal,subprocess,time,json\nfrom pathlib import Path\n"
                    + f"worker=subprocess.Popen([sys.executable,'-c',{worker_code!r}])\n"
                    + f"Path({str(record)!r}).write_text(json.dumps({{'parent':os.getpid(),'worker':worker.pid}}))\n"
                    + "deadline=time.monotonic()+3\n"
                    + f"while not Path({str(ready)!r}).exists() and time.monotonic()<deadline: time.sleep(0.01)\n"
                    + f"assert Path({str(ready)!r}).exists(), 'fixture worker did not start'\n"
                    + ending + "\n")
                try:
                    status = r.run_child([sys.executable, str(script)], tmp, str(base / "out"), str(base / "err"),
                                         5, dict(os.environ))
                    self.assertEqual(status, expected)
                    release.write_text("continue")
                    deadline = time.monotonic() + 0.5
                    while not escaped.exists() and time.monotonic() < deadline:
                        time.sleep(0.01)
                    self.assertFalse(escaped.exists(), "worker continued after harness exit")
                finally:
                    if record.exists():
                        owner = json.loads(record.read_text())
                        try:
                            os.killpg(owner["parent"], r.signal.SIGKILL)
                        except ProcessLookupError:
                            pass

    def test_real_fake_executable_exit_and_timeout(self):
        # Only Python fixture code executes, never an authenticated agent CLI.
        with tempfile.TemporaryDirectory() as tmp:
            out, err = str(Path(tmp) / "out"), str(Path(tmp) / "err")
            code = r.run_child([sys.executable, "-c", "print('evidence', flush=True); raise SystemExit(7)"],
                               tmp, out, err, 5, dict(os.environ))
            self.assertEqual(code, 7)
            self.assertEqual(Path(out).read_text(), "evidence\n")
            out, err = out + "2", err + "2"
            with self.assertRaises(subprocess.TimeoutExpired):
                r.run_child([sys.executable, "-c", "import time; print('partial', flush=True); time.sleep(30)"],
                            tmp, out, err, 1, dict(os.environ))
            self.assertEqual(Path(out).read_text(), "partial\n")


if __name__ == "__main__":
    unittest.main()
