---
name: pojasni-mi
description: Pretvara konkretan ugovor, tabelu, kod, dokument, URL ili dijagram u sledljivu interaktivnu HTML Mapu razumevanja. Koristi kada korisnik mora nešto da razume, odluči ili uradi na osnovu stvarnog izvora.
license: MIT
metadata:
  author: IT Polako
  version: "0.1.0"
  language: sr-Latn-RS
---

# Pojasni mi

Od stvarnog artefakta napravi samostalnu interaktivnu **Mapu razumevanja** na srpskom, latinicom i ekavicom. Cilj nije lep sažetak, nego razumevanje dovoljno dobro da korisnik donese odluku ili izvede radnju.

## Kada se koristi

Koristi za ugovor, tabelu, CSV/XLSX, kod ili repozitorijum, PDF/Word dokument, URL, sliku, šemu ili dijagram kada korisnik navede šta mora da razume, odluči ili uradi.

Ne koristi kao generički kurs o temi bez konkretnog izvora. Ne koristi za razradu nove ideje; za to služi `iskristalisi-ideju`.

## Podrazumevani rezultat

Napravi jedan lokalni fajl `mapa-razumevanja.html` koji:

- radi bez interneta i bez instalacije zavisnosti;
- jasno odvaja **Izvor** od **Tumačenja**;
- vezuje materijalne tvrdnje za stranu, odeljak, ćeliju, formulu, fajl, simbol ili drugi locirajući podatak;
- sadrži režim **Idi u detalje**;
- podrazumevano sadrži praktičnu proveru **Proveri me**;
- nudi what-if ili odgovarajuću proveru posledica kada izvor to dopušta.

## Postupak

1. **Potvrdi ulaz.** Moraš imati stvarni artefakt i operativni cilj. Ako jedno nedostaje, traži samo to.
2. **Pregledaj izvor.** Ne zaključuj iz naziva fajla ili kratkog isečka ako je dostupan ceo sadržaj.
3. **Izaberi pravila tipa.** Učitaj odgovarajuću referencu:
   - [ugovori](references/ugovori.md)
   - [tabele](references/tabele.md)
   - [kod](references/kod.md)
   - [dokumenti i dijagrami](references/dokumenti-i-dijagrami.md)
4. **Napravi model mape.** Prati [format mape](references/format-mape.md). Svaka sekcija mora imati najmanje jednu `source_refs` stavku.
5. **Proveri vernost.** Odvoji ono što izvor kaže od zaključka, neizvesnosti i nedostajućeg podatka. Ukloni ili označi tvrdnju koju ne možeš da vežeš za izvor.
6. **Renderuj HTML.** Pokreni `scripts/render_map.py <ulaz.json> <izlaz.html>` iz direktorijuma ovog skilla. Završni izlaz mora biti jedan samostalni HTML fajl.
7. **Otvori i proveri.** Proveri konzolu, navigaciju, `Idi u detalje`, what-if i `Proveri me`. Ne prijavljuj uspeh bez stvarnog otvaranja kada pregledač postoji.
8. **Ponudi objavljivanje odvojeno.** Lokalni HTML je završen rezultat. Claude Artifact je opcioni kanal isporuke, nikada preduslov.

## Idi u detalje

`Idi u detalje` nije poseban skill. Kada korisnik izabere deo:

1. vrati se na odgovarajući deo izvora;
2. dodaj kontekst, odnose, posledice i neizvesnosti samo za taj deo;
3. ne širi ostale sekcije bez potrebe;
4. ažuriraj isti HTML, a u Claude Code-u i isti Artifact ako je ranije objavljen i korisnik to želi.

## Proveri me

`Proveri me` nije poseban skill. Pitanja moraju proveravati primenu:

- predviđanje posledice;
- izbor bezbednog postupka;
- pronalaženje rizika ili kontradikcije;
- promenu ulaza i procenu ishoda;
- odluku koju izvor podržava ili ne podržava.

Ne koristi trivijalno prepričavanje. Svako objašnjenje odgovora mora vratiti korisnika na lokaciju u izvoru. Kviz je podrazumevan, ali ga izostavi kada korisnik to izričito traži.

## Claude Artifact i privatnost

- Nikada ne objavljuj automatski.
- Pre objavljivanja reci da se HTML šalje na Anthropic servere i traži eksplicitnu saglasnost.
- Za poverljiv ili lični sadržaj preporuči lokalni HTML ili redigovanu verziju.
- Ako je Claude Code Artifact alat dostupan, objavi tek posle provere lokalnog fajla i saglasnosti.
- Ako alat nije dostupan, lokalni HTML ostaje potpuno funkcionalan rezultat.

## Zabranjeno ponašanje

- Ne mešaj citat ili podatak iz izvora sa svojim tumačenjem.
- Ne izmišljaj stranu, ćeliju, liniju, formulu, odnos ili pravnu posledicu.
- Ne pretvaraj približan podatak u precizan.
- Ne koristi udaljene biblioteke, fontove, slike, analitiku ili mrežne pozive u HTML-u.
- Ne koristi `eval`, dinamičko izvršavanje formule ili neproveren `innerHTML` za sadržaj izvora.
- Ne predstavljaj objašnjenje ugovora kao pravni savet.

## Provera

Završeno je tek kada:

- postoji jedan lokalni HTML koji se otvara bez mreže;
- svaka materijalna sekcija ima locirajući izvor;
- sadržaj izvora i tumačenje su vizuelno odvojeni;
- `Idi u detalje` i `Proveri me` rade tastaturom i mišem;
- nema grešaka u konzoli;
- what-if ne koristi neproverenu matematiku;
- objavljivanje nije obavljeno bez eksplicitne saglasnosti.
