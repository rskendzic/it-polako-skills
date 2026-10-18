---
name: mesecni-finansijski-presek
description: Zatvori prethodni mesec iz bankovnih izvoda po korisnikovom config-u — prikupi izvode, parsiraj ih, proveri bilans, kategorizuj, normalizuj prema baznoj liniji i predloži upis u lični zapis po izboru (samo izveštaj, markdown folder, CSV tabela ili Obsidian). Koristi kad korisnik traži mesečni finansijski pregled, presek, obračun ili zatvaranje meseca; kad pošalje PDF bankovni izvod i traži analizu; kad pita koliko je potrošio, koliki mu je višak, kolika mu je plata po izvodima, gde ide keš ili da li mu izlazi štednja; kad zakazani zadatak pokrene presek; i kad traži da se presek postavi, podesi ili da se napravi ili proveri config za presek. Koristi i kad se pominje izvod, anuitet, pretplate, revolving kartica, keš naracija ili amortizacioni fond u kontekstu ličnog budžeta. Ne koristi za poslovno knjigovodstvo, poreske prijave ni investicione savete.
license: MIT
metadata:
  author: IT Polako
  version: "0.1.0"
  language: sr-Latn-RS
---

# Mesečni finansijski presek

Zatvaranje prethodnog meseca iz bankovnih izvoda: od izvora do zapisa.

Posao nije „sabrati troškove". Posao je **doći do broja kome se može verovati** i koji se može uporediti sa prošlim mesecom. Zato je polovina ovog skill-a o kontroli i normalizaciji, a ne o kategorizaciji.

Skriptovi su u `scripts/` ovog skilla. Razreši putanju do direktorijuma ovog skilla i pokreći ih dostupnim Python 3 interpreterom, sa apsolutnim putanjama do config-a i izvoda. Ti izvršavaš komande; korisnik ne mora da koristi terminal.

Skill je generički. Sve što je specifično za jednu osobu — banke, računi, trgovci, plata, krediti, ciljevi, gde se vodi zapis — živi u **config-u**, ne ovde.

## Postavka (prvo korišćenje)

Pokreće se kad config ne postoji, kad korisnik kaže „postavi", „podesi" ili „kako da počnem", ili kad je skill pozvan sa argumentom `postavi`. Cilj je da korisnik posle jednog razgovora ima sve što prvi presek traži, i da zna šta mu fali.

1. **Config** — onboarding (dole). Na kraju pokreni `proveri_config.py --potrebe`.
2. **Spremnost** — za svaku potrebu proveri da li okruženje to zaista ima (tabela dole). Pokaži korisniku tabelu spremnosti.
3. **Najkraći put** — reci jednim redom koje je **prvo** sledeće što korisnik treba da uradi, pa ponudi da to uradiš ti, ako možeš (npr. predlog povezivanja mejla). Ne nabrajaj sve odjednom kao domaći zadatak.
4. **Prvi presek** — čim nijedna kritična potreba ne fali, ponudi da odmah zatvoriš prethodni mesec.
5. **Zakazani zadatak** — tek posle prvog uspešnog preseka (korak 10).

Nijedna praznina ne blokira postavku. Config se pravi i kad mejl još nije povezan; presek se ne pokreće dok kritična potreba fali.

### Spremnost

`proveri_config.py <config> --potrebe` kaže šta config traži od okruženja. Potrebe se računaju samo za ispravan config; prvo ispravi greške. Skript ne vidi tvoje alate — ti proveravaš da li potreba postoji:

| Potreba | Kako proveravaš | Ako fali |
|---|---|---|
| `mejl` (kritično) | postoji li alat za pretragu mejla i preuzimanje priloga; probna pretraga po jednom pošiljaocu za poslednjih 40 dana | reci koji nalog i koji pošiljaoci; ponudi povezivanje mejl konektora ako ga okruženje nudi; dotle izvor tretiraj kao `rucno` |
| `folder` (kritično) | da li je folder dostupan (povezan folder, priložen fajl) | zamoli korisnika da poveže folder ili priloži izvode |
| `rucno` (kritično) | ništa — uvek zavisi od korisnika | reci tačno šta i kada da priloži (`uputstvo`); u radu bez nadzora to ide u izveštaj kao „fali" |
| `alat` (kritično) | `which pdftotext` | instaliraj (`poppler-utils`) ako okruženje dopušta; inače stani i reci šta treba |
| `folder_zapisa` (preporuka) | da li je folder iz `izlaz.putanja` dostupan za pisanje | izveštaj ostaje u razgovoru; ponudi `izlaz.tip: chat` ili povezivanje foldera |
| `zakazani_zadatak` (preporuka) | postoji li alat za zakazane zadatke i da li zadatak za presek već postoji | ponudi posle prvog uspešnog preseka |

