#!/usr/bin/env python3
"""Render a source-traceable understanding map as one offline HTML file."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


ALLOWED_TYPES = {"contract", "spreadsheet", "code", "document", "diagram", "url", "other"}
RESERVED_DOM_IDS = {
    "artifact-type",
    "content",
    "disclaimer",
    "map-data",
    "odnosi",
    "otvorena-pitanja",
    "page-goal",
    "page-title",
    "proveri-me",
    "toc",
    "what-if",
}
JS_MAX_SAFE_INTEGER = 9_007_199_254_740_991
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
DATA_PATTERN = re.compile(
    r'<script type="application/json" id="map-data">(.*?)</script>', re.DOTALL
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def nonempty(value: Any, path: str) -> str:
    require(isinstance(value, str) and value.strip() != "", f"{path} mora biti neprazan tekst")
    return value.strip()


def validate_source_ref(ref: Any, path: str) -> None:
    require(isinstance(ref, dict), f"{path} mora biti objekat")
    nonempty(ref.get("label"), f"{path}.label")
    nonempty(ref.get("quote"), f"{path}.quote")
    if "location" in ref:
        nonempty(ref["location"], f"{path}.location")


def validate_source_labels(value: Any, path: str, available: set[str]) -> None:
    require(isinstance(value, list) and bool(value), f"{path} mora biti neprazna lista")
    for index, label in enumerate(value):
        resolved = nonempty(label, f"{path}[{index}]")
        require(resolved in available, f"{path}[{index}] ne pokazuje na postojeći izvor: {resolved}")


def validate_number(value: Any, path: str) -> None:
    require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{path} mora biti broj, ne boolean")
    if isinstance(value, float):
        require(math.isfinite(value), f"{path} mora biti konačan broj")
    require(abs(value) <= JS_MAX_SAFE_INTEGER, f"{path} nije bezbedno predstavljiv kao JavaScript broj")


def validate_payload(data: Any) -> dict[str, Any]:
    require(isinstance(data, dict), "Koren JSON-a mora biti objekat")
    meta = data.get("meta")
    require(isinstance(meta, dict), "meta mora biti objekat")
    nonempty(meta.get("title"), "meta.title")
    nonempty(meta.get("goal"), "meta.goal")
    artifact_type = nonempty(meta.get("artifact_type"), "meta.artifact_type")
    require(artifact_type in ALLOWED_TYPES, f"meta.artifact_type mora biti jedan od: {', '.join(sorted(ALLOWED_TYPES))}")
    if "disclaimer" in meta:
        nonempty(meta["disclaimer"], "meta.disclaimer")
    if artifact_type == "contract":
        disclaimer = str(meta.get("disclaimer", "")).lower()
        require("pravni savet" in disclaimer, "ugovor mora imati disclaimer koji kaže da sadržaj nije pravni savet")

    sections = data.get("sections")
    require(isinstance(sections, list) and bool(sections), "sections mora biti neprazna lista")
    section_ids: set[str] = set()
    source_labels: set[str] = set()
    for index, section in enumerate(sections):
        path = f"sections[{index}]"
        require(isinstance(section, dict), f"{path} mora biti objekat")
        section_id = nonempty(section.get("id"), f"{path}.id")
        require(ID_PATTERN.fullmatch(section_id) is not None, f"{path}.id mora biti kebab-case")
        require(section_id not in RESERVED_DOM_IDS, f"{path}.id je rezervisan DOM id: {section_id}")
        require(section_id not in section_ids, f"dupliran section id: {section_id}")
        section_ids.add(section_id)
        nonempty(section.get("title"), f"{path}.title")
        nonempty(section.get("summary"), f"{path}.summary")
        nonempty(section.get("why_it_matters"), f"{path}.why_it_matters")
        refs = section.get("source_refs")
        require(isinstance(refs, list) and bool(refs), f"{path}.source_refs mora biti neprazna lista")
        for ref_index, ref in enumerate(refs):
            validate_source_ref(ref, f"{path}.source_refs[{ref_index}]")
            source_labels.add(ref["label"].strip())
        for field in ("details", "consequences", "uncertainties"):
            values = section.get(field, [])
            require(isinstance(values, list), f"{path}.{field} mora biti lista")
            for item_index, item in enumerate(values):
                nonempty(item, f"{path}.{field}[{item_index}]")
    for section_id in section_ids:
        require(
            f"{section_id}-details" not in section_ids,
            f"DOM id kolizija: {section_id}-details je istovremeno section id",
        )

    relationships = data.get("relationships", [])
    require(isinstance(relationships, list), "relationships mora biti lista")
    for index, relation in enumerate(relationships):
        path = f"relationships[{index}]"
        require(isinstance(relation, dict), f"{path} mora biti objekat")
        require(relation.get("from") in section_ids, f"{path}.from ne pokazuje na sekciju")
        require(relation.get("to") in section_ids, f"{path}.to ne pokazuje na sekciju")
        nonempty(relation.get("label"), f"{path}.label")
        validate_source_labels(relation.get("source_refs"), f"{path}.source_refs", source_labels)

    what_if = data.get("what_if", [])
    require(isinstance(what_if, list), "what_if mora biti lista")
    what_if_ids: set[str] = set()
    for index, scenario in enumerate(what_if):
        path = f"what_if[{index}]"
        require(isinstance(scenario, dict), f"{path} mora biti objekat")
        scenario_id = nonempty(scenario.get("id"), f"{path}.id")
        require(ID_PATTERN.fullmatch(scenario_id) is not None, f"{path}.id mora biti kebab-case")
        require(scenario_id not in what_if_ids, f"dupliran what_if id: {scenario_id}")
        what_if_ids.add(scenario_id)
        nonempty(scenario.get("title"), f"{path}.title")
        nonempty(scenario.get("prompt"), f"{path}.prompt")
        kind = scenario.get("kind")
        require(kind in {"choice", "number"}, f"{path}.kind mora biti choice ili number")
        if kind == "choice":
            choices = scenario.get("choices")
            require(isinstance(choices, list) and len(choices) >= 2, f"{path}.choices mora imati bar dve stavke")
            for choice_index, choice in enumerate(choices):
                choice_path = f"{path}.choices[{choice_index}]"
                require(isinstance(choice, dict), f"{choice_path} mora biti objekat")
                nonempty(choice.get("label"), f"{choice_path}.label")
                nonempty(choice.get("outcome"), f"{choice_path}.outcome")
                validate_source_labels(choice.get("source_refs"), f"{choice_path}.source_refs", source_labels)
        else:
            for field in ("min", "max", "step", "base_value", "factor", "offset"):
                validate_number(scenario.get(field), f"{path}.{field}")
            require(scenario["min"] < scenario["max"], f"{path}.min mora biti manje od max")
            require(scenario["step"] > 0, f"{path}.step mora biti veće od nule")
            range_magnitude = max(abs(scenario["min"]), abs(scenario["max"]))
            require(
                scenario["step"] >= math.ulp(float(range_magnitude)),
                f"{path}.step je premali za numeričku rezoluciju opsega",
            )
            require(
                (scenario["max"] - scenario["min"]) / scenario["step"] <= 1_000_000,
                f"{path} ne sme imati više od 1000000 koraka",
            )
            require(scenario["min"] <= scenario["base_value"] <= scenario["max"], f"{path}.base_value je van opsega")
            validate_source_labels(scenario.get("source_refs"), f"{path}.source_refs", source_labels)
            for boundary in (scenario["min"], scenario["max"], scenario["base_value"]):
                validate_number(
                    boundary * scenario["factor"] + scenario["offset"],
                    f"{path}.calculated_result",
                )
            if "precision" in scenario:
                precision = scenario["precision"]
                require(
                    isinstance(precision, int) and not isinstance(precision, bool) and 0 <= precision <= 20,
                    f"{path}.precision mora biti ceo broj od 0 do 20",
                )

    quiz = data.get("quiz", [])
    require(isinstance(quiz, list), "quiz mora biti lista")
    quiz_ids: set[str] = set()
    for index, question in enumerate(quiz):
        path = f"quiz[{index}]"
        require(isinstance(question, dict), f"{path} mora biti objekat")
        question_id = nonempty(question.get("id"), f"{path}.id")
        require(ID_PATTERN.fullmatch(question_id) is not None, f"{path}.id mora biti kebab-case")
        require(question_id not in quiz_ids, f"dupliran quiz id: {question_id}")
        quiz_ids.add(question_id)
        nonempty(question.get("question"), f"{path}.question")
        options = question.get("options")
        require(isinstance(options, list) and len(options) >= 2, f"{path}.options mora imati bar dve stavke")
        for option_index, option in enumerate(options):
            nonempty(option, f"{path}.options[{option_index}]")
        correct_index = question.get("correct_index")
        require(isinstance(correct_index, int) and not isinstance(correct_index, bool), f"{path}.correct_index mora biti ceo broj")
        require(0 <= correct_index < len(options), f"{path}.correct_index je van opsega")
        nonempty(question.get("explanation"), f"{path}.explanation")
        validate_source_labels(question.get("source_refs"), f"{path}.source_refs", source_labels)

    open_questions = data.get("open_questions", [])
    require(isinstance(open_questions, list), "open_questions mora biti lista")
    for index, question in enumerate(open_questions):
        nonempty(question, f"open_questions[{index}]")
    return data


def json_for_html(data: dict[str, Any]) -> str:
    serialized = json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return (
        serialized.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


HTML_TEMPLATE = r'''<!doctype html>
<html lang="sr-Latn">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'">
  <title>Mapa razumevanja</title>
  <style>
    :root {
      color-scheme: light;
      --paper: #f5f0e8;
      --surface: #fffdf8;
      --ink: #171714;
      --muted: #6b675f;
      --line: #d8d0c3;
      --accent: #d64b2a;
      --accent-soft: #f8ded5;
      --source: #efe9df;
      --success: #166534;
      --danger: #9f2415;
      --radius: 14px;
      --shadow: 0 14px 40px rgba(43, 34, 22, .08);
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.55;
    }
    button, input { font: inherit; }
    button { min-height: 44px; }
    button:focus-visible, a:focus-visible, input:focus-visible, [tabindex]:focus-visible {
      outline: 3px solid color-mix(in srgb, var(--accent), white 35%);
      outline-offset: 3px;
    }
    .hero {
      border-bottom: 1px solid var(--line);
      background: var(--surface);
      padding: clamp(2rem, 5vw, 5rem) clamp(1rem, 5vw, 5rem);
    }
    .eyebrow { color: var(--accent); font-weight: 800; letter-spacing: .08em; text-transform: uppercase; font-size: .78rem; }
    h1 { font-family: Georgia, "Times New Roman", serif; font-size: clamp(2.5rem, 7vw, 5.6rem); line-height: .96; max-width: 15ch; margin: .5rem 0 1.25rem; letter-spacing: -.045em; }
    .goal { max-width: 70ch; color: var(--muted); font-size: clamp(1.05rem, 2vw, 1.3rem); text-wrap: pretty; }
    .meta-row { display: flex; flex-wrap: wrap; gap: .6rem; margin-top: 1.5rem; }
    .pill { border: 1px solid var(--line); border-radius: 999px; padding: .35rem .75rem; background: var(--paper); font-size: .85rem; }
    .disclaimer { margin-top: 1.5rem; max-width: 70ch; border: 1px solid #e7ae9f; background: #fff1ed; padding: 1rem; border-radius: 10px; color: #762b1b; }
    .layout { display: grid; grid-template-columns: minmax(13rem, 18rem) minmax(0, 1fr); gap: clamp(1.5rem, 4vw, 4rem); max-width: 1320px; margin: 0 auto; padding: 2rem clamp(1rem, 4vw, 4rem) 5rem; }
    nav { position: sticky; top: 1rem; align-self: start; }
    nav h2 { font-size: .78rem; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); }
    nav a { display: block; color: var(--ink); text-decoration: none; padding: .55rem 0; border-bottom: 1px solid var(--line); }
    nav a:hover { color: var(--accent); }
    main { min-width: 0; }
    .section-card, .panel {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: clamp(1.1rem, 3vw, 2rem);
      margin-bottom: 1.25rem;
    }
    .section-card h2, .panel h2 { font-family: Georgia, "Times New Roman", serif; font-size: clamp(1.7rem, 4vw, 2.7rem); line-height: 1.08; margin: 0 0 1rem; }
    .split { display: grid; grid-template-columns: minmax(0, .9fr) minmax(0, 1.1fr); gap: 1rem; }
    .source, .interpretation { border-radius: 10px; padding: 1rem; }
    .source { background: var(--source); border: 1px solid var(--line); }
    .interpretation { border: 1px solid var(--line); }
    .label { display: block; font-size: .74rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin-bottom: .55rem; }
    blockquote { margin: .6rem 0 0; font-family: Georgia, "Times New Roman", serif; font-size: 1.04rem; }
    .source-meta { font-size: .82rem; color: var(--muted); }
    .why { margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--line); }
    .actions { display: flex; flex-wrap: wrap; gap: .65rem; margin-top: 1rem; }
    .button { border: 1px solid var(--ink); color: var(--ink); background: transparent; border-radius: 999px; padding: .55rem 1rem; cursor: pointer; font-weight: 700; }
    .button:hover, .button[aria-expanded="true"] { background: var(--ink); color: var(--surface); }
    .button-accent { background: var(--accent); border-color: var(--accent); color: white; }
    .details { margin-top: 1rem; background: var(--accent-soft); border-radius: 10px; padding: 1rem; }
    .details[hidden] { display: none; }
    .columns { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }
    .list-box { border-top: 1px solid var(--line); padding-top: .8rem; }
    .list-box h3 { font-size: .85rem; text-transform: uppercase; letter-spacing: .06em; }
    ul { padding-left: 1.2rem; }
    .relation { display: grid; grid-template-columns: 1fr auto 1fr; gap: .8rem; align-items: center; padding: .8rem 0; border-bottom: 1px solid var(--line); }
    .relation-arrow { color: var(--accent); font-weight: 800; text-align: center; }
    .scenario { border-top: 1px solid var(--line); padding: 1.25rem 0; }
    .choice-row { display: flex; flex-wrap: wrap; gap: .55rem; }
    .outcome, .quiz-result { min-height: 3rem; margin-top: .8rem; padding: .85rem; border-radius: 8px; background: var(--source); }
    .range-line { display: grid; grid-template-columns: 1fr auto; gap: 1rem; align-items: center; }
    input[type="range"] { width: 100%; accent-color: var(--accent); min-height: 44px; }
    fieldset { border: 0; padding: 1rem 0; margin: 0; border-top: 1px solid var(--line); }
    legend { font-weight: 800; padding: 1rem 0 .5rem; }
    .option { display: flex; align-items: flex-start; gap: .65rem; padding: .55rem 0; }
    .option input { margin-top: .25rem; }
    .feedback { margin-top: .7rem; padding: .8rem; border-radius: 8px; }
    .feedback.correct { color: var(--success); background: #e8f5eb; }
    .feedback.incorrect { color: var(--danger); background: #fff0ed; }
    footer { color: var(--muted); max-width: 1320px; margin: 0 auto; padding: 0 clamp(1rem, 4vw, 4rem) 3rem; font-size: .85rem; }
    .empty { color: var(--muted); font-style: italic; }
    @media (max-width: 820px) {
      .layout { grid-template-columns: 1fr; }
      nav { position: static; }
      .split, .columns { grid-template-columns: 1fr; }
      .relation { grid-template-columns: 1fr; }
      .relation-arrow { text-align: left; }
    }
    @media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
    @media print {
      body { background: white; }
      nav, .actions, .quiz-submit { display: none; }
      .layout { display: block; padding: 0; }
      .section-card, .panel { box-shadow: none; break-inside: avoid; }
      .details[hidden] { display: block; }
    }
  </style>
</head>
<body>
  <header class="hero">
    <div class="eyebrow">IT Polako · Mapa razumevanja</div>
    <h1 id="page-title">Mapa razumevanja</h1>
    <p class="goal" id="page-goal"></p>
    <div class="meta-row"><span class="pill" id="artifact-type"></span><span class="pill">Lokalni, samostalni HTML</span></div>
    <div class="disclaimer" id="disclaimer" hidden></div>
  </header>
  <div class="layout">
    <nav aria-label="Sadržaj"><h2>Sadržaj</h2><div id="toc"></div></nav>
    <main id="content"></main>
  </div>
  <footer>Napravio skill „Pojasni mi“. Izvor i tumačenje su namerno odvojeni.</footer>
  <script type="application/json" id="map-data">__MAP_DATA__</script>
  <script>
    (() => {
      'use strict';
      const data = JSON.parse(document.getElementById('map-data').textContent);
      const content = document.getElementById('content');
      const toc = document.getElementById('toc');
      const typeNames = {contract:'Ugovor', spreadsheet:'Tabela', code:'Kod', document:'Dokument', diagram:'Dijagram', url:'URL', other:'Artefakt'};
      const el = (tag, className, text) => {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined && text !== null) node.textContent = String(text);
        return node;
      };
      const list = (items) => {
        const ul = el('ul');
        items.forEach(item => ul.append(el('li', '', item)));
        return ul;
      };
      const addNav = (id, label) => {
        const link = el('a', '', label);
        link.href = '#' + id;
        toc.append(link);
      };
      const panel = (id, title) => {
        const node = el('section', 'panel');
        node.id = id;
        node.append(el('h2', '', title));
        content.append(node);
        addNav(id, title);
        return node;
      };
      const safeStore = (key, value) => {
        try { localStorage.setItem(key, value); } catch (_) { /* file privacy mode */ }
      };
      const safeLoad = (key) => {
        try { return localStorage.getItem(key); } catch (_) { return null; }
      };

      document.getElementById('page-title').textContent = data.meta.title;
      document.title = data.meta.title + ' · Mapa razumevanja';
      document.getElementById('page-goal').textContent = data.meta.goal;
      document.getElementById('artifact-type').textContent = typeNames[data.meta.artifact_type] || 'Artefakt';
      if (data.meta.disclaimer) {
        const disclaimer = document.getElementById('disclaimer');
        disclaimer.textContent = data.meta.disclaimer;
        disclaimer.hidden = false;
      }

      data.sections.forEach((section, index) => {
        const card = el('article', 'section-card');
        card.id = section.id;
        card.append(el('div', 'eyebrow', String(index + 1).padStart(2, '0')));
        card.append(el('h2', '', section.title));
        addNav(section.id, section.title);

        const split = el('div', 'split');
        const source = el('div', 'source');
        source.tabIndex = -1;
        source.append(el('span', 'label', 'Izvor'));
        section.source_refs.forEach(ref => {
          const meta = [ref.label, ref.location].filter(Boolean).join(' · ');
          source.append(el('div', 'source-meta', meta));
          source.append(el('blockquote', '', ref.quote));
        });
        const interpretation = el('div', 'interpretation');
        interpretation.append(el('span', 'label', 'Tumačenje'));
        interpretation.append(el('p', '', section.summary));
        const why = el('div', 'why');
        why.append(el('span', 'label', 'Zašto je važno'));
        why.append(el('p', '', section.why_it_matters));
        interpretation.append(why);
        split.append(source, interpretation);
        card.append(split);

        const actions = el('div', 'actions');
        const detailButton = el('button', 'button', 'Idi u detalje');
        detailButton.type = 'button';
        detailButton.setAttribute('aria-expanded', 'false');
        const sourceButton = el('button', 'button', 'Vrati me na izvor');
        sourceButton.type = 'button';
        actions.append(detailButton, sourceButton);
        card.append(actions);

        const details = el('div', 'details');
        details.hidden = true;
        details.id = section.id + '-details';
        detailButton.setAttribute('aria-controls', details.id);
        const columns = el('div', 'columns');
        [['Detalji', section.details || []], ['Posledice', section.consequences || []], ['Neizvesnosti', section.uncertainties || []]].forEach(([heading, items]) => {
          if (!items.length) return;
          const box = el('div', 'list-box');
          box.append(el('h3', '', heading), list(items));
          columns.append(box);
        });
        if (!columns.children.length) columns.append(el('p', 'empty', 'Nema dodatnih tvrdnji vezanih za izvor.'));
        details.append(columns);
        card.append(details);

        const storageKey = 'pojasni-mi:' + data.meta.title + ':' + section.id;
        if (safeLoad(storageKey) === 'open') {
          details.hidden = false;
          detailButton.setAttribute('aria-expanded', 'true');
        }
        detailButton.addEventListener('click', () => {
          details.hidden = !details.hidden;
          const open = !details.hidden;
          detailButton.setAttribute('aria-expanded', String(open));
          safeStore(storageKey, open ? 'open' : 'closed');
        });
        sourceButton.addEventListener('click', () => source.focus());
        content.append(card);
      });

      if (data.relationships && data.relationships.length) {
        const relations = panel('odnosi', 'Kako su delovi povezani');
        const names = Object.fromEntries(data.sections.map(item => [item.id, item.title]));
        data.relationships.forEach(item => {
          const row = el('div', 'relation');
          row.append(
            el('strong', '', names[item.from]),
            el('div', 'relation-arrow', '→ ' + item.label + ' · Izvor: ' + item.source_refs.join(', ')),
            el('strong', '', names[item.to])
          );
          relations.append(row);
        });
      }

      if (data.what_if && data.what_if.length) {
        const whatIfPanel = panel('what-if', 'Pokaži posledice');
        data.what_if.forEach(scenario => {
          const box = el('div', 'scenario');
          box.append(el('h3', '', scenario.title), el('p', '', scenario.prompt));
          const outcome = el('div', 'outcome', 'Izaberi scenario.');
          outcome.setAttribute('aria-live', 'polite');
          if (scenario.kind === 'choice') {
            const row = el('div', 'choice-row');
            scenario.choices.forEach(choice => {
              const button = el('button', 'button', choice.label);
              button.type = 'button';
              button.addEventListener('click', () => {
                outcome.textContent = choice.outcome + ' · Izvor: ' + choice.source_refs.join(', ');
              });
              row.append(button);
            });
            box.append(row, outcome);
          } else {
            const line = el('div', 'range-line');
            const input = document.createElement('input');
            input.type = 'range';
            input.min = String(scenario.min);
            input.max = String(scenario.max);
            input.step = String(scenario.step);
            input.value = String(scenario.base_value);
            input.setAttribute('aria-label', scenario.prompt);
            const value = el('strong');
            line.append(input, value);
            const update = () => {
              const number = Number(input.value);
              const result = number * scenario.factor + scenario.offset;
              value.textContent = number.toLocaleString('sr-RS') + ' ' + (scenario.unit || '');
              outcome.textContent = result.toLocaleString('sr-RS', {maximumFractionDigits: scenario.precision ?? 2}) + ' ' + (scenario.result_unit || '') + ' · Izvor: ' + scenario.source_refs.join(', ');
            };
            input.addEventListener('input', update);
            update();
            box.append(line, outcome);
          }
          whatIfPanel.append(box);
        });
      }

      if (data.quiz && data.quiz.length) {
        const quizPanel = panel('proveri-me', 'Proveri me');
        quizPanel.append(el('p', '', 'Pitanja proveravaju primenu, ne puko pamćenje.'));
        const questions = [];
        data.quiz.forEach((question, questionIndex) => {
          const fieldset = document.createElement('fieldset');
          fieldset.append(el('legend', '', (questionIndex + 1) + '. ' + question.question));
          question.options.forEach((option, optionIndex) => {
            const label = el('label', 'option');
            const input = document.createElement('input');
            input.type = 'radio';
            input.name = 'question-' + questionIndex;
            input.value = String(optionIndex);
            label.append(input, el('span', '', option));
            fieldset.append(label);
          });
          const feedback = el('div', 'feedback');
          feedback.hidden = true;
          fieldset.append(feedback);
          quizPanel.append(fieldset);
          questions.push({question, fieldset, feedback});
        });
        const submit = el('button', 'button button-accent quiz-submit', 'Proveri odgovore');
        submit.type = 'button';
        const result = el('div', 'quiz-result');
        result.setAttribute('aria-live', 'polite');
        submit.addEventListener('click', () => {
          let score = 0;
          questions.forEach(({question, fieldset, feedback}) => {
            const selected = fieldset.querySelector('input:checked');
            const correct = selected && Number(selected.value) === question.correct_index;
            if (correct) score += 1;
            feedback.hidden = false;
            feedback.className = 'feedback ' + (correct ? 'correct' : 'incorrect');
            feedback.textContent = (correct ? 'Tačno. ' : 'Nije tačno. ') + question.explanation + ' · Izvor: ' + question.source_refs.join(', ');
          });
          result.textContent = 'Rezultat: ' + score + '/' + questions.length + '. Vrati se na označene izvore, pa pokušaj ponovo.';
          safeStore('pojasni-mi:' + data.meta.title + ':quiz-score', String(score));
        });
        quizPanel.append(submit, result);
      }

      if (data.open_questions && data.open_questions.length) {
        const open = panel('otvorena-pitanja', 'Šta još nije razrešeno');
        open.append(list(data.open_questions));
      }
    })();
  </script>
</body>
</html>
'''


def render(data: dict[str, Any]) -> str:
    return HTML_TEMPLATE.replace("__MAP_DATA__", json_for_html(data))


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    temporary.replace(path)


def extract(html_path: Path, output_path: Path) -> None:
    html = html_path.read_text(encoding="utf-8")
    match = DATA_PATTERN.search(html)
    if match is None:
        raise ValueError("HTML ne sadrži map-data blok")
    data = validate_payload(json.loads(match.group(1)))
    atomic_write(output_path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Ulazni JSON ili postojeći HTML uz --extract")
    parser.add_argument("output", type=Path, help="Izlazni HTML ili JSON uz --extract")
    parser.add_argument("--extract", action="store_true", help="Izvuci ugrađeni JSON iz postojeće mape")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.extract:
            extract(args.source, args.output)
        else:
            data = validate_payload(json.loads(args.source.read_text(encoding="utf-8")))
            atomic_write(args.output, render(data))
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Greška: {error}", file=sys.stderr)
        return 2
    print(f"Gotovo: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
