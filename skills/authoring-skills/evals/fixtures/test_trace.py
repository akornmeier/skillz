#!/usr/bin/env python3
"""Network-free trace checks. Also safe for unittest discovery."""
import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL / "scripts"))
import trace_skill_use as t


class TraceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "target"
        self.root.mkdir()
        (self.root / "SKILL.md").write_text("---\nname: target\ndescription: Test.\n---\nBody\n")
        (self.root / "ref.md").write_text("Reference\n")

    def report(self, events, fmt="pi-json", root=None):
        path = Path(self.tmp.name) / "trace.jsonl"
        path.write_text("\n".join(json.dumps(e) for e in events))
        out = io.StringIO()
        with redirect_stdout(out):
            code = t.main([str(root or self.root), str(path), "--format", fmt, "--json"])
        self.assertEqual(code, 0)
        return json.loads(out.getvalue())

    def start(self, tool="read", path=None, **args):
        return {"type": "tool_execution_start", "toolCallId": "a", "toolName": tool,
                "args": {"path": str(path or self.root / "SKILL.md"), **args}}

    def end(self, error=False):
        return {"type": "tool_execution_end", "toolCallId": "a", "isError": error,
                "result": {"content": [{"type": "text", "text": "denied" if error else "Body"}]}}

    def complete(self, *events):
        return [{"type": "session", "cwd": self.tmp.name}, *events, {"type": "agent_settled"}]

    def test_writes_and_edits_never_fire(self):
        for tool in ("write", "edit"):
            with self.subTest(tool=tool):
                r = self.report(self.complete(self.start(tool), self.end()))
                self.assertIs(r["fired"], False)
                self.assertEqual(r["reads"], [])

    def test_denied_read(self):
        r = self.report(self.complete(self.start(), self.end(True)))
        self.assertIs(r["fired"], False)
        self.assertEqual(r["reads"][0]["outcome"], "failed")

    def test_missing_result_is_unknown(self):
        r = self.report(self.complete(self.start()))
        self.assertIsNone(r["fired"])
        self.assertEqual(r["reads"][0]["outcome"], "unknown")

    def test_success_range_and_dedup(self):
        start, end = self.start(offset=4, limit=2), self.end()
        r = self.report(self.complete(start, start, end, end))
        self.assertIs(r["fired"], True)
        self.assertEqual(r["loadMechanism"], "read")
        self.assertIs(r["targetMatch"], True)
        self.assertEqual(len(r["reads"]), 1)
        self.assertEqual(r["reads"][0]["requestedRange"], {"offset": 4, "limit": 2})

    def test_wrong_copy_and_matching_manifest(self):
        other = Path(self.tmp.name) / "other" / "target"
        shutil.copytree(self.root, other)
        (other / "ref.md").write_text("Different reference; same SKILL.md\n")
        r = self.report(self.complete(self.start(path=other / "SKILL.md"), self.end()))
        self.assertIs(r["fired"], False)
        self.assertIs(r["targetMatch"], False)
        (other / "ref.md").write_bytes((self.root / "ref.md").read_bytes())
        r = self.report(self.complete(self.start(path=other / "SKILL.md"), self.end()))
        self.assertIs(r["fired"], True)
        self.assertIs(r["targetMatch"], True)
        renamed = other.with_name("renamed-package")
        other.rename(renamed)
        r = self.report(self.complete(self.start(path=renamed / "SKILL.md"), self.end()))
        self.assertIs(r["fired"], True)  # Exact manifests still identify copies at other names.

    def test_unrelated_skill_is_not_a_conflicting_copy(self):
        other = Path(self.tmp.name) / "unrelated-skill"
        other.mkdir()
        (other / "SKILL.md").write_text("---\nname: unrelated-skill\ndescription: Other work.\n---\n")
        r = self.report(self.complete(self.start(path=other / "SKILL.md"), self.end()))
        self.assertIs(r["fired"], False)
        self.assertIsNone(r["other_copy_loaded"])
        self.assertIsNone(r["targetMatch"])

    def test_deleted_candidate_has_unknown_historical_identity(self):
        other = Path(self.tmp.name) / "deleted-workspace" / "target"
        r = self.report(self.complete(self.start(path=other / "SKILL.md"), self.end()))
        self.assertIsNone(r["fired"])
        self.assertIsNone(r["targetMatch"])
        self.assertIsNone(r["other_copy_loaded"])

    def test_conflicting_copy_attempts_require_successful_delivery(self):
        other = Path(self.tmp.name) / "other" / "target"
        shutil.copytree(self.root, other)
        (other / "ref.md").write_text("Different manifest")
        start = self.start(path=other / "SKILL.md")
        r = self.report(self.complete(start))
        self.assertIsNone(r["fired"])
        self.assertIsNone(r["other_copy_loaded"])
        r = self.report(self.complete(start, self.end(True)))
        self.assertIs(r["fired"], False)
        self.assertIsNone(r["other_copy_loaded"])
        intended, result = self.start(), self.end()
        intended["toolCallId"] = result["toolCallId"] = "b"
        r = self.report(self.complete(start, self.end(True), intended, result))
        self.assertIs(r["fired"], True)
        self.assertIsNone(r["other_copy_loaded"])
        self.assertIs(r["targetMatch"], True)

    def test_codemode_is_opaque_but_nested_events_work(self):
        opaque = {"type": "tool_execution_start", "toolCallId": "outer", "toolName": "codemode",
                  "args": {"code": f'await tools.read({{path: "{self.root}/SKILL.md"}})'}}
        r = self.report(self.complete(opaque))
        self.assertIsNone(r["fired"])
        self.assertTrue(any("codemode" in s for s in r["limitations"]))
        r = self.report(self.complete(opaque, self.start(), self.end()))
        self.assertIs(r["fired"], True)

    def test_empty_content_does_not_prove_delivery(self):
        end = self.end()
        end["result"]["content"] = []
        self.assertIsNone(self.report(self.complete(self.start(), end))["fired"])

    def test_incomplete_malformed_and_text_are_unknown(self):
        self.assertIsNone(self.report([{"type": "session"}])["fired"])
        self.assertIsNone(self.report([{"unexpected": 3}, {"type": "agent_settled"}])["fired"])
        self.assertIsNone(self.report([str(self.root / "SKILL.md")], fmt="text")["fired"])

    def test_skill_tool_requires_confirmed_identity(self):
        req = {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "s", "name": "Skill", "input": {"skill": "target"}}]}}
        result = {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "s", "content": f"Base directory for this skill: {self.root}\nBody"}]}}
        r = self.report([req, result, {"type": "result", "is_error": False}], "stream-json")
        self.assertIs(r["fired"], True)
        self.assertEqual(r["loadMechanism"], "skill-tool")
        result["message"]["content"][0]["content"] = "Loaded target"
        self.assertIsNone(self.report([req, result, {"type": "result"}], "stream-json")["fired"])

    def test_pi_session_log_tool_result(self):
        events = [self.start(), {"type": "message", "message": {
            "role": "toolResult", "toolCallId": "a", "toolName": "read", "isError": False,
            "content": [{"type": "text", "text": "Body"}]}}, {"type": "agent_settled"}]
        self.assertIs(self.report(events)["fired"], True)

    def test_relative_paths_use_session_cwd(self):
        start = self.start(path="target/SKILL.md")
        self.assertIs(self.report(self.complete(start, self.end()))["fired"], True)
        self.assertIsNone(self.report([start, self.end(), {"type": "agent_settled"}])["fired"])

    def test_shell_reads_are_not_content_proof(self):
        commands = [
            "cat {D}/ref.md", "head -5 {D}/ref.md", "tail -5 {D}/ref.md",
            "sed -n '1,3p;5,7p' {D}/ref.md", "grep -n '^#' {D}/ref.md",
            'echo "ref.md" && cat {D}/ref.md', "B={D}; cat $B/ref.md",
            "cat {D}/ref.md | head -40", "cat ${{B}}/x; B={D}; cat ${{B}}/ref.md",
        ]
        for command in commands:
            with self.subTest(command=command):
                event = self.start("bash", command=command.format(D=self.root))
                r = self.report(self.complete(event, self.end()))
                self.assertIsNot(r["fired"], True)
                self.assertFalse(any(x["outcome"] == "success" for x in r["reads"]))
        for command in ("wc -c {D}/SKILL.md", "ls {D}/SKILL.md"):
            event = self.start("bash", command=command.format(D=self.root))
            r = self.report(self.complete(event, self.end()))
            self.assertIs(r["fired"], False)
            self.assertEqual(r["reads"], [])

    def test_shell_expansions_are_unknown(self):
        commands = [f"cat {self.root}/*.md", f"cat {self.root}/{{SKILL,ref}}.md",
                    f"cat {self.root}/[S]*.md", f"cat {self.root}/SKILL.?d",
                    f"echo {self.root}/*.md", "cat <(printf Body)"]
        for command in commands:
            with self.subTest(command=command):
                r = self.report(self.complete(self.start("bash", command=command), self.end()))
                self.assertIsNone(r["fired"])

    def test_inline_interpreters_do_not_execute_data_operands(self):
        for command in (
            f"python3 -c 'print(open(__import__(\"sys\").argv[1]).read())' {self.root}/SKILL.md",
            f"node -e 'process.stdout.write(require(\"fs\").readFileSync(process.argv[1]))' {self.root}/SKILL.md",
            f"bash -c 'cat \"$1\"' unused {self.root}/SKILL.md",
        ):
            with self.subTest(command=command):
                r = self.report(self.complete(self.start("bash", command=command), self.end()))
                self.assertIsNone(r["fired"])
                self.assertEqual(r["runs"], [])
        command = f"python3 {self.root}/ref.md {self.root}/SKILL.md"
        r = self.report(self.complete(self.start("bash", command=command), self.end()))
        self.assertIsNone(r["fired"])
        self.assertEqual([event["path"] for event in r["runs"]], ["ref.md"])

    def test_shell_non_loading_requires_supported_metadata_semantics(self):
        for command in ("custom-loader", "env custom-loader", "python3 -m package", "node --eval code"):
            with self.subTest(command=command):
                r = self.report(self.complete(self.start("bash", command=command), self.end()))
                self.assertIsNone(r["fired"])

    def test_search_classification_depends_on_output_mode(self):
        for mode in ("content", "future-mode", None):
            with self.subTest(mode=mode):
                start = self.start("Grep", pattern="^", output_mode=mode)
                self.assertIsNone(self.report(self.complete(start, self.end()))["fired"])
        for args in ({}, {"output_mode": "files_with_matches"}, {"output_mode": "count"}):
            start = self.start("Grep", **args)
            self.assertIs(self.report(self.complete(start, self.end()))["fired"], False)
        self.assertIs(self.report(self.complete(self.start("Glob"), self.end()))["fired"], False)

    def test_result_status_is_strictly_boolean(self):
        for status in (None, 0, 1, "false", [], {}):
            with self.subTest(status=status):
                request = {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "id": "a", "name": "Read", "input": {"file_path": str(self.root / "SKILL.md")}}]}}
                result = {"type": "user", "message": {"content": [
                    {"type": "tool_result", "tool_use_id": "a", "is_error": status, "content": "Body"}]}}
                r = self.report([request, result, {"type": "result"}], "stream-json")
                self.assertIsNone(r["fired"])
                self.assertEqual(r["reads"][0]["outcome"], "unknown")
                r = self.report(self.complete(self.start(), self.end(status)))
                self.assertIsNone(r["fired"])
        # Malformed evidence must not become negative even for non-loading tools.
        self.assertIsNone(self.report(self.complete(self.start("write"), self.end(None)))["fired"])

    def test_skill_load_directory_can_contain_spaces(self):
        other = Path(self.tmp.name) / "work space" / "target"
        shutil.copytree(self.root, other)
        request = {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "a", "name": "Skill", "input": {"skill": "target"}}]}}
        result = {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "a", "content": f"Base directory for this skill: {other}\nBody"}]}}
        r = self.report([request, result, {"type": "result"}], "stream-json")
        self.assertIs(r["fired"], True)
        self.assertIs(r["targetMatch"], True)
        self.assertEqual(r["loadMechanism"], "skill-tool")

    def test_unclassified_shell_reads_preserve_uncertainty(self):
        start = self.start("bash", command=f"env cat {self.root}/SKILL.md")
        self.assertIsNone(self.report(self.complete(start, self.end()))["fired"])
        for command in ("stat", "wc -c", "ls", "test -f", "du", "file", "echo", "printf %s"):
            with self.subTest(command=command):
                start = self.start("bash", command=f"{command} {self.root}/SKILL.md")
                self.assertIs(self.report(self.complete(start, self.end()))["fired"], False)

    def test_unsupported_tools_cannot_prove_non_activation(self):
        for name in ("read_file", "mcp__filesystem__read_file", "future_tool"):
            for result in (self.end(), self.end(True), None):
                with self.subTest(tool=name, result=result):
                    events = [self.start(name)]
                    if result is not None:
                        events.append(result)
                    r = self.report(self.complete(*events))
                    self.assertIsNone(r["fired"])
                    self.assertTrue(any("Unclassified tool" in note for note in r["limitations"]))
        # Unknown extra activity does not erase separately confirmed delivery.
        known, result = self.start(), self.end()
        known["toolCallId"] = result["toolCallId"] = "b"
        r = self.report(self.complete(self.start("read_file"), self.end(), known, result))
        self.assertIs(r["fired"], True)

    def test_malformed_message_structures_are_unknown(self):
        messages = [None, {"role": "assistant"}, {"role": [], "content": []},
                    {"role": "unknown", "content": []},
                    {"content": {}}, {"content": [None]}, {"content": [{}]},
                    {"content": [{"type": " "}]}, {"content": [{"type": "future_delivery"}]},
                    {"content": [{"type": 12}]}, {"content": [{"type": "text", "text": None}]},
                    {"content": [{"type": "tool_use", "id": "a", "name": None, "input": {}}]}]
        for message in messages:
            with self.subTest(message=message):
                r = self.report([{"type": "assistant", "message": message}, {"type": "result"}], "stream-json")
                self.assertIsNone(r["fired"])

    def test_relative_shell_read_without_cwd_is_unknown(self):
        start = {"type": "tool_execution_start", "toolCallId": "a", "toolName": "bash",
                 "args": {"command": "cat target/SKILL.md"}}
        r = self.report([start, self.end(), {"type": "agent_settled"}])
        self.assertIsNone(r["fired"])

    def test_terminal_event_must_match_client_protocol(self):
        for fmt, header, terminal in (
            ("pi-json", {"type": "session"}, {"type": "result"}),
            ("stream-json", {"type": "system", "subtype": "init"}, {"type": "agent_settled"}),
        ):
            with self.subTest(fmt=fmt):
                self.assertIsNone(self.report([header, terminal], fmt)["fired"])

    def test_orphan_results_do_not_prove_non_activation(self):
        self.assertIsNone(self.report(self.complete(self.end()))["fired"])
        # Correlate after parsing: late requests still identify their result.
        self.assertIs(self.report(self.complete(self.end(), self.start()))["fired"], True)

    def injected_text(self):
        return (f'<skill name="target" location="{self.root}/SKILL.md">\n'
                f'References are relative to {self.root}.\n\nBody\n</skill>')

    def test_unverified_markup_is_not_delivery(self):
        valid = self.injected_text()
        variants = [
            ("pi-json", valid.replace('name="target"', 'name="unrelated"')),
            ("pi-json", valid.replace("\n\nBody\n", "\n\nUnrelated instructions\n")),
            ("pi-json", "Quoted example:\n```xml\n" + valid + "\n```"),
            ("stream-json", valid),
        ]
        for fmt, text in variants:
            with self.subTest(fmt=fmt, text=text):
                event = {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": text}]}}
                r = self.report([event, {"type": "result"}], fmt)
                self.assertIsNone(r["fired"])
                self.assertIsNone(r["targetMatch"])

    def test_pi_logged_tool_call_and_injected_load(self):
        request = {"type": "message", "message": {"role": "assistant", "content": [
            {"type": "toolCall", "id": "a", "name": "read", "arguments": {"path": str(self.root / "SKILL.md")}}]}}
        result = {"type": "message", "message": {"role": "toolResult", "toolCallId": "a", "isError": False,
                  "content": [{"type": "text", "text": "Body"}]}}
        self.assertIs(self.report([request, result, {"type": "agent_settled"}])["fired"], True)
        injection = {"type": "message", "message": {"role": "user", "content": [{"type": "text",
            "text": self.injected_text()}]}}
        r = self.report(self.complete(injection))
        self.assertIs(r["fired"], True)
        self.assertEqual(r["loadMechanism"], "injected")

    def test_malformed_requests_and_results_stay_unknown(self):
        events = [self.start("bash", command=3), {"type": "tool_execution_start", "toolCallId": [],
                   "toolName": "read", "args": None}, {"type": "tool_execution_end", "toolCallId": {}},
                  {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": {}}]}}]
        self.assertIsNone(self.report(self.complete(*events))["fired"])

    def test_conflicting_duplicates_cannot_confirm_delivery(self):
        start = self.start()
        conflicting = self.start(path=self.root / "ref.md")
        self.assertIsNone(self.report(self.complete(start, conflicting, self.end()))["fired"])
        self.assertIsNone(self.report(self.complete(start, self.end(), self.end(True)))["fired"])

    def test_pi_lifecycle_and_logged_result_deduplicate(self):
        start, end = self.start(), self.end()
        partial = {"type": "message_start", "message": {"role": "assistant", "content": [
            {"type": "toolCall", "id": "a", "name": "read", "arguments": {}}]}}
        final = {"type": "message_end", "message": {"role": "toolResult", "toolCallId": "a",
                 "content": [{"type": "text", "text": "Body"}]}}
        r = self.report(self.complete(partial, start, end, final))
        self.assertIs(r["fired"], True)
        self.assertEqual(len(r["reads"]), 1)
        self.assertEqual(r["reads"][0]["outcome"], "success")
        self.assertIsNone(self.report([{"type": "session"}, {"type": "agent_end", "willRetry": True}])["fired"])

    def test_unicode_separators_are_not_jsonl_record_boundaries(self):
        path = Path(self.tmp.name) / "unicode.jsonl"
        events = self.complete(self.start(), self.end())
        events[2]["result"]["content"][0]["text"] = "A\u2028B\u2029C"
        path.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in events))
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(t.main([str(self.root), str(path), "--json"]), 0)
        r = json.loads(out.getvalue())
        self.assertIs(r["fired"], True)
        self.assertEqual(r["skipped_lines"], 0)

    def test_existing_fixtures(self):
        for name, reads in (("trace-sample.jsonl", 4), ("trace-sample-pi.jsonl", 3)):
            with self.subTest(name=name):
                raw = (Path(__file__).parent / name).read_text()
                for old in ("/Users/tk/.claude/skills/authoring-skills", "/Users/tk/.agents/skills/authoring-skills"):
                    raw = raw.replace(old, str(SKILL))
                events = [json.loads(line) for line in raw.splitlines()]
                fmt = "pi-json" if "-pi" in name else "stream-json"
                r = self.report(events, fmt, SKILL)
                self.assertIs(r["fired"], True)
                self.assertEqual(r["fired_step"], 1)
                self.assertEqual(len(r["reads"]), reads)
                self.assertEqual(sum(x["partial"] for x in r["reads"]), 1)
                self.assertEqual([x["path"] for x in r["runs"]], ["scripts/lint_skill.py"])


if __name__ == "__main__":
    unittest.main()