Tabela za korisnika:

```markdown
| Šta | Stanje | Zašto je važno | Sledeći korak |
|---|---|---|---|
| Mejl za izvode ****1111 | ✗ nije povezan | bez njega se izvodi ne prikupljaju | povezati Gmail (mogu da predložim) |
| Izvod ****5555 | ručno | aplikacija banke ne šalje mejl | do 7. u mesecu priložiti PDF |
| Zapis | ✓ samo izveštaj | — | — |
```

Spremnost proveri i **na početku svakog preseka**, kratko. Kad kritična potreba fali, presek ne kreće; u radu bez nadzora izveštaj je samo tabela spremnosti i spisak onoga što fali.

## Korak 0: config

### Gde ga tražiš, ovim redom

1. U kontekstu — prompt zakazanog zadatka, poruka korisnika, nalepljen YAML
2. Putanja koju korisnik navede
3. `finansije.config.yaml` u folderu koji korisnik koristi za finansije, ako je neki povezan
4. Ništa od toga → **onboarding** (dole)

Ne pretpostavljaj da korisnik ima vault, repo ili ikakav folder. Ko ne vodi zapis drži config u promptu zakazanog zadatka ili ga nalepi u razgovor.

Kad ga nađeš, pokreni:

```bash
python3 scripts/proveri_config.py <config.yaml>
```

Config koji živi u promptu zakazanog zadatka **ne upisuj u fajl** — ni korisniku ni u radni folder. Prosledi ga preko standardnog ulaza; svi skriptovi prihvataju `-` umesto putanje:

```bash
python3 scripts/proveri_config.py - <<'CONFIG'
<config iz prompta>
CONFIG
```

Greške (izlazni kod 1) zaustavljaju presek — prijavi ih i stani. Upozorenja (zastareo kredit, istekao rok cilja, trgovac u dve kategorije) navedi na vrhu izveštaja; ne zaustavljaju rad.

### Onboarding kad config ne postoji

Pročitaj `references/config-sablon.md`. Kreni od `assets/config.minimalni.yaml` i popuni ga kroz razgovor — banke, računi (samo poslednje 4 cifre), odakle stižu izvodi, kako se prepoznaje plata. Pitaj da li uopšte želi trajni zapis; ako ne zna, `izlaz.tip: chat`. Ostalo se dopunjava posle prvog preseka, iz samih izvoda. `assets/config.primer.yaml` je potpun izmišljen primer za referencu.

Config upiši u fajl samo uz odobrenje i samo ako korisnik ima gde da ga drži. Inače mu ga daj kao tekst za prompt zakazanog zadatka.

### Config je hipoteza, izvodi su autoritet

**Proveri svaku tvrdnju iz config-a na izvodima.** Config navodi podračun koji nikad nije postojao, platu koja je bila pre povišice, kredit koji je zatvoren. Kad izvodi pobiju config, prijavi to i predloži konkretnu izmenu config-a — ne prilagođavaj podatke pretpostavci.

## Režimi rada

**Interaktivno** (korisnik je tu): pitaj kad nešto fali, posebno za keš i neobjašnjene transakcije.

**Bez nadzora** (zakazani zadatak, niko ne odgovara): ne čekaj odgovore. Prvo proveri spremnost; ako kritična potreba fali, izveštaj je samo tabela spremnosti. Uradi sve što izvodi omogućavaju, sva pitanja skupi u sekciju `Pitanja`, keš označi kao `čeka naraciju`, a izveštaj kao **nacrt**. Ništa ne upisuj. Ako izvor nedostaje, izveštaj je samo spisak onoga što fali.

## Orkestracija

Ako config ima `orkestracija.podagenti: da` i imaš alat za podagente, podeli posao po modelima iz config-a (`mehanicki`, `analiticki`, `verifikacija`). Postavi model eksplicitno na svakom podagentu. Inače radi sam.

Verifikacija nije formalnost. Podagent koji parsira zna samo svoj fajl; onaj ko verifikuje vidi da li se izvodi međusobno poklapaju — prenos sa računa A mora stajati i kao uplata na računu B, do jedinice valute.

## Koraci

### 1. Prikupi izvode

Za svaki izvor iz `izvori` u config-u:

