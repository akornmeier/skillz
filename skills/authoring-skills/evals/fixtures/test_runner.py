#!/usr/bin/env python3
"""Runner contracts exercised with mocked children and temporary fixtures only."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
        with patch.object(r, "CLAUDE_PROJECTS", str(projects)):
            code, s = self.run_capture("--harness", "claude", "--trace", str(self.target))
        self.assertEqual(code, 0)
        self.assertEqual((s["observedModel"], s["turns"], s["costUSD"]), ("exact-model", 3, 0.2))
        self.assertTrue(Path(s["sessionLog"]).is_file())
        self.assertIs(s["sessionTrace"]["fired"], True)

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
