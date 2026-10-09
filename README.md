# IT Polako Skills

Tri Agent Skilla na srpskom, latinicom i ekavicom:

- **Iskristališi ideju** pretvara nedorečenu ili već razrađenu ideju u proverljiv Radni nacrt i sledeći test.
- **Pojasni mi** pretvara konkretan izvor u samostalnu interaktivnu HTML Mapu razumevanja.
- **IT Polako montaža** montira IT Polako klip od originalnog 4K HLG snimka do proverenog završnog fajla, u izgledu serijala.

Skill nije poseban program koji pokrećete u terminalu. Instalirate ga u Claude Code, Codex ili drugi podržani agent, a zatim ga pozovete u razgovoru.

## Instalacija

Izaberite **jedan** način instalacije po agentu. Za Claude Code koristite plugin **ili** `skills` CLI, ne oba. Istovremeno možete koristiti Claude plugin za Claude Code i `skills` CLI za Codex.

### Claude Code plugin

U Claude Code-u pokrenite:

```text
/plugin marketplace add rskendzic/it-polako-skills
/plugin install it-polako-skills@it-polako
```

Posle instalacije pokrenite `/reload-plugins` ako Claude Code to zatraži.

### Codex i drugi Agent Skills klijenti

Interaktivna instalacija:

```bash
npx --yes skills@1.5.26 add rskendzic/it-polako-skills
```

CLI zatim nudi izbor skilla, agenta i project/global instalacije.

Svi skillovi globalno za Codex, bez dodatnih pitanja:

```bash
npx --yes skills@1.5.26 add rskendzic/it-polako-skills \
  --skill '*' \
  --agent codex \
  --global \
  --yes
```

Samo jedan skill:

```bash
npx --yes skills@1.5.26 add rskendzic/it-polako-skills \
  --skill pojasni-mi \
  --agent codex \
  --global \
  --yes
```

Za Claude Code kroz otvoreni Agent Skills format umesto plugin-a zamenite `codex` sa `claude-code`.

### Lokalni razvoj Claude plugin-a

```bash
git clone https://github.com/rskendzic/it-polako-skills.git
cd it-polako-skills
claude --plugin-dir .
```

## Kako se koristi

### Claude Code

```text
/it-polako-skills:pojasni-mi ugovor.pdf

Moram da razumem obaveze, rokove, uslove raskida i šta treba da proverim pre potpisivanja.
```

```text
/it-polako-skills:iskristalisi-ideju

Želim servis koji pomaže malim firmama da prate ugovorne obaveze, ali još ne znam ko je prvi korisnik niti šta je najmanji proizvod.
```

```text
/it-polako-skills:it-polako-montaza

Montiraj klip iz ovog foldera. Original je u assets/source/, beleške u production-notes.md, reference u assets/style-reference/, fontovi u assets/fonts/.
```

### Codex

```text
$pojasni-mi

Pojasni mi ugovor.pdf. Moram da odlučim da li smem da ga potpišem i koje tačke zahtevaju stručnu proveru.
```

```text
$iskristalisi-ideju

Želim servis za praćenje ugovornih obaveza malih firmi.
```

```text
$it-polako-montaza

Montiraj klip iz ovog foldera i prijavi šta nije provereno.
```

Codex može automatski da izabere `iskristalisi-ideju`. `pojasni-mi` i `it-polako-montaza` zahtevaju eksplicitan poziv, jer čitaju konkretan izvor i prave fajl.

## Šta dobijate

### Iskristališi ideju

Agent vodi razgovor jednim materijalnim pitanjem odjednom i održava **Radni nacrt** sa:

- ishodom, problemom i korisnikom;
- činjenicama i pretpostavkama;
- odlukama, odbačenim opcijama i kontradikcijama;
- granicama, rizicima i otvorenim pitanjima;
- najjeftinijim testom koji može da obori ključnu pretpostavku.

Ako kažete da je dosta, agent odmah vraća trenutno stanje i označava šta je ostalo otvoreno.

### Pojasni mi

Agent pravi:

```text
mapa-razumevanja.html
```

Fajl se podrazumevano čuva u trenutnom radnom direktorijumu, odnosno u folderu koji ste dali Cowork-u. Agent mora da prijavi tačnu putanju. HTML:

- radi lokalno, bez servera i interneta;
- odvaja izvor od tumačenja;
- vezuje tvrdnje za stranu, odeljak, ćeliju, fajl ili drugi locirajući podatak;
- sadrži `Idi u detalje`, bezbedan what-if kada je primenljiv i `Proveri me`;
- ne koristi udaljene biblioteke ni analitiku.

Renderer koristi Python standardnu biblioteku, ali ga pokreće agent, ne korisnik. Ako izvršavanje koda nije dostupno, agent mora da prijavi blokadu umesto da napravi nevalidiran HTML.

Claude Artifact je opcioni kanal isporuke. Objavljivanje se radi samo uz eksplicitnu saglasnost, jer se sadržaj šalje na Anthropic servere. Lokalni HTML je osnovni rezultat.

