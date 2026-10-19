#!/usr/bin/env python3
"""Pinned-PyYAML, network-free format/policy/cost fixtures."""
import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL / "scripts"))
import lint_skill as lint


def suite(name="fixture"):
    return {"schema": 1, "skill": name, "requiredProfiles": list(lint.PROFILES), "cases": [
        {"id": f"{name}-{i}", "summary": "A case", "setup": "Temporary workspace", "prompt": f"Task {i}",
         "expectedBehavior": ["Writes result", "Reports evidence"],
         "forbiddenBehavior": ["Calls an API", "Changes unrelated files"]} for i in range(3)]}


class LintTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "fixture"
        self.root.mkdir()
        (self.root / "evals").mkdir()
        (self.root / "evals/evals.json").write_text(json.dumps(suite()))
        self.write()

    def write(self, fields="name: fixture\ndescription: Performs fixture tasks. Use for fixture work.", body="# Fixture\n", newline="\n"):
        (self.root / "SKILL.md").write_bytes((f"---\n{fields}\n---\n{body}").replace("\n", newline).encode())

    def check(self, target="portable"):
        findings, summary = lint.lint_skill(str(self.root), target)
        self.assertTrue(all(f.authority in {"portable", "platform", "local", "heuristic"} for f in findings))
        return findings, summary

    def assert_passes(self, target="portable"):
        findings, summary = self.check(target)
        self.assertEqual(summary["fail"], 0, [f.as_dict() for f in findings])
        return findings, summary

    def test_quoted_multiline_unicode_and_crlf(self):
        for value in ('"Processes café: résumé."', ">\n  Processes Unicode 数据.\n  Applies to fixture tasks.",
                      "|\n  Processes tasks.\n  Use for fixtures."):
            for newline in ("\n", "\r\n"):
                with self.subTest(value=value, newline=repr(newline)):
                    self.write("name: fixture\ndescription: " + value, newline=newline)
                    self.assert_passes()

    def test_valid_optional_fields_and_merge(self):
        self.write('name: fixture\ndescription: Performs fixture tasks.\nlicense: MIT\ncompatibility: Python 3.9+\n'
                   'allowed-tools: Read Grep\nmetadata:\n  version: "1.0"\n  author: Tony')
        self.assert_passes()
        self.write('name: fixture\ndescription: Performs fixture tasks.\nmetadata:\n  <<: &base {author: Tony}\n  author: User')
        self.assert_passes()

    def test_malformed_yaml_and_unsafe_tags_fail(self):
        for fields in ('name: fixture\ndescription: "unclosed', 'name: fixture\nname: duplicate\ndescription: Text',
                       '- name\n- description', 'name: fixture\ndescription: !!python/object/apply:os.system ["echo bad"]',
                       'name: fixture\ndescription: Text\nmetadata: {author: X, author: Y}'):
            with self.subTest(fields=fields):
                self.write(fields)
                findings, summary = self.check()
                self.assertGreater(summary["fail"], 0)
                self.assertTrue(any(f.check == "frontmatter" and f.authority == "portable" for f in findings))

    def test_required_fields_are_strings(self):
        for field in ("name", "description"):
            for value in ("true", "27", "[]", "{}", "null", '"   "'):
                with self.subTest(field=field, value=value):
                    fields = {"name": "fixture", "description": "Does fixture tasks"}
                    fields[field] = value
                    self.write("\n".join(f"{k}: {v}" for k, v in fields.items()))
                    findings, summary = self.check()
                    self.assertGreater(summary["fail"], 0)
                    self.assertTrue(any(f.check == f"{field}-type" for f in findings))

    def test_invalid_optional_types(self):
        for optional in ("license: []", "compatibility: false", "metadata: []", "metadata: {version: 1}",
                         "metadata: {true: author}", "allowed-tools: [Read, Grep]"):
            self.write("name: fixture\ndescription: Does fixture work\n" + optional)
            self.assertGreater(self.check()[1]["fail"], 0, optional)
        self.assert_passes("claude-code")  # Last optional: Claude Code's documented list form.

    def test_lengths_use_parsed_values_not_normalized_prose(self):
        for field, size in (("description", 1025), ("compatibility", 501), ("name", 65)):
            values = {"name": "fixture", "description": "Does fixture work"}
            values[field] = "x" * size
            self.write("\n".join(f"{k}: {v}" for k, v in values.items()))
            findings, _ = self.check()
            self.assertTrue(any(f.check == field + "-length" and f.level == "FAIL" for f in findings))
        self.write("name: fixture\ndescription: '" + "x " * 513 + "'")
        self.assertGreater(self.check()[1]["fail"], 0)

    def test_wording_and_size_are_advice(self):
        for rows in (151, 501):
            self.write("name: fixture\ndescription: I produce fixture reports for teams.", body="Line\n" * rows)
            findings, _ = self.assert_passes()
            self.assertTrue(any(f.check == "body-length" and f.level == "WARN" for f in findings))
            self.assertTrue(any(f.check == "description-person" and f.authority == "heuristic" for f in findings))
        out = io.StringIO()
        with redirect_stdout(out):
            code = lint.main([str(self.root), "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.getvalue())["exit"], 0)

    def test_portable_and_client_authority(self):
        self.root.rename(self.root.with_name("claude-fixture"))
        self.root = self.root.with_name("claude-fixture")
        (self.root / "evals/evals.json").write_text(json.dumps(suite("claude-fixture")))
        self.write("name: claude-fixture\ndescription: Does fixture work")
        self.assert_passes()
        self.assert_passes("pi")
        findings, summary = self.check("claude-code")
        self.assertGreater(summary["fail"], 0)
        self.assertTrue(any(f.check == "name-reserved" and f.authority == "platform" for f in findings))

    def test_extensions_have_target_scoped_types(self):
        self.write('name: fixture\ndescription: Does fixture work\ndisable-model-invocation: "yes"')
        self.assert_passes()  # Unknown portable extension gets compatibility advice.
        findings, summary = self.check("pi")
        self.assertGreater(summary["fail"], 0)
        self.assertTrue(any(f.check == "field-type" and f.authority == "platform" for f in findings))
        self.write("name: fixture\ndescription: Does fixture work\ndisable-model-invocation: true\nuser-invocable: false")
        self.assert_passes("claude-code")

    def test_claude_boolean_aliases_do_not_become_portable_errors(self):
        for value in ('"yes"', '"OFF"', '"1"', "0", "true", "false"):
            self.write("name: fixture\ndescription: Does fixture work\nuser-invocable: " + value)
            self.assert_passes("claude-code")
        self.write("name: fixture\ndescription: Does fixture work\nuser-invocable: []")
        self.assertGreater(self.check("claude-code")[1]["fail"], 0)

    def test_crlf_costs_count_actual_utf8_bytes(self):
        self.write(newline="\r\n")
        _, summary = self.assert_passes()
        self.assertEqual(summary["bytes"], len((self.root / "SKILL.md").read_bytes()))
        self.assertEqual(summary["metadata_bytes"] + summary["body_bytes"], summary["bytes"])

    def test_unicode_lowercase_name(self):
        self.root.rename(self.root.with_name("résumé"))
        self.root = self.root.with_name("résumé")
        (self.root / "evals/evals.json").write_text(json.dumps(suite("résumé")))
        self.write("name: résumé\ndescription: Describes résumé review tasks.")
        self.assert_passes()

    def test_local_evals_shape_and_duplicate_ids(self):
        invalid = [{}, [], {**suite(), "schema": True}, {**suite(), "cases": []},
                   {**suite(), "requiredProfiles": ["balanced/default"]}]
        for field, value in (("id", None), ("expectedBehavior", []), ("forbiddenBehavior", ["one", False]), ("prompt", "")):
            data = copy.deepcopy(suite())
            data["cases"][0][field] = value
            invalid.append(data)
        duplicate = suite()
        duplicate["cases"][1]["id"] = duplicate["cases"][0]["id"]
        invalid.append(duplicate)
        for data in invalid:
            (self.root / "evals/evals.json").write_text(json.dumps(data))
            findings, summary = self.check()
            self.assertGreater(summary["fail"], 0)
            self.assertTrue(any(f.check == "evals-format" and f.authority == "local" for f in findings))
        (self.root / "evals/evals.json").write_text("{")
        self.assertGreater(self.check()[1]["fail"], 0)

    def test_missing_evals_is_local_policy_advice(self):
        (self.root / "evals/evals.json").unlink()
        findings, _ = self.assert_passes()
        self.assertTrue(any(f.check == "evals-missing" and f.authority == "local" for f in findings))

    def test_static_context_and_padding_independence(self):
        (self.root / "workflows").mkdir()
        (self.root / "references").mkdir()
        (self.root / "assets").mkdir()
        (self.root / "scripts").mkdir()
        self.write(body="# Fixture\nRead `workflows/one.md` for one, `workflows/two.md` for two.\n")
        (self.root / "workflows/one.md").write_text("Read `references/shared.md`. Run `scripts/x.py`.\n")
        (self.root / "workflows/two.md").write_text("Read `references/shared.md`.\n")
        (self.root / "references/shared.md").write_text("Shared safety info\n")
        (self.root / "scripts/x.py").write_text("print('result')\n")
        (self.root / "assets/padding.txt").write_text("small")
        findings, before = self.assert_passes()
        (self.root / "assets/padding.txt").write_text("large" * 10000)
        _, after = self.assert_passes()
        self.assertEqual(before["routes"], after["routes"])
        self.assertGreater(after["bundle_bytes"], before["bundle_bytes"])
        self.assertEqual(before["fail"], after["fail"])
        self.assertFalse(any(f.check == "budget-route" for f in findings))
        self.assertGreater(before["metadata_bytes"], 0)
        self.assertGreater(before["body_bytes"], 0)
        for scenario in before["routes"].values():
            self.assertEqual(scenario["kind"], "static referenced-material estimate")
            self.assertNotIn("scripts/x.py", scenario["files"])
            self.assertNotIn("share", scenario)
            self.assertIn("references/shared.md", scenario["files"])

    def test_cli_format_fail_exit_and_finding_shape(self):
        self.write('name: fixture\ndescription: "unclosed')
        out = io.StringIO()
        with redirect_stdout(out):
            code = lint.main(["--json", "--target", "portable", str(self.root)])
        self.assertEqual(code, 1)
        d = json.loads(out.getvalue())
        self.assertEqual(d["exit"], 1)
        self.assertTrue(all("authority" in f for f in d["skills"][0]["findings"]))

    def test_missing_skill_reports_failure(self):
        (self.root / "SKILL.md").unlink()
        self.assertEqual(self.check()[1]["fail"], 1)


if __name__ == "__main__":
    unittest.main()
