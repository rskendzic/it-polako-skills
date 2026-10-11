# Config

Config je sve što je lično. Skill je sve ostalo. Config se drži kod korisnika i ne ulazi u skill. Gde, zavisi od toga šta korisnik ima:

| Korisnik ima | Config živi |
|---|---|
| ništa, samo razgovor | u promptu zakazanog zadatka, ili ga nalepi kad pokreće presek |
| folder (lokalni, Dropbox, iCloud) | `finansije.config.yaml` u tom folderu |
| repo ili Obsidian vault | `finansije.config.yaml` u korenu |

- `assets/config.minimalni.yaml` — početak
- `assets/config.primer.yaml` — potpun izmišljen primer
- `scripts/proveri_config.py` — provera šeme i zastarelosti

## Polja

Obavezno je samo ono označeno sa **\***. Sve ostalo ima razumnu podrazumevanu vrednost ili isključuje korak koji mu pripada.

### `verzija` \*
Trenutno `1`. Skript odbija nepoznatu verziju umesto da pogađa.

### `lokalizacija`
| Polje | Podrazumevano | Značenje |
|---|---|---|
| `jezik` | srpski | jezik izveštaja |
| `valuta_osnovna` | RSD | valuta u kojoj se sabira |
| `decimalni_separator` | otkriva se iz fajla | `","` za 1.234,56, `"."` za 1,234.56 |
| `vremenska_zona` | — | za „koji je mesec prethodni" kod zakazanog pokretanja |

### `izvestaj`
| Polje | Podrazumevano | Značenje |
|---|---|---|
| `prag_odstupanja` | 5% prosečnih isplata | ispod ovoga je šum |
| `istorija_meseci` | 6 | prošli izvodi za platu i matricu pretplata |
| `tolerancija` | 0.01 | dopuštena razlika u kontroli bilansa |

### `izvori` \*
Lista. Svaki ima `id` \* i `tip` \*.

| `tip` | Dodatna polja |
|---|---|
| `mejl` | `posiljaoci` \*, `ocekivano_do` (dan u mesecu, 1–31) |
| `mejl_tekst` | `posiljaoci` \*, `izvuci` (polja iz teksta mejla) |
| `folder` | `putanja` \*, `obrazac` |
| `rucno` | `uputstvo` — šta korisnik treba da uradi |

### `racuni` \*
Lista. **Samo poslednje 4 cifre** — skript odbija sve duže od 4 cifre u poljima `zadnje4`, i upozorava na svaki niz od 8+ cifara bilo gde u config-u.

| Polje | Značenje |
|---|---|
| `zadnje4` \* | identifikator računa |
| `tip` \* | `tekuci`, `devizni`, `multivalutni`, `kreditna_kartica`, `stedni` |
| `izvor` \* | `id` iz `izvori`; nije obavezan za račun van obuhvata |
| `valuta` | valuta računa |
| `banka`, `uloga` | opis za ljude i za kategorizaciju |
| `obuhvat` | da li promena stanja ulazi u višak; podrazumevano `true` za sve osim `tip: stedni` — vidi `references/normalizacija.md` |
| `kartica_zadnje4` | debitna kartica vezana za račun |
| `limit` | kod kreditne kartice |
| `naknada_konverzije_procenat` | prateći red tog procenta je naknada |
| `uslov_odrzavanja.min_mesecna_potrosnja` | izveštaj proverava da li je ispunjeno |

### `prihodi`
| Polje | Značenje |
|---|---|
| `naziv` \* | |
| `prepoznaj_po` \* | lista delova opisa transakcije |
| `tip` \* | `prihod` ili `refundacija` (refundacija umanjuje trošak) |
| `racun`, `ritam` | sužavaju i proveravaju prepoznavanje |

Iznos plate se **namerno ne upisuje** u config. Uvek se meri sa izvoda.

### `kategorije`
Mapa ime → lista trgovaca, ili ime → `{trgovci, ritam}`. Poklapanje je po delu opisa, bez obzira na velika i mala slova. `ritam` (`mesecno`, `sezonsko`, `neredovno`) pomaže da normalizacija razdvoji redovno od jednokratnog.

Trgovac u dve kategorije je dvosmislen — skript upozorava.

### `transferi`
`opisi` — delovi opisa koji označavaju premeštanje novca. Prenosi između računa iz config-a prepoznaju se i bez ovoga.

### `krediti`
`naziv` \*, `anuitet` \*, `poslednja_rata` (YYYY-MM) \*, `partija_zadnje4`, `dan_naplate`. Posle `poslednja_rata` kredit ne postoji — skript upozorava kad je datum prošao, jer bi normalizacija inače dodavala nepostojeću ratu u nedogled.

### `kes`
Bez ovog bloka korak 7 se preskače. `ladica: true` znači da se neiskorišćen keš prenosi u sledeći mesec. `stalne_linije` su poznati redovni izdaci gotovinom.

### `rezerva`
`godisnje_procena` i `stavke` — rezerva za neredovne godišnje troškove. Mesečno se oduzima `godisnje_procena / 12`.

### `ciljevi`
`naziv` \*, `iznos` \*, `rok` (YYYY-MM) \*, `valuta`, `drzi_se_na` (zadnje4 računa), `mesecna_stopa_plan`. Ušteđeno se uvek meri na izvodu računa iz `drzi_se_na`, nikad ne uzima iz plana.

### `izlaz`
Bez ovog bloka važi `tip: chat` — samo izveštaj, ništa se ne upisuje.

| Polje | Za tip | Značenje |
|---|---|---|
| `tip` | — | `chat`, `markdown`, `csv` ili `obsidian` |
| `putanja` \* | sve osim `chat` | folder u koji se piše |
| `mesecne_note` | `markdown`, `obsidian` | obrazac, `{YYYY}` i `{MM}` se zamenjuju; podrazumevano `{YYYY}-{MM}.md` |
| `glavni_fajl` | `markdown`, `obsidian` | opcioni pregled po mesecima |
| `fajl` | `csv` | podrazumevano `finansije.csv` |
| `pravila` | sve osim `chat` | opcioni fajl sa pravilima zapisa — ima prednost nad skill-om |
| `log` | sve osim `chat` | opcioni fajl u koji se beleži šta je urađeno |

### `orkestracija`
`podagenti: da` uključuje podelu posla; `modeli.mehanicki/analiticki/verifikacija` biraju model za svaku vrstu posla.

## Održavanje

**Izvodi su autoritet.** Svaka tvrdnja u config-u je hipoteza. Kad izvodi pokažu drugačije, izveštaj predlaže konkretnu izmenu config-a u sekciji `Config`.

**Šta presek tipično predlaže:** nov trgovac koji se ponavlja i nije kategorisan; kredit kome je prošla poslednja rata; račun koji config ne zna a pojavljuje se u prenosima; podračun koji config navodi a izvodi nikad ne pokazuju.

**Zakazani zadatak.** Prompt treba da sadrži putanju do config-a ili ceo config, i rečenicu da je rad bez nadzora. Ko nema folder, nalepi ceo YAML umesto putanje; agent ga tada proverava i koristi preko standardnog ulaza (`proveri_config.py -`), bez upisivanja u fajl. Primer:

```
Pokreni mesečni finansijski presek za prethodni mesec.
Config: ~/Finansije/finansije.config.yaml
Rad bez nadzora: ništa ne upisuj, pitanja skupi u izveštaj.
```