### IT Polako montaža

Agent pravi završni klip u izlaznom folderu projekta, u istoj rezoluciji, fps-u i HDR nameri kao original, osim ako odobrite drugačije. Usput:

- pravi jedan transkript po rečima i ispravlja pomak audio toka;
- otkriva ponovljene početke rečenica koje transkript sakrije;
- meri naslov i titlove na referentnim kadrovima pre rendera;
- duže umetke stavlja u podeljen ekran, sa govornikom ispod;
- mapira grafiku u HLG i pravi SDR pregled kroz LUT;
- proverava original, frejmove, spojeve, tokove i glasnoću, pa prijavljuje šta nije provereno.

Potrebni su `ffmpeg` sa `libx265` i `zimg`, Python 3 sa Pillow-om i lokalni model za prepoznavanje govora. Pomoćnik `scripts/hlg_boje.py` koristi samo standardnu biblioteku.

## Probajte primer bez agenta

Repo sadrži potpuno sintetički ugovor i očekivani HTML:

- [ulazni JSON](examples/pojasni-mi/sinteticki-ugovor.json)
- [generisana Mapa razumevanja](examples/pojasni-mi/mapa-razumevanja.html)

Ponovno generisanje primera:

```bash
git clone https://github.com/rskendzic/it-polako-skills.git
cd it-polako-skills
python3 skills/pojasni-mi/scripts/render_map.py \
  examples/pojasni-mi/sinteticki-ugovor.json \
  mapa-razumevanja.html
```

Otvorite `mapa-razumevanja.html` dvoklikom ili direktno iz pregledača.

## Skillovi

### Iskristališi ideju

Koristi se za proizvod, funkciju, sadržaj, proces ili eksperiment. Ne izmišlja persone, tržište ili brojke i ne proglašava ideju validiranom samo zato što je razjašnjena.

### Pojasni mi

Koristi se samo uz konkretan ugovor, tabelu, CSV/XLSX, kod, repozitorijum, PDF/Word dokument, URL, sliku, šemu ili dijagram i jasan cilj razumevanja ili odluke.

`Idi u detalje` i `Proveri me` su režimi unutar `Pojasni mi`, ne posebni skillovi.

### IT Polako montaža

Koristi se samo uz originalni snimak, produkcione beleške ili scenario, vizuelne reference i fontove serijala. Ne piše scenario i ne objavljuje klip. Ako projekat ima sopstveni postupak montaže, on ima prednost.

## Arhitektura

```text
it-polako-skills/
├── .claude-plugin/
│   ├── marketplace.json             # Claude Code distribucija
│   └── plugin.json                  # tanak Claude Code omotač
├── skills/
│   ├── iskristalisi-ideju/
│   │   ├── SKILL.md                 # kanonsko ponašanje
│   │   ├── agents/openai.yaml       # Codex/ChatGPT prikaz
│   │   └── references/
│   ├── pojasni-mi/
│   │   ├── SKILL.md                 # kanonsko ponašanje
│   │   ├── agents/openai.yaml       # Codex/ChatGPT prikaz
│   │   ├── references/
│   │   └── scripts/render_map.py
│   └── it-polako-montaza/
│       ├── SKILL.md                 # kanonsko ponašanje
│       ├── agents/openai.yaml       # Codex/ChatGPT prikaz
│       ├── references/              # izgled, transkript i rez, HLG, ograničeno okruženje
│       └── scripts/hlg_boje.py
├── examples/                        # samo sintetički primeri
├── evals/                           # obavezna i zabranjena ponašanja
└── tests/
```

Kanonska pravila su provider-neutralna. Claude plugin i `agents/openai.yaml` su samo distribucioni adapteri i metapodaci.

## Razvoj i provera

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_repo.py
uvx --from skills-ref==0.1.1 agentskills validate skills/iskristalisi-ideju
uvx --from skills-ref==0.1.1 agentskills validate skills/pojasni-mi
uvx --from skills-ref==0.1.1 agentskills validate skills/it-polako-montaza
```

Claude marketplace i plugin možete proveriti komandom:

```bash
claude plugin validate .
```

GitHub Actions šablon je u `ci/github-actions.yml`. Da bi bio aktivan, kopirajte ga u `.github/workflows/ci.yml`. Credential kojim šaljete tu promenu mora imati GitHub `workflow` dozvolu.

Primeri i evalovi moraju ostati sintetički. Ne dodajte privatne ugovore, poslovne podatke, kod ili slike.

## Pozicioniranje

Projekat ne tvrdi da je prvi interaktivni explainer ili prvi skill za razjašnjavanje ideja. Vrednost je srpski podrazumevani jezik, prenosiv Agent Skills format, sledljivost prema stvarnom izvoru i provera praktičnog razumevanja.

## Licenca

MIT. Pogledajte [LICENSE](LICENSE).