| `tip` | Kako |
|---|---|
| `mejl` | pretraga po `posiljaoci`, od 1. tekućeg meseca; samo čitanje |
| `folder` | fajlovi u `putanja` koji odgovaraju `obrazac` |
| `rucno` | traži od korisnika da priloži (izvoz iz aplikacije, portal) |
| `mejl_tekst` | mejl bez priloga — iz teksta izvuci polja navedena u `izvuci` |

Izvodi meseca N obično nose podatke za mesec N−1 i ne stižu istog dana. `ocekivano_do` u izvoru kaže do kog dana u mesecu treba čekati.

Kad izvor nedostaje: **prijavi tačno koji i stani.** Ne procenjuj, ne ekstrapoliraj, ne radi presek na tri četvrtine podataka i ne nazivaj to presekom.

Izvodi bez priloga sa linkom na portal: ne loguj se. Izvuci šta tekst nudi, a PDF traži ručno.

### 2. Preuzmi priloge

Prilozi mogu biti URL-safe base64 (`-` i `_` umesto `+` i `/`). Posle svakog fajla proveri `head -c 5` da daje `%PDF` — tiho pokvaren fajl je gori od fajla koji nije preuzet. Detalji u `references/parsiranje-izvoda.md`.

### 3. Parsiraj i kontroliši

`pdftotext -layout` je osnovni alat; `-raw` je rezerva kad je tabela izlomljena.

Cilj kontrole je da potvrdi da je **pročitana svaka transakcija** — ne da je računica banke tačna. Zaglavlje skoro uvek izlazi; to ne govori ništa o tome šta je parsiranje propustilo. Zato se zbirovi iz zaglavlja nikad ne koriste umesto parsiranih, nego se sa njima porede.

**Tri provere, sve obavezne:**

1. **Lanac**: od početnog stanja iz zaglavlja, kroz svaku transakciju (stanje = prethodno ± iznos u istom redu), do završnog stanja iz zaglavlja. Lanac je usidren u zaglavlje na oba kraja, pa se vidi i kad je ispala prva ili poslednja transakcija.
2. **Promet**: parsirane isplate i uplate = isplate i uplate iz zaglavlja.
3. **Zaglavlje**: `početno − isplate + uplate = završno`.

```bash
python3 scripts/kontrola_bilansa.py izvod.txt --config <config.yaml> \
  --pocetno … --zavrsno … --isplate … --uplate …
```

Četiri iznosa prepiši sa zaglavlja izvoda, ne iz parsiranja. Kod kreditne kartice stanje je dug, zadaj ga kao negativan broj.

| Status | Kod | Značenje | Šta radiš |
|---|---|---|---|
| PROSLA | 0 | sve tri provere prošle | nastavi |
| NIJE PROSLA | 1 | bar jedna pala | prijavi fajl, proveru i razliku; stani |
| NEPOTPUNA | 3 | nema zaglavlja, ili kolona stanja nije potvrđena | **nije uspeh**; prijavi razlog; stani |

**Izvod bez kolone stanja** (tipično kartični): skript to ne pretpostavlja sam, jer loše parsiranje i izvod bez salda izgledaju isto. Pogledaj izvod. Tek ako zaista nema saldo po redu, pokreni ponovo sa `--bez-kolone-stanja`. Tada lanca nema, a potpunost potvrđuju promet i zaglavlje — u izveštaju to i napiši.

Izvod koji stiže samo kao tekst mejla, bez transakcija, ne može da prođe kontrolu. Njegovo stanje (dug) koristi se za obračun viška, ali kategorije za taj račun ostaju **nepotpune** dok ne stigne PDF.

Ako kontrola ne prođe, prijavi koji fajl i koliku razliku, i stani. Procenjen broj u finansijskom izveštaju je gori od praznog polja — praznom polju se ne veruje, procenjenom se veruje.

### 4. Kategorizuj

Kategorije i trgovci dolaze iz `kategorije` u config-u. Poklapanje je po delu opisa transakcije, bez obzira na velika i mala slova.

**Ništa ne sme da ispadne.** Zbir svih kategorija + transferi mora biti jednak ukupnim isplatama. Nabroj doslovno svaku transakciju koja nije pala ni u jednu kategoriju — velike jednokratne se najlakše izgube upravo zato što ne pripadaju nijednoj poznatoj grupi. Za svaku ponovljenu nekategorisanu predloži dopunu config-a.

**Transferi nisu rashod.** Prenos između računa iz config-a, kupovina deviza, uplata na sopstvenu kreditnu karticu — premeštanje, ne potrošnja. Prepoznaju se automatski po računima iz config-a i po `transferi.opisi`. Vodi ih odvojeno.

