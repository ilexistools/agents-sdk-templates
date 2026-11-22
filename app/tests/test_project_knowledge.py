"""The knowledge given to AI coding assistants stays consistent with the project.

Run with: uv run --locked python -m unittest app.tests.test_project_knowledge -v
"""

import re
import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / ".agents" / "skills"
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")


def skill_dirs():
    return sorted(path for path in SKILLS.iterdir() if (path / "SKILL.md").is_file())


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


class ProjectKnowledgeTests(unittest.TestCase):
    def test_skills_have_valid_front_matter(self):
        for skill in skill_dirs():
            with self.subTest(skill=skill.name):
                match = FRONTMATTER.match(read(skill / "SKILL.md"))
                self.assertIsNotNone(match)
                fields = dict(line.split(": ", 1) for line in match.group(1).splitlines() if ": " in line)
                self.assertEqual(fields.get("name"), skill.name)
                self.assertTrue(re.fullmatch(r"[a-z0-9-]{1,64}", skill.name))
                self.assertTrue(40 <= len(fields.get("description", "")) <= 1024)
                self.assertTrue((skill / "agents" / "openai.yaml").is_file(), "Codex interface metadata")

    def test_claude_code_mirrors_are_in_sync(self):
        sync = runpy.run_path(str(ROOT / "scripts" / "sync_skills.py"))
        self.assertEqual(sync["stale"](), [], "Run: uv run --locked python scripts/sync_skills.py")

    def test_relative_links_resolve(self):
        documents = [ROOT / "AGENTS.md", ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
        for skill in skill_dirs():
            documents += sorted(skill.rglob("*.md"))
        for document in documents:
            for target in LINK.findall(read(document)):
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                with self.subTest(document=str(document.relative_to(ROOT)), target=target):
                    self.assertTrue((document.parent / target).exists())

    def test_agents_md_indexes_every_skill_and_guide(self):
        text = read(ROOT / "AGENTS.md")
        for skill in skill_dirs():
            with self.subTest(skill=skill.name):
                self.assertIn(skill.name, text)
        for guide in ("docs/architecture.md", "docs/catalog-standards.md"):
            self.assertIn(guide, text)
        self.assertIn("@AGENTS.md", read(ROOT / "CLAUDE.md"))

    def test_documented_commands_exist(self):
        text = read(ROOT / "AGENTS.md") + "".join(read(path) for skill in skill_dirs()
                                                  for path in skill.rglob("*.md"))
        for module in set(re.findall(r"python -m (app(?:\.[a-z_]+)*)", text)):
            path = ROOT / Path(*module.split("."))
            with self.subTest(module=module):
                self.assertTrue(path.with_suffix(".py").is_file() or (path / "__main__.py").is_file()
                                or path.is_dir())


if __name__ == "__main__":
    unittest.main()
