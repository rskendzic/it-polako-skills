#!/usr/bin/env python3
"""Validate the portable skill contract without third-party dependencies."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NoReturn


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SKILLS = {"iskristalisi-ideju", "pojasni-mi"}
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_PATTERN = re.compile(r"^---\n(.*?)\n---\n(.+)$", re.DOTALL)


def fail(message: str) -> NoReturn:
    raise ValueError(message)


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_PATTERN.match(text)
    if match is None:
        fail(f"Neispravan frontmatter: {path.relative_to(ROOT)}")
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if line.startswith((" ", "\t")) or ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"')
    return values, match.group(2)


def validate_skills() -> None:
    skill_files = list((ROOT / "skills").glob("*/SKILL.md"))
    found = {path.parent.name for path in skill_files}
    if found != EXPECTED_SKILLS:
        fail(f"Očekivana su tačno dva skilla {sorted(EXPECTED_SKILLS)}, pronađeno {sorted(found)}")
    for path in skill_files:
        values, body = parse_frontmatter(path)
        name = values.get("name", "")
        description = values.get("description", "")
        if name != path.parent.name or NAME_PATTERN.fullmatch(name) is None:
            fail(f"Neispravan name u {path.relative_to(ROOT)}")
        if not 1 <= len(description) <= 1024:
            fail(f"Description mora imati 1-1024 znaka u {path.relative_to(ROOT)}")
        if values.get("license") != "MIT":
            fail(f"Nedostaje MIT licenca u {path.relative_to(ROOT)}")
        if not body.strip():
            fail(f"Prazno telo skilla: {path.relative_to(ROOT)}")
        openai = path.parent / "agents" / "openai.yaml"
        if not openai.is_file():
            fail(f"Nedostaje {openai.relative_to(ROOT)}")
        metadata = openai.read_text(encoding="utf-8")
        for field in ("display_name:", "short_description:", "default_prompt:"):
            if field not in metadata:
                fail(f"Nedostaje {field} u {openai.relative_to(ROOT)}")


def validate_plugin() -> None:
    manifest_path = ROOT / ".claude-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("name") != "it-polako-skills":
        fail("Plugin name mora biti it-polako-skills")
    if manifest.get("skills") != "./skills/":
        fail("Plugin mora upućivati na kanonski ./skills/ direktorijum")
    forbidden = {"hooks", "mcpServers", "commands", "agents"} & manifest.keys()
    if forbidden:
        fail(f"Plugin više nije tanak omotač: {sorted(forbidden)}")

    marketplace_path = ROOT / ".claude-plugin" / "marketplace.json"
    marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    if marketplace.get("name") != "it-polako":
        fail("Marketplace name mora biti it-polako")
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or len(plugins) != 1:
        fail("Marketplace mora izlagati tačno jedan plugin")
    if plugins[0].get("name") != "it-polako-skills" or plugins[0].get("source") != "./":
        fail("Marketplace mora izlagati it-polako-skills iz korena repozitorijuma")


def validate_evals() -> None:
    cases = json.loads((ROOT / "evals" / "cases.json").read_text(encoding="utf-8"))
    if not isinstance(cases, list) or len(cases) < 6:
        fail("Potrebno je najmanje šest eval slučajeva")
    ids: set[str] = set()
    for case in cases:
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id or case_id in ids:
            fail("Eval id mora biti jedinstven neprazan tekst")
        ids.add(case_id)
        if case.get("skill") not in EXPECTED_SKILLS:
            fail(f"Nepoznat skill u evalu: {case_id}")
        if case.get("synthetic") is not True:
            fail(f"Eval nije označen kao sintetički: {case_id}")
        if not case.get("must") or not case.get("must_not"):
            fail(f"Eval mora imati must i must_not: {case_id}")


def validate_rendering() -> None:
    renderer = ROOT / "skills" / "pojasni-mi" / "scripts" / "render_map.py"
    examples = list((ROOT / "examples" / "pojasni-mi").glob("*.json"))
    if not examples:
        fail("Nedostaje JSON primer za Pojasni mi")
    with tempfile.TemporaryDirectory() as tmp:
        for source in examples:
            output = Path(tmp) / f"{source.stem}.html"
            result = subprocess.run(
                [sys.executable, str(renderer), str(source), str(output)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode != 0:
                fail(f"Renderer je pukao za {source.name}: {result.stderr.strip()}")
            html = output.read_text(encoding="utf-8")
            if "<script src=" in html.lower() or "<link rel=" in html.lower():
                fail(f"HTML nije samostalan: {source.name}")
            extracted = Path(tmp) / f"{source.stem}.roundtrip.json"
            roundtrip = subprocess.run(
                [sys.executable, str(renderer), "--extract", str(output), str(extracted)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            if roundtrip.returncode != 0:
                fail(f"Round-trip je pukao za {source.name}: {roundtrip.stderr.strip()}")
            original_data = json.loads(source.read_text(encoding="utf-8"))
            extracted_data = json.loads(extracted.read_text(encoding="utf-8"))
            if original_data != extracted_data:
                fail(f"Round-trip je promenio podatke: {source.name}")


def main() -> int:
    try:
        validate_skills()
        validate_plugin()
        validate_evals()
        validate_rendering()
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Puklo je: {error}", file=sys.stderr)
        return 1
    print("Prolazi: 2 skilla, plugin, Codex metapodaci, evalovi i offline HTML.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
