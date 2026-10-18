# Šablon izveštaja i mesečne note

**Izveštaj** ide korisniku u razgovor i vodi ka odluci — uvek. **Zapis** (nota ili red u tabeli) postoji samo ako `izlaz.tip` nije `chat` i služi proveri za godinu dana. Nisu isti dokument.

---

## Izveštaj u razgovoru

Redosled je namerno ovakav: prvo ono što zahteva radnju, pa objašnjenje. Ko pročita samo prvi ekran mora da zna šta mu treba.

```markdown
# <Mesec godina>

<Jedna rečenica: koliko izvora je primljeno i da li kontrola prolazi.
Kod rada bez nadzora: „NACRT — čeka odgovore na pitanja".>

## Hitno

<Račun čije stanje neće pokriti naplate sledećeg meseca, neispunjen
uslov održavanja, dospeće kartice. Prazno → izostavi sekciju.>

## Config

<Upozorenja iz proveri_config.py i izmene koje predlažu izvodi:
nov trgovac, zatvoren kredit, nepoznat račun. Prazno → izostavi.>

## Rezultat

| | <valuta> |
|---|---:|
| Stanje na početku | |
| Stanje na kraju | |
| **Rezultat** | |
| Bazna linija | |
| Odstupanje | |

## Normalizacija

<Obuhvat (koji računi), pa vodopad iz obracun_viska.py, svaki korak označen
kao izvedeno. Zatim kontrola drugim putem: redovni prihodi − redovni
troškovi + obaveze koje prestaju. Dva puta moraju dati isti broj.
Ako je neki izvod prošao samo bez kolone stanja, ili kartica stiže bez
transakcija, napiši to ovde.>

## Odstupanja preko <prag>

| Kategorija | Mesec | Bazna linija | Razlika |

<Samo preko praga. Uz svaku kategoriju koja je nepotpuna reci zašto —
„nisko zato što izvor X nije stigao" nije ušteda.>

## Gotovina

| | |
|---|---:|
| Preneto iz prošlog meseca | |
| Podignuto | |
| **Raspoloživo** | |
| <kategorije iz naracije> | |
| **Kategorisano** | |
| **Potrošeno bez zapisa** | |

<Razdvoj jednokratno od ponavljajućeg pre bilo kakvog zaključka.>

## Napredak ka cilju

<Ušteđeno, ostatak, meseci koji su ostali, potrebna mesečna stopa.
Ako potrebna stopa prelazi realno raspoloživo, reci to i ponudi
alternative sa cenom svake.>

## Novo ovog meseca

<Nove pretplate, poskupljenja, kategorije koje se nisu pojavljivale.>

## Nedostaje

<Izvori koji nisu stigli i šta korisnik treba da pošalje ručno.>

## Pitanja

<Numerisano, konkretno, sa iznosom i datumom. „Šta je transakcija
od 48.000 dana 12.09?" se odgovara. „Objasni potrošnju" se ne odgovara.>

## Predlog izmena u zapisu — čekam OK

<Po fajlu i sekciji, ili po redu i koloni za csv. Šta se dodaje, šta se
zatvara, šta ostaje u zagradi. Kad je izlaz.tip chat, ove sekcije nema.>
```

### Šta izveštaj ne radi

Ne zaokružuje da bi bilo lepše. Ne spaja nepotpunu kategoriju sa potpunom. Ne naziva uštedom ono što je nedostajući izvor. Ne preporučuje iznos ulaganja.

Ako nalaz obara cilj koji je korisnik postavio, to ide u izveštaj. Prećutano odstupanje se pojavi mesec pre roka, kad je prepozno.

---

## Nota u zapisu (`markdown` i `obsidian`)

Putanja iz `izlaz.mesecne_note`, relativno na `izlaz.putanja`.

```markdown
# Finansije — <mesec godina>

Period: YYYY-MM · Status: čeka pregled · Ažurirano: YYYY-MM-DD
Izvori očekivani: … · primljeni: …
Tri vrste podataka su razdvojene: **izvod**, **korisnik**, **izvedeno**.

## Kontrola kompletnosti
## Prihod
## <Račun po račun>
## Kategorije
## Gotovina
## Neusaglašeno
## Otvoreno za proveru
```

**Samo za `obsidian`** dodaj na vrh frontmatter, a ispod naslova vezu na pregled:

