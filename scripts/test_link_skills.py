"""Isolated checks for skill linking and generated hook/command quoting."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class LinkSkillsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / "clone with spaces ' $literal"
        self.repo.mkdir()
        self.home = self.root / "home"
        self.home.mkdir()
        self.env = {**os.environ, "HOME": str(self.home)}
        self.run_command("git", "init", "-q")
        (self.repo / "scripts").mkdir()
        self.script = self.repo / "scripts/link-skills.sh"
        shutil.copy2(Path(__file__).with_name("link-skills.sh"), self.script)
        self.add_skill("first")

    def run_command(self, *args, cwd=None):
        return subprocess.run(
            args, cwd=cwd or self.repo, env=self.env, check=True,
            text=True, capture_output=True,
        ).stdout

    def add_skill(self, name):
        skill = self.repo / "skills" / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("# Test skill\n")
        return skill

    def test_hooks_preserve_custom_targets_from_other_working_directory(self):
        relative = "../target with spaces ' $literal"
        target = (self.repo / relative).resolve()
        second = self.root / "second target"
        self.run_command(str(self.script), "--install-hooks", relative, str(second))
        self.assertEqual((target / "first").resolve(), self.repo / "skills/first")
        self.add_skill("added")
        shutil.rmtree(self.repo / "skills/first")
        # Git runs hooks from the repository root, not the installation cwd.
        nested = self.repo / "nested"
        nested.mkdir()
        self.run_command(str(self.script), "--install-hooks", "../../" + target.name,
                         str(second), cwd=nested)
        for name in ("post-merge", "post-rewrite"):
            with self.subTest(hook=name):
                for dest in (target, second):
                    (dest / "added").unlink(missing_ok=True)
                self.run_command(str(self.repo / ".git/hooks" / name))
                for dest in (target, second):
                    self.assertEqual((dest / "added").resolve(), self.repo / "skills/added")
                    self.assertFalse((dest / "first").is_symlink())
        self.assertFalse((self.home / ".agents").exists())
        self.assertFalse((self.home / ".claude").exists())

    def test_printed_install_command_round_trips_prefix(self):
        skill = self.repo / "skills/first"
        (skill / "package.json").write_text("{}\n")
        output = self.run_command(str(self.script), str(self.root / "target"))
        command = next(line.split("run: ", 1)[1] for line in output.splitlines()
                       if "run: " in line)
        capture = self.root / "npm-args"
        self.env["CAPTURE"] = str(capture)
        self.run_command("bash", "-c",
                         'npm() { printf "%s\\0" "$@" > "$CAPTURE"; }; ' + command)
        self.assertEqual(capture.read_bytes().split(b"\0")[:-1], [
            b"install", b"--prefix", os.fsencode(skill), b"--ignore-scripts",
        ])
        self.assertFalse((skill / "node_modules").exists())

    def test_dry_run_link_prune_and_conflict_safety(self):
        target = self.root / "target"
        self.run_command(str(self.script), "-n", "--install-hooks", str(target))
        self.assertFalse(target.exists())
        self.assertFalse((self.repo / ".git/hooks/post-merge").exists())
        target.mkdir()
        (target / "foreign").symlink_to(self.root / "missing")
        (target / "removed").symlink_to(self.repo / "skills/removed")
        self.add_skill("directory-conflict")
        (target / "directory-conflict").mkdir()
        self.add_skill("link-conflict")
        (target / "link-conflict").symlink_to(self.root / "elsewhere")
        self.run_command(str(self.script), str(target))
        self.assertEqual((target / "first").resolve(), self.repo / "skills/first")
        self.assertFalse((target / "removed").is_symlink())
        self.assertEqual(os.readlink(target / "foreign"), str(self.root / "missing"))
        self.assertEqual(os.readlink(target / "link-conflict"), str(self.root / "elsewhere"))
        self.assertFalse((target / "directory-conflict").is_symlink())
        output = self.run_command(str(self.script), "-n", str(target))
        self.assertNotIn("  ln ", output)
        self.assertNotIn("  rm ", output)


if __name__ == "__main__":
    unittest.main()
