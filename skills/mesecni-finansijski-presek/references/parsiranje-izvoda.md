# Parsiranje izvoda

## Osnovni postupak

```bash
pdftotext -layout izvod.pdf izvod.layout.txt   # cuva kolone, prvi izbor
pdftotext -raw    izvod.pdf izvod.raw.txt      # rezerva kad je tabela izlomljena
```

Pročitaj **sve** strane. Izvodi tekućeg računa se često prelivaju na 5+ strana, a podnožje svake strane ponavlja zaglavlje banke — ne pobrkaj ga sa podacima.

Kad se brojevi iz dva režima ne slože, izvuci samo brojeve i uporedi:

```bash
grep -oE '[0-9]{1,3}(\.[0-9]{3})*,[0-9]{2}' izvod.layout.txt | sort > a
grep -oE '[0-9]{1,3}(\.[0-9]{3})*,[0-9]{2}' izvod.raw.txt    | sort > b
diff a b
```

Prazan diff znači da su oba parsiranja pročitala iste brojeve, i da možeš verovati bilo kojem.

## Format brojeva

Format zadaje `lokalizacija.decimalni_separator` u config-u. Bez njega ga `kontrola_bilansa.py` otkriva iz fajla.

| Separator | Primer | Tipično |
|---|---|---|
| `","` | `1.234.567,89` | Srbija, većina kontinentalne Evrope |
| `"."` | `1,234,567.89` | UK, SAD, neki devizni izvodi |
| `","` sa razmakom | `1 234 567,89` | Francuska, Skandinavija — ukloni razmake pre parsiranja |
| `"."` sa apostrofom | `1'234'567.89` | Švajcarska — ukloni apostrofe pre parsiranja |

```python
def u_broj(s):
    return float(s.strip().replace('.', '').replace(',', '.'))
```

Ista banka može koristiti različit format na različitim računima. Kad se format izvoda ne poklapa sa config-om, izvod je autoritet — prijavi i predloži izmenu (ili polje po računu).

## Kolone

Tipičan red izvoda: `Rb. | Opis | Dat. knjiženja | Dat. valute | Isplata | Uplata | Stanje`. Nazivi se razlikuju po banci i jeziku (Debit/Credit/Balance, Zaduženje/Odobrenje/Saldo) — kolona stanja je ona najdesnija koja nosi tekući saldo, i po tome je `kontrola_bilansa.py` nalazi bez obzira na naziv.

Dva datuma nisu greška:
- **datum valute** — kad je transakcija izvršena
- **datum knjiženja** — kad je pala na račun

Kartične kupovine iz prošlog meseca se knjiže u ovom. Za kategorizaciju meseca koristi **datum knjiženja**, jer se po njemu poklapa bilans. Datum valute zadrži u zapisu, jer objašnjava zašto se neka kupovina pojavljuje „prekasno".

## Devizna naknada kao poseban red

Na deviznim računima se uz transakciju često javlja prateći red od fiksnog procenta iznosa. To je naknada, ne druga transakcija. Procenat po računu stoji u `racuni[].naknada_konverzije_procenat`.

Razdvoj glavni iznos od naknade i prikaži oba. Ne duplaj ih u zbiru i ne tretiraj naknadu kao potrošnju kod trgovca.

Provera: ako je prateći red tačno taj procenat prethodnog (sa zaokruživanjem), to je naknada. Ako config nema procenat a obrazac se ponavlja, predloži ga.

## Reverzali

Par redova koji se poništavaju (isplata 1,00 i uplata 1,00, isti trgovac, isti dan) je provera kartice, ne potrošnja. Neto je nula.

Banka takve parove često **netuje u zbirnom redu**, pa se tvoj zbir pojedinačnih redova neće poklopiti sa zbirom na izvodu dok ih i ti ne netuješ. Isto važi za vraćenu naknadu: naplata 595 pa povrat 595 daje neto nulu, a u koloni uplata se možda ne vidi.

Ako ti zbir ne izlazi za iznos koji se pojavljuje i kao isplata i kao uplata — to je reverzal.

## Izvodi bez priloga

Kreditne kartice često šalju samo tekst i link na portal koji traži logovanje. Iz teksta izvuci:

- ukupan dug
- minimalnu uplatu
- datum dospeća
- broj izvoda

Ne pokušavaj da se logujes na portal. Za detaljan raspored rata traži od korisnika da pošalje PDF.

## Prilozi iz mejla

Prilozi mogu biti URL-safe base64:

```bash
tr '\-_' '+/' < prilog.b64 | base64 -d > izvod.pdf
head -c 5 izvod.pdf   # mora dati %PDF
```

Ako nije `%PDF`, fajl je pokvaren — ne parsiraj ga, preuzmi ponovo.

## Broj izvoda ne mora da odgovara mesecu

Računi otvoreni u različito vreme imaju različite redne brojeve izvoda. Izvod br. 8 i izvod br. 9 mogu pokrivati isti kalendarski mesec. **Period u zaglavlju je autoritet, ne redni broj.**

## Istorija

Za normalizaciju prihoda i za matricu pretplata treba ti `izvestaj.istorija_meseci` meseci (podrazumevano 6), ne samo tekući. Pretraži mejl po istom pošiljaocu za starije periode i preuzmi ih u odvojen folder.

Kad proveravaš platu, povuci izvode računa na koji plata stiže. Kad proveravaš pretplate, povuci izvode računa čija `uloga` ih pominje i napravi matricu servis × mesec — tako se vide poskupljenja, nove i mrtve pretplate.

## Zbirni redovi

Zaglavlje, podnožje i rekapitulacija po strani nose zbirove (početno, isplate, uplate, završno). Takav red ne sme u lanac: njegov zbir uplata bi „objasnio" skok stanja i prikrio transakciju koja je ispala. `kontrola_bilansa.py` izbacuje iz lanca svaki red sa bar dva iznosa iz zaglavlja i navodi te linije.

## Kad stati

- Parsiranje padne ili je tekst nečitljiv → prijavi fajl, stani
- Kontrola bilansa NIJE PROSLA → prijavi proveru i razliku, stani
- Kontrola bilansa NEPOTPUNA → prijavi razlog, stani; to nije uspeh
- Izvor nedostaje → prijavi koji, stani

Ni u jednom slučaju ne procenjuj brojeve. Procenjen broj u finansijskom izveštaju izgleda kao podatak i neće biti proveren.
