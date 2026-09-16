import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SKILLS = {"iskristalisi-ideju", "pojasni-mi"}


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise AssertionError(f"Nedostaje YAML frontmatter: {path}")
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip().strip('"')
    return values


class RepositoryContractTests(unittest.TestCase):
    def test_repository_contains_exactly_two_public_skills(self) -> None:
        found = {
            path.parent.name
            for path in (ROOT / "skills").glob("*/SKILL.md")
        }
        self.assertEqual(found, EXPECTED_SKILLS)

    def test_skill_frontmatter_matches_agent_skills_spec(self) -> None:
        for slug in EXPECTED_SKILLS:
            path = ROOT / "skills" / slug / "SKILL.md"
            values = frontmatter(path)
            self.assertEqual(values.get("name"), slug)
            self.assertGreater(len(values.get("description", "")), 20)
            self.assertLessEqual(len(values["description"]), 1024)
            self.assertEqual(values.get("license"), "MIT")

    def test_claude_plugin_is_a_thin_wrapper(self) -> None:
        manifest = json.loads(
            (ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["name"], "it-polako-skills")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertNotIn("hooks", manifest)
        self.assertNotIn("mcpServers", manifest)

    def test_claude_marketplace_exposes_the_plugin(self) -> None:
        marketplace = json.loads(
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(marketplace["name"], "it-polako")
        self.assertEqual(marketplace["owner"]["name"], "IT Polako")
        self.assertEqual(len(marketplace["plugins"]), 1)
        self.assertEqual(marketplace["plugins"][0]["name"], "it-polako-skills")
        self.assertEqual(marketplace["plugins"][0]["source"], "./")

    def test_each_skill_has_codex_metadata(self) -> None:
        for slug in EXPECTED_SKILLS:
            metadata = ROOT / "skills" / slug / "agents" / "openai.yaml"
            text = metadata.read_text(encoding="utf-8")
            self.assertIn("display_name:", text)
            self.assertIn("short_description:", text)
            self.assertIn("default_prompt:", text)

    def test_pojasni_mi_requires_explicit_codex_invocation(self) -> None:
        metadata = (
            ROOT / "skills" / "pojasni-mi" / "agents" / "openai.yaml"
        ).read_text(encoding="utf-8")
        self.assertIn("allow_implicit_invocation: false", metadata)

    def test_iskristalisi_ideju_handles_early_stop_and_ready_ideas(self) -> None:
        text = (ROOT / "skills" / "iskristalisi-ideju" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("traži završetak", text)
        self.assertIn("već dovoljno razrađena", text)
        self.assertIn("ne prolazi mehanički", text)

    def test_radni_nacrt_contains_a_synthetic_example(self) -> None:
        text = (
            ROOT
            / "skills"
            / "iskristalisi-ideju"
            / "references"
            / "radni-nacrt.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Sintetički primer", text)
        self.assertIn("Otvoreno pitanje", text)

    def test_readme_has_copy_paste_install_and_run_examples(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        required = (
            "npx --yes skills@1.5.26 add rskendzic/it-polako-skills",
            "/plugin marketplace add rskendzic/it-polako-skills",
            "/plugin install it-polako-skills@it-polako",
            "/it-polako-skills:pojasni-mi",
            "/it-polako-skills:iskristalisi-ideju",
            "$pojasni-mi",
            "$iskristalisi-ideju",
            "mapa-razumevanja.html",
        )
        for fragment in required:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, readme)
        self.assertNotIn("skills@latest", readme)
        self.assertIn("--from skills-ref==0.1.1", readme)

    def test_new_idea_edge_case_evals_exist(self) -> None:
        cases = json.loads((ROOT / "evals" / "cases.json").read_text(encoding="utf-8"))
        ids = {case["id"] for case in cases}
        self.assertTrue(
            {
                "ideja-korisnik-zavrsava",
                "ideja-vec-razradjena",
                "ideja-korisnik-ne-zna",
                "ideja-prerani-prd",
            }.issubset(ids)
        )

    def test_pojasni_mi_keeps_modes_internal(self) -> None:
        text = (ROOT / "skills" / "pojasni-mi" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Idi u detalje", text)
        self.assertIn("Proveri me", text)
        self.assertNotIn("Uđi dublje", text)
        self.assertIn("eksplicit", text.lower())
        self.assertIn("lokal", text.lower())
        self.assertIn("putanju do direktorijuma ovog skilla", text)
        self.assertIn("apsolutnu putanju", text)

    def test_pojasni_mi_has_type_specific_rules(self) -> None:
        refs = ROOT / "skills" / "pojasni-mi" / "references"
        expected = {
            "ugovori.md",
            "tabele.md",
            "kod.md",
            "dokumenti-i-dijagrami.md",
            "format-mape.md",
        }
        self.assertTrue(expected.issubset({p.name for p in refs.glob("*.md")}))

    def test_evals_use_only_synthetic_fixtures(self) -> None:
        cases = json.loads((ROOT / "evals" / "cases.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(cases), 6)
        for case in cases:
            self.assertTrue(case["synthetic"])
            self.assertTrue(case["must"])
            self.assertTrue(case["must_not"])


if __name__ == "__main__":
    unittest.main()