### 5. Razdvoj prihode po kanalima

Prihodi se prepoznaju po `prihodi[].prepoznaj_po`. Stavka sa `tip: refundacija` **nije prihod** — oduzima se od troška koji pokriva.

Ako korisnik ili config kaže koliko je plata, **proveri na izvodima.** Povuci `izvestaj.istorija_meseci` prošlih izvoda i poređaj redovnu uplatu. Grozd meseci sa malom razlikom je plata; mesec koji se izdvaja je bonus, regres ili zaostatak i mora se normalizovati. **Gledaj grozd, ne prosek.**

### 6. Normalizuj pre bilo kakvog zaključka

Višak se ne računa iz jednog računa. Prenos na štednju smanjuje tekući, a nije potrošnja; kupovina karticom ne dira tekući, a jeste potrošnja. Višak se računa nad **obuhvatom** — računima sa `obuhvat: true` u config-u (podrazumevano svi osim štednih):

```
  Σ promena stanja računa u obuhvatu       svaki u svojoj valuti, jednim kursom
+ prenosi na sopstvene račune van obuhvata štednja, investicije: ušteda, ne trošak
− prenosi sa sopstvenih računa van obuhvata povlačenje iz štednje nije prihod
= višak meseca
− jednokratni prihodi                      bonus, regres, refundacija, poklon
+ jednokratni troškovi                     nameštaj, bela tehnika, putovanje
+ obaveze koje prestaju                    poslednja rata kredita
= ponovljiv mesečni višak
− mesečna rezerva (rezerva iz config-a / 12)
= realno raspoloživo
```

Prenosi unutar obuhvata se poništavaju sami. Prenos na račun koji nije u config-u nije transfer nego rashod.

```bash
python3 scripts/obracun_viska.py mesec.json --config <config.yaml>
```

`mesec.json` sastavljaš od izvoda koji su prošli kontrolu: početno i završno stanje svakog računa u obuhvatu, kurs, svi prenosi između sopstvenih računa, jednokratne stavke i kontrola drugim putem. Format je u zaglavlju skripta; primer je `assets/mesec.primer.json`.

**Kontrola drugim putem je obavezna**: `redovni prihodi − redovni troškovi + obaveze koje prestaju` mora dati isti ponovljiv višak. Bez nje skript vraća NEPOTPUNO; ako se ne poklapa, stavka je na pogrešnoj strani. Ni u jednom slučaju ne izvodi zaključke. Detalji u `references/normalizacija.md`.

### 7. Keš

Samo ako config ima `kes`. Keš je jedini deo gde zavisiš od korisnikove naracije.

1. Sa izvoda uzmi **sva podizanja**, pojedinačno, sa datumima
2. Dodaj preneto iz prošlog meseca, ako `kes.ladica: da`
3. Od korisnika uzmi naraciju; dodaj `kes.stalne_linije`
4. **Eksplicitno prijavi razliku** između raspoloživog i objašnjenog

Keš u ladici nije trošak dok ne ode. Neobjašnjen ostatak upiši kao **potrošeno bez zapisa**, sa iznosom — iskrenije od lažne kategorije.

Pre saveta, **razdvoj jednokratno od ponavljajućeg.** Savet „prepolovi keš" je besmislen ako je veći deo bila jednokratna kupovina.

### 8. Izveštaj

Struktura u `assets/sablon-izvestaja.md`, na jeziku iz `lokalizacija.jezik`. Vodi se onim što korisniku treba za odluku:

- **Operativno hitno prvo** — račun čije stanje neće pokriti naplate sledećeg meseca, uslov održavanja računa koji nije ispunjen, dospeće kartice
- **Rezultat** naspram bazne linije, sa vodopadom iz `obracun_viska.py` i navedenim obuhvatom
- **Odstupanja** samo iznad `izvestaj.prag_odstupanja`
- **Keš**: podignuto, kategorisano, bez zapisa, preneto
- **Ciljevi**: ušteđeno (sa izvoda), ostatak, meseci do roka, potrebna stopa naspram realno raspoloživog
- **Novo**: pretplate i poskupljenja — matrica servis × mesec iz istorije
- **Config**: predložene izmene na osnovu izvoda

Svaki broj ima poreklo: **izvod**, **korisnik** ili **izvedeno**.

Ako brojevi obore cilj, reci to i ponudi alternative sa cenom svake.

### 9. Upis

Zavisi od `izlaz.tip`. Podrazumevano je `chat` — korisnik nema nikakav zapis i to je potpuno validan izbor.

