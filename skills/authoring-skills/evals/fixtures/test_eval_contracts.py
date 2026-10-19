#!/usr/bin/env python3
"""Frozen discovery labels target the named skill, not presence of a keyword.

Definition/fixture checks only: no model execution, task-quality or trigger-rate claim.
"""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL / "scripts"))
import lint_skill as lint

# Original evidence at repository revision 66b43cb; new definitions must not relabel it.
HISTORY_DIGEST = "c89d04b590c99b8fc51fcc4c9cb7f4ec1514ea04862730ad39ad9d78f3a24e8b"
PROFILES = ["fast/economical", "balanced/default", "highest-reasoning"]
CASE_IDS = {"authoring-skills-create", "authoring-skills-improve", "authoring-skills-audit",
            "authoring-skills-tune-trigger", "authoring-skills-review-only", "authoring-skills-targeted-repair"}


class EvalContractTests(unittest.TestCase):
    def test_six_execution_cases_and_profile_contract(self):
        path = SKILL / "evals/evals.json"
        data = json.loads(path.read_text())
        self.assertEqual(data["schema"], 1)
        self.assertEqual(data["skill"], "authoring-skills")
        self.assertEqual(data["requiredProfiles"], PROFILES)
        self.assertEqual(len(data["cases"]), 6)
        self.assertEqual({case["id"] for case in data["cases"]}, CASE_IDS)
        findings = []
        lint.validate_evals(str(path), "authoring-skills", lambda *args: findings.append(args))
        self.assertEqual(findings, [])

    def test_historical_evidence_unchanged(self):
        data = json.loads((SKILL / "evals/evals.json").read_text())
        history = {key: data[key] for key in ("baseline", "results", "results_matrix")}
        digest = hashlib.sha256(json.dumps(history, sort_keys=True).encode()).hexdigest()
        self.assertEqual(digest, HISTORY_DIGEST)

    def test_discovery_corpus_counts_types_and_identity(self):
        data = json.loads((SKILL / "evals/trigger-queries.json").read_text())
        self.assertEqual(data["schema"], 1)
        self.assertEqual(data["skill"], "authoring-skills")
        queries = data["queries"]
        self.assertEqual(len(queries), 26)
        self.assertEqual(len({q["id"] for q in queries}), 26)
        normalized = {" ".join(q["prompt"].casefold().split()) for q in queries}
        self.assertEqual(len(normalized), 26)
        self.assertEqual({q["split"] for q in queries}, {"train", "validation", "fresh"})
        for query in queries:
            self.assertIs(type(query["shouldTrigger"]), bool)
            self.assertTrue(isinstance(query["id"], str) and query["id"].startswith("authoring-skills-"))
            self.assertTrue(isinstance(query["prompt"], str) and query["prompt"].strip())
        for split, size in (("train", 12), ("validation", 8), ("fresh", 6)):
            subset = [q for q in queries if q["split"] == split]
            self.assertEqual(len(subset), size)
            self.assertEqual(sum(q["shouldTrigger"] for q in subset), size // 2)

    def test_template_retains_execution_schema(self):
        data = json.loads((SKILL / "templates/evals.json").read_text())
        self.assertEqual(data["schema"], 1)
        self.assertEqual(data["requiredProfiles"], PROFILES)
        self.assertEqual(len(data["cases"]), 3)
        for case in data["cases"]:
            self.assertGreaterEqual(len(case["expectedBehavior"]), 2)
            self.assertGreaterEqual(len(case["forbiddenBehavior"]), 2)
            self.assertTrue(all(isinstance(v, str) and v.strip() for v in case["expectedBehavior"] + case["forbiddenBehavior"]))

    def test_simulated_skill_packages_stay_outside_discovery_tree(self):
        fixtures = Path(__file__).parent
        self.assertEqual(list(fixtures.rglob("SKILL.md")), [])
        active_skills = SKILL.parent.resolve()
        with tempfile.TemporaryDirectory(prefix="authoring-skill-fixture-") as tmp:
            root = Path(tmp).resolve()
            self.assertFalse(root == active_skills or active_skills in root.parents)
            package = root / "sample"
            package.mkdir()
            (package / "SKILL.md").write_text("---\nname: sample\ndescription: Tests fixture isolation.\n---\nRead needed sections.\n")
            self.assertTrue((package / "SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