```markdown
---
title: Finansije — <mesec godina>
type: <tip iz izlaz.pravila, ako postoji>
period: YYYY-MM
status: needs-review
sources_expected: [...]
sources_received: [...]
updated: YYYY-MM-DD
tags: [finansije, izvod, mesecni-pregled]
---

Deo [[<izlaz.glavni_fajl bez .md>]].
```

Kod `markdown` tipa nema wiki linkova; ako postoji `glavni_fajl`, veza je običan relativni link.

### Pravila note

**Poreklo uz svaki broj.** Kolona ili oznaka: izvod, korisnik, izvedeno. Bez toga se za pola godine ne zna šta je podatak a šta procena, i procena počne da se citira kao podatak.

**Agregati, ne transakcije.** Lista trgovaca u zapisu stari i ne čita se. Agregat po kategoriji se poredi kroz mesece. Ako pravila zapisa (`izlaz.pravila`) zabranjuju imena trgovaca i brojeve računa, ta pravila imaju prednost.

**Protivrečnosti se ne razrešavaju same.** Kad korisnikova naracija ne odgovara izvodu, obe verzije ostaju u `## Neusaglašeno`, sa datumom, i sa stavkom da korisnik presudi. Model ne bira koja je verzija tačna.

**Stara vrednost ide u zagradu.** „32.000 (ranije 45.000)". Brisanje sakriva da se znanje menjalo, a upravo to je ono što mesečni zapis treba da pokaže.

**Ne prepisuj postojeću notu.** Mesečna nota može sadržati korisnikovu živu naraciju upisanu u toku meseca — podatke koje izvod ne zna. Dopuni je.

---

## Red u tabeli (`csv`)

Jedan red po mesecu u `izlaz.fajl`. Ova tabela je za poređenje kroz mesece, ne za objašnjenje — naracija, neusaglašeno i pitanja ostaju u izveštaju.

Kolone, ovim redom:

```
mesec, izvori_primljeni, izvori_ocekivani, kontrola,
obuhvat, promena_obuhvata, prenosi_van_obuhvata, visak,
jednokratni_prihodi, jednokratni_troskovi, prestale_obaveze,
ponovljiv_visak, rezerva_mesecno, realno_raspolozivo,
kes_podignuto, kes_bez_zapisa, kes_preneto,
kat_<ime>…  (po jedna kolona za svaku kategoriju iz config-a, abecedno),
transferi, nekategorisano, napomena
```

- `mesec` je `YYYY-MM`; `kontrola` je `prosla`, `nije_prosla` ili `nepotpuna` — red se upisuje samo kad je `prosla`.
- `obuhvat` su poslednje 4 cifre računa razdvojene sa `;`. Kad se obuhvat promeni, redovi pre i posle nisu direktno uporedivi — napomeni to u `napomena`.
- Brojevi bez separatora hiljada, sa tačkom kao decimalnim (`12345.67`), da ih svaki program čita isto bez obzira na lokalizaciju. Valuta je `lokalizacija.valuta_osnovna`.
- Kodiranje UTF-8, separator zapeta, tekst sa zapetom u navodnicima.
- **Zaštita od formula.** Excel i Sheets izvršavaju ćeliju koja počinje sa `=`, `+`, `-`, `@`, tabom ili znakom za novi red. Tekstualne kolone (`mesec`, `kontrola`, `obuhvat`, `napomena` i svaka druga koja nije broj) koje počinju nekim od tih znakova upiši sa apostrofom ispred (`'=SUM(…)`). Numeričke kolone smeju da sadrže samo broj u obliku `-?\d+(\.\d+)?`, ili ostaju prazne; ništa drugo se u njih ne upisuje.
- Pre upisa reda proveri oba pravila za svaku ćeliju. Ćelija koja ih krši ne ide u fajl.
- Prazna ćelija znači „nije poznato". Nula znači nula. Ne mešaj ih.
- Nova kategorija u config-u → predloži novu kolonu na kraju `kat_` grupe; stari redovi u njoj ostaju prazni.
- Postojeći red za isti mesec se ne prepisuje tiho: prikaži staru i novu vrednost svake promenjene ćelije i čekaj odobrenje.
- Ako fajl ne postoji, prvi upis pravi i zaglavlje.