| `izlaz.tip` | Šta nastaje | Za koga |
|---|---|---|
| `chat` | samo izveštaj u razgovoru; na zahtev i kao `.md` fajl za preuzimanje | nema zapis, ili tek počinje |
| `markdown` | mesečna nota i pregled u folderu, običan markdown bez wiki linkova | bilo koji editor, Git, Dropbox |
| `csv` | jedan red po mesecu u tabeli | Excel, Numbers, Google Sheets |
| `obsidian` | kao `markdown`, plus frontmatter i `[[linkovi]]` | Obsidian vault |

Format note i kolone tabele su u `assets/sablon-izvestaja.md`.

Za sve osim `chat`:

**Ne upisuj bez izričitog odobrenja.** Predloži izmene po fajlu i sekciji (ili po redu i koloni), pa čekaj. Ovo ne menja ni config ni zakazani zadatak.

Ako config ima `izlaz.pravila`, pročitaj taj fajl pre upisa — njegova pravila imaju prednost nad ovim skill-om za strukturu.

Ako mesec već postoji: **diff, ne prepisivanje.** Postojeća nota može nositi korisnikovu živu naraciju; postojeći red u tabeli se ne menja tiho — prikaži staru i novu vrednost.

### 10. Zakazani zadatak

Posle **prvog uspešnog preseka** u interaktivnom radu, ako zadatak za presek još ne postoji, ponudi jednom da ga napraviš. Napravi ga tek na izričito „da".

- Dan: iz `--potrebe` (`zakazani_zadatak.dan`), vremenska zona iz config-a. Kad izvodi stižu do 27., to je dan posle poslednjeg i presek zatvara prethodni mesec. Kad stižu 28. ili kasnije, zadatak ide 1. u mesecu i zatvara **mesec pre prethodnog** (`pomeraj_meseci: 2`) — to mora pisati u promptu zadatka i u izveštaju.
- Prompt: rečenica o radu bez nadzora, plus putanja do config-a, ili ceo config ako korisnik nema folder. Primer je u `references/config-sablon.md`.
- Reci korisniku šta zakazani rad zahteva: isti pristup mejlu i folderu kao sada, i da ništa neće upisati bez njega — izveštaj je nacrt.

Ako alat za zakazane zadatke ne postoji, daj korisniku gotov prompt i reci gde se zadatak pravi.

## Pravila koja config ne može da promeni

**Pune brojeve računa nikad ne upisuj.** Samo poslednje 4 cifre — u izveštaju, zapisu bilo kog tipa, međurezultatima i config-u.

**Izvori su samo za čitanje.** Ne šalji, ne odgovaraj, ne briši, ne menjaj labele, ne loguj se na portale.

**Ne mešaj kredit za stvar sa troškovima te stvari.** Rata i registracija auta su odvojene stavke sa različitim ritmom.

**Kreditna kartica.** „Ukupan dug" je ono što se uplaćuje do dospeća. „Zbir dospelih rata" je već uračunat u ukupan dug — ne sabiraj ih. Ne izvodi zaključak o revolving kamati bez poređenja uplate sa **prethodnim** stanjem duga.

**Nema investicionih saveta.** Scenariji sa iznosom koji korisnik zada — da. Ukazivanje na sukob rokova ili na dug sa višom kamatom od očekivanog prinosa — da. Preporuka iznosa ulaganja — ne; za to licencirani savetnik.

**Osetljivi podaci.** Apoteka kao kategorija je u redu. Dijagnoza, lek ili stanje ne idu nigde — ni u izveštaj, ni u zapis, ni u memoriju.

## Dodatni fajlovi

| Fajl | Kad |
|---|---|
| `references/config-sablon.md` | onboarding, izmena config-a, značenje polja |
| `assets/config.minimalni.yaml` | početak onboardinga |
| `assets/config.primer.yaml` | potpun izmišljen primer |
| `assets/mesec.primer.json` | ulaz za `obracun_viska.py` |
| `scripts/proveri_config.py` | uvek, u koraku 0; sa `--potrebe` u postavci i proveri spremnosti |
| `README.md` | uputstvo za korisnika — šta je potrebno i kako se počinje |
| `scripts/kontrola_bilansa.py` | uvek, u koraku 3 |
| `scripts/obracun_viska.py` | uvek, u koraku 6 |
| `references/parsiranje-izvoda.md` | izvod se ne parsira čisto, formati brojeva, devizne naknade |
| `references/normalizacija.md` | vodopad, rezerva, plata, projekcija ka cilju |
| `assets/sablon-izvestaja.md` | struktura izveštaja i mesečne note |
