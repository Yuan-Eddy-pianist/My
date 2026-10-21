from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


@unittest.skipUnless(shutil.which("zsh"), "zsh is required by the skill installers")
class SkillInstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="my-skills-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / "repo with spaces"
        self.user_root = self.root / "user with spaces"
        self.repo.mkdir()
        source = Path(__file__).resolve().parents[1]
        for name in ["install-skills.sh", "uninstall-skills.sh", "skills-common.zsh"]:
            shutil.copy2(source / name, self.repo / name)
        self.personal = self.repo / ".agent/skills"
        self.write(self.personal / "teach/SKILL.md", "personal tutorial")
        self.write(self.personal / "score-dsl/SKILL.md", "personal score editing")
        self.canvas = self.user_root / ".cursor/skills-cursor/canvas"
        self.write(self.canvas / "SKILL.md", "managed canvas")
        self.system_marker = self.user_root / ".codex/skills/.system/example/SKILL.md"
        self.write(self.system_marker, "managed system skill")
        self.env = dict(os.environ, MY_SKILLS_HOME=str(self.user_root))

    @staticmethod
    def write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def run_script(self, name: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["zsh", str(self.repo / name), *args],
            env=self.env, text=True, capture_output=True, check=True,
        )

    def test_install_links_personal_skills_and_managed_canvas_idempotently(self) -> None:
        self.run_script("install-skills.sh", "cursor", "codex")
        self.run_script("install-skills.sh", "cursor", "codex")
        self.assertEqual((self.user_root / ".agents/skills").resolve(), self.personal)
        self.assertEqual((self.user_root / ".cursor/skills").resolve(), self.personal)
        self.assertEqual((self.user_root / ".codex/skills/teach").resolve(), self.personal / "teach")
        self.assertEqual((self.user_root / ".codex/skills/canvas").resolve(), self.canvas)
        self.assertFalse((self.personal / "canvas").exists())
        self.assertEqual(self.system_marker.read_text(), "managed system skill")
        self.assertEqual((self.canvas / "SKILL.md").read_text(), "managed canvas")

    def test_missing_cursor_canvas_does_not_copy_or_invent_it(self) -> None:
        shutil.rmtree(self.canvas)
        result = self.run_script("install-skills.sh", "codex")
        self.assertIn("Canvas not linked", result.stderr)
        self.assertTrue((self.user_root / ".agents/skills").is_symlink())
        self.assertFalse((self.user_root / ".codex/skills/canvas").is_symlink())

    def test_install_preserves_conflicting_skill_directories_and_links(self) -> None:
        other = self.root / "other skill"
        self.write(other / "SKILL.md", "foreign skill")
        self.write(self.user_root / ".codex/skills/teach/SKILL.md", "existing local skill")
        (self.user_root / ".codex/skills/canvas").symlink_to(other, target_is_directory=True)
        self.run_script("install-skills.sh", "codex")
        self.assertEqual((self.user_root / ".codex/skills/teach/SKILL.md").read_text(), "existing local skill")
        self.assertEqual((self.user_root / ".codex/skills/canvas").resolve(), other)
        self.assertFalse(list((self.user_root / ".codex/skills").glob("*.bak.*")))

    def test_uninstall_removes_owned_links_and_keeps_managed_sources(self) -> None:
        self.run_script("install-skills.sh", "all")
        foreign = self.root / "foreign"
        self.write(foreign / "SKILL.md", "foreign")
        link = self.user_root / ".codex/skills/score-dsl"
        link.unlink()
        link.symlink_to(foreign, target_is_directory=True)
        self.run_script("uninstall-skills.sh", "all")
        for rel in [".agents/skills", ".cursor/skills", ".claude/skills", ".config/opencode/skills", ".codex/skills/teach", ".codex/skills/canvas"]:
            self.assertFalse((self.user_root / rel).is_symlink(), rel)
        self.assertEqual(link.resolve(), foreign)
        self.assertTrue((self.personal / "teach/SKILL.md").is_file())
        self.assertEqual((self.canvas / "SKILL.md").read_text(), "managed canvas")
        self.assertEqual(self.system_marker.read_text(), "managed system skill")

    def test_legacy_aliases_are_recognized(self) -> None:
        legacy = self.repo / ".cursor/personal-skills"
        legacy.parent.mkdir()
        legacy.symlink_to(self.personal, target_is_directory=True)
        root_link = self.user_root / ".agents/skills"
        root_link.parent.mkdir()
        root_link.symlink_to(legacy, target_is_directory=True)
        (self.user_root / ".codex/skills/teach").symlink_to(legacy / "teach", target_is_directory=True)
        self.run_script("install-skills.sh", "codex")
        self.assertEqual(root_link.resolve(), self.personal)
        self.run_script("uninstall-skills.sh", "codex")
        self.assertFalse(root_link.is_symlink())
        self.assertFalse((self.user_root / ".codex/skills/teach").is_symlink())

    def test_help_does_not_modify_user_links(self) -> None:
        legacy = self.user_root / ".gemini/skills"
        legacy.parent.mkdir()
        legacy.symlink_to(self.personal, target_is_directory=True)
        for name in ["install-skills.sh", "uninstall-skills.sh"]:
            self.run_script(name, "--help")
        self.assertTrue(legacy.is_symlink())
        self.assertFalse((self.user_root / ".agents").exists())


if __name__ == "__main__":
    unittest.main()
