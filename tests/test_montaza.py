import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "it-polako-montaza"
HELPER = SKILL / "scripts" / "hlg_boje.py"


def load_helper():
    spec = importlib.util.spec_from_file_location("hlg_boje", HELPER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class HlgHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.hlg = load_helper()

    def test_reference_white_lands_on_75_percent_hlg(self) -> None:
        self.assertEqual(self.hlg.srgb_to_hlg((255, 255, 255)), (191, 191, 191))

    def test_brand_yellow_and_black(self) -> None:
        self.assertEqual(self.hlg.srgb_to_hlg(self.hlg.parse_hex("#FBD800")), (185, 176, 65))
        self.assertEqual(self.hlg.srgb_to_hlg((0, 0, 0)), (0, 0, 0))

    def test_preview_lut_is_complete_and_monotonic_on_grey(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pregled.cube"
            result = subprocess.run(
                [sys.executable, str(HELPER), "lut", str(out), "--size", "9"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            lines = out.read_text(encoding="utf-8").splitlines()
        self.assertIn("LUT_3D_SIZE 9", lines)
        data = [tuple(map(float, l.split())) for l in lines if l[:1].isdigit()]
        self.assertEqual(len(data), 9 ** 3)
        grey = [data[i * (81 + 9 + 1)][0] for i in range(9)]
        self.assertEqual(grey, sorted(grey))
        self.assertTrue(all(0.0 <= v <= 1.0 for row in data for v in row))

    def test_rejects_malformed_hex(self) -> None:
        with self.assertRaises(ValueError):
            self.hlg.parse_hex("#FFF")


class MontazaContractTests(unittest.TestCase):
    def test_skill_keeps_learned_rules(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for fragment in ("podeljen ekran", "start_time", "ponovljen", "uporedo sa referencom", "sha256"):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)

    def test_references_carry_measured_look_and_pipeline(self) -> None:
        izgled = (SKILL / "references" / "izgled.md").read_text(encoding="utf-8")
        self.assertIn("title-heavy.ttf", izgled)
        self.assertIn("bez obrisa", izgled)
        self.assertIn("#FBD800", izgled)
        hlg = (SKILL / "references" / "hlg.md").read_text(encoding="utf-8")
        self.assertIn("-frames:v N", hlg)
        self.assertIn("arib-std-b67", hlg)

    def test_skill_keeps_c14_lessons(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for fragment in ("posle pauze", "izgovoreni oblik", "reč po reč", "međunaslove"):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)
        izgled = (SKILL / "references" / "izgled.md").read_text(encoding="utf-8")
        self.assertIn("iza govornika", izgled)
        self.assertIn("vrh glave", izgled)
        hlg = (SKILL / "references" / "hlg.md").read_text(encoding="utf-8")
        self.assertIn("bframes=0", hlg)

    def test_montaza_requires_explicit_codex_invocation(self) -> None:
        metadata = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("allow_implicit_invocation: false", metadata)


if __name__ == "__main__":
    unittest.main()
