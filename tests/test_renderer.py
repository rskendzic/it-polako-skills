import json
import re
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "skills" / "pojasni-mi" / "scripts" / "render_map.py"
FIXTURE = ROOT / "examples" / "pojasni-mi" / "sinteticki-ugovor.json"


class TagCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append((tag, dict(attrs)))


class RendererTests(unittest.TestCase):
    def render(self, source: Path, output: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(RENDERER), str(source), str(output)],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_renderer_produces_one_self_contained_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "mapa-razumevanja.html"
            result = self.render(FIXTURE, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual([p.name for p in Path(tmp).iterdir()], [output.name])
            html = output.read_text(encoding="utf-8")
            self.assertIn("<!doctype html>", html.lower())
            self.assertIn("Mapa razumevanja", html)
            self.assertIn("Idi u detalje", html)
            self.assertIn("Proveri me", html)
            self.assertIn("application/json", html)
            self.assertNotIn("<script src=", html.lower())
            self.assertNotIn("<link rel=", html.lower())

    def test_documented_required_format_is_renderable(self) -> None:
        reference = (
            ROOT / "skills" / "pojasni-mi" / "references" / "format-mape.md"
        ).read_text(encoding="utf-8")
        match = re.search(r"```json\n(.*?)\n```", reference, re.DOTALL)
        if match is None:
            self.fail("Nedostaje dokumentovani JSON primer")
        payload = json.loads(match.group(1))
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "documented.json"
            output = Path(tmp) / "mapa.html"
            source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            result = self.render(source, output)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_renderer_preserves_source_traceability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "mapa.html"
            result = self.render(FIXTURE, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            html = output.read_text(encoding="utf-8")
            self.assertIn("Član 4", html)
            self.assertIn("Izvor", html)
            self.assertIn("Tumačenje", html)
            self.assertIn("Nije pravni savet", html)

    def test_renderer_rejects_claim_without_source_reference(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["sections"][0]["source_refs"] = []
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "invalid.json"
            output = Path(tmp) / "mapa.html"
            source.write_text(json.dumps(payload), encoding="utf-8")
            result = self.render(source, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("source_refs", result.stderr)
            self.assertFalse(output.exists())

    def test_renderer_rejects_unresolvable_relationship_source(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["relationships"][0]["source_refs"] = ["Nepostojeći član"]
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "invalid.json"
            output = Path(tmp) / "mapa.html"
            source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            result = self.render(source, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("source_refs", result.stderr)
            self.assertFalse(output.exists())

    def test_renderer_rejects_non_finite_and_boolean_numbers(self) -> None:
        invalid_values = [
            float("nan"),
            True,
            10**400,
            float(2**53),
            1e300,
        ]
        for invalid in invalid_values:
            with self.subTest(value=invalid):
                payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
                payload["what_if"][0]["factor"] = invalid
                with tempfile.TemporaryDirectory() as tmp:
                    source = Path(tmp) / "invalid.json"
                    output = Path(tmp) / "mapa.html"
                    source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                    result = self.render(source, output)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("factor", result.stderr)
                    self.assertFalse(output.exists())

    def test_renderer_rejects_slider_step_below_range_resolution(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        scenario = payload["what_if"][0]
        scenario["min"] = 0
        scenario["max"] = 100
        scenario["initial"] = 10
        scenario["step"] = 5e-324
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "invalid.json"
            output = Path(tmp) / "mapa.html"
            source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            result = self.render(source, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("step je premali", result.stderr)
            self.assertFalse(output.exists())

    def test_renderer_rejects_impractical_slider_step_count(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        scenario = payload["what_if"][0]
        scenario["min"] = 0
        scenario["max"] = 100
        scenario["initial"] = 10
        scenario["step"] = 0.00001
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "invalid.json"
            output = Path(tmp) / "mapa.html"
            source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            result = self.render(source, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("više od 1000000 koraka", result.stderr)
            self.assertFalse(output.exists())

    def test_renderer_rejects_unsupported_precision(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["what_if"][0]["precision"] = 21
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "invalid.json"
            output = Path(tmp) / "mapa.html"
            source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            result = self.render(source, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("precision", result.stderr)
            self.assertFalse(output.exists())

    def test_renderer_rejects_reserved_or_colliding_dom_ids(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["sections"][0]["id"] = "what-if"
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "reserved.json"
            output = Path(tmp) / "mapa.html"
            source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            result = self.render(source, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("rezervisan", result.stderr)

        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["sections"][1]["id"] = payload["sections"][0]["id"] + "-details"
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "collision.json"
            output = Path(tmp) / "mapa.html"
            source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            result = self.render(source, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("DOM", result.stderr)

    def test_renderer_does_not_turn_source_markup_into_dom(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["sections"][0]["summary"] = '<img src="https://evil.invalid/x" onerror="alert(1)">'
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "hostile.json"
            output = Path(tmp) / "mapa.html"
            source.write_text(json.dumps(payload), encoding="utf-8")
            result = self.render(source, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            collector = TagCollector()
            collector.feed(output.read_text(encoding="utf-8"))
            remote_media = [
                (tag, attrs)
                for tag, attrs in collector.tags
                if tag in {"img", "script", "link", "iframe"}
                and any(
                    (attrs.get(key) or "").startswith(("http://", "https://"))
                    for key in ("src", "href")
                )
            ]
            self.assertEqual(remote_media, [])

    def test_repository_validator_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_repo.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Prolazi", result.stdout)


if __name__ == "__main__":
    unittest.main()
