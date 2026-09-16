# IT Polako Skills

Agent Skills na srpskom, latinicom i ekavicom. Jedan repozitorijum, dva javna skilla, ista kanonska pravila za Claude Code i Codex.

## Skillovi

### Iskristališi ideju

Istrajno pretvara nedorečenu ideju u proverljiv **Radni nacrt**: činjenice, pretpostavke, odluke, kontradikcije, rizici, otvorena pitanja i najjeftiniji sledeći test.

### Pojasni mi

Od konkretnog ugovora, tabele, koda, dokumenta, URL-a ili dijagrama pravi samostalnu interaktivnu HTML **Mapu razumevanja**. Tvrdnje su vezane za izvor, a provera meri praktičnu primenu.

`Idi u detalje` i `Proveri me` su režimi unutar `Pojasni mi`, ne posebni skillovi.

## Šta Pojasni mi pravi

Podrazumevani rezultat je jedan lokalni `mapa-razumevanja.html`:

- radi bez interneta;
- nema udaljene biblioteke ni analitiku;
- odvaja izvor od tumačenja;
- prikazuje odnose i posledice;
- podržava bezbedan what-if;
- ima praktičan kviz `Proveri me`;
- može opciono da se objavi kao Claude Artifact, ali samo uz eksplicitnu saglasnost.

Primer je napravljen od potpuno sintetičkog ugovora:

```bash
python3 skills/pojasni-mi/scripts/render_map.py \
  examples/pojasni-mi/sinteticki-ugovor.json \
  examples/pojasni-mi/mapa-razumevanja.html
```

## Arhitektura

```text
it-polako-skills/
├── .claude-plugin/plugin.json       # tanak Claude Code omotač
├── skills/
│   ├── iskristalisi-ideju/
│   │   ├── SKILL.md                 # kanonsko ponašanje
│   │   ├── agents/openai.yaml       # Codex/ChatGPT prikaz
│   │   └── references/
│   └── pojasni-mi/
│       ├── SKILL.md                 # kanonsko ponašanje
│       ├── agents/openai.yaml       # Codex/ChatGPT prikaz
│       ├── references/
│       └── scripts/render_map.py
├── examples/                        # sintetički primeri
├── evals/                           # obavezna i zabranjena ponašanja
└── tests/
```

Jezgro nije vezano za jedan model. `.claude-plugin/plugin.json` distribuira iste skillove u Claude Code-u, a `agents/openai.yaml` dodaje OpenAI prikaz i podrazumevani prompt. Nema kopirane druge implementacije.

## Claude Code

Za lokalni razvoj učitaj ceo repozitorijum kao plugin:

```bash
claude --plugin-dir /putanja/do/it-polako-skills
```

Claude Code otkriva oba direktorijuma u `skills/`. Lokalni HTML je uvek osnovni izlaz. Ako je Artifact alat dostupan, objavljivanje je poseban, opcioni korak.

## Codex

Instaliraj svaki skill iz GitHub repozitorijuma pomoću `$skill-installer`, ili kopiraj/simlinkuj direktorijume u korisnički katalog:

```bash
mkdir -p ~/.agents/skills
ln -s /putanja/do/it-polako-skills/skills/iskristalisi-ideju ~/.agents/skills/iskristalisi-ideju
ln -s /putanja/do/it-polako-skills/skills/pojasni-mi ~/.agents/skills/pojasni-mi
```

Codex koristi isti `SKILL.md`. Claude-specifični Artifact korak se preskače, dok lokalni HTML ostaje isti.

## Provera

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_repo.py
```

Repo sadrži spreman GitHub Actions šablon u `ci/github-actions.yml`. Za aktivaciju ga kopirajte u `.github/workflows/ci.yml`; credential koji obavlja push mora imati dozvolu za workflow fajlove.

Repo ima sintetičke eval slučajeve. Ne stavljajte privatne ugovore, podatke, kod ili slike u `examples/` i `evals/`.

## Pozicioniranje

Ovaj projekat ne tvrdi da je prvi interaktivni explainer ili prvi skill za razjašnjavanje ideja. Postoje srodni alati. Vrednost ovde je srpski podrazumevani jezik, prenosiv Agent Skills format, stroga sledljivost prema stvarnom izvoru i provera operativnog razumevanja.

## Licenca

MIT. Pogledajte [LICENSE](LICENSE).
