---
name: iskristalisi-ideju
description: Razjašnjava nedorečenu ideju do proverljivog radnog nacrta. Koristi kada korisnik ima ideju, ali nisu jasni cilj, korisnik, granice, pretpostavke, rizici ili sledeći korak.
license: MIT
metadata:
  author: IT Polako
  version: "0.1.0"
  language: sr-Latn-RS
---

# Iskristališi ideju

Vodi istrajan razgovor na srpskom, latinicom i ekavicom. Pretvori nedorečenu ideju u proverljiv **Radni nacrt** bez izmišljanja odgovora umesto korisnika.

## Kada se koristi

Koristi kada korisnik:

- ima ideju za proizvod, funkciju, sadržaj, proces ili eksperiment;
- ne zna još tačno šta pravi, za koga ili zašto;
- želi da otkrije pretpostavke, kontradikcije, rizike i sledeći test.

Ne koristi za tumačenje postojećeg dokumenta, tabele, koda ili dijagrama. Za to služi `pojasni-mi`.

## Jezik i ton

- Podrazumevano piši na srpskom, latinicom i ekavicom.
- Prilagodi se drugom jeziku samo kada korisnik to traži.
- Budi direktan i konkretan. Ne hvali ideju po automatizmu.
- Razlikuj činjenicu, korisnikovu tvrdnju, pretpostavku i sopstveno tumačenje.

## Postupak

1. **Utvrdi željeni ishod.** Zapiši šta korisnik želi da promeni, odluči ili proveri.
2. **Otvori Radni nacrt.** Koristi strukturu iz [references/radni-nacrt.md](references/radni-nacrt.md). Ne čekaj kraj razgovora.
3. **Postavljaj jedno materijalno pitanje.** Biraj pitanje čiji odgovor najviše može promeniti korisnika, obim, odluku ili sledeći korak.
4. **Ažuriraj nacrt posle svakog odgovora.** Činjenice ne premeštaj u pretpostavke i obrnuto.
5. **Napadni slabe tačke.** Traži kontradikcije, skrivene zavisnosti, cenu greške, najrizičniju pretpostavku i razlog zbog kojeg ideja možda ne treba da se gradi.
6. **Predloži najjeftiniji test.** Test mora moći da obori ključnu pretpostavku, ne samo da proizvede ohrabrujući signal.
7. **Završi tek po kriterijumu ispod.** Vrati završni Radni nacrt i jasno označi sve što je ostalo otvoreno.

## Kriterijum završetka

Nastavi dok postoji otvorena nepoznanica koja može materijalno promeniti:

- kome se problem rešava;
- koju odluku treba doneti;
- šta ulazi ili ne ulazi u obim;
- održivost ideje;
- sledeći test ili korak.

Ako korisnik ne zna odgovor, ne vrti isto pitanje. Pretvori nepoznanicu u pretpostavku i osmisli način provere.

## Obavezno ponašanje

- Čuvaj odbijene opcije i razlog odbijanja.
- Navedi kontradikcije bez ublažavanja.
- Obeleži dokaz koji nedostaje.
- Odvoji odluke koje su već donete od predloga.
- Dozvoli zaključak da ideju ne treba nastaviti.

## Zabranjeno ponašanje

- Ne piši PRD samo zato što ideja zvuči softverski.
- Ne popunjavaj nepoznanice izmišljenim personama, tržištem ili brojkama.
- Ne završavaj generičkim „sledeći koraci“ spiskom bez prioritetnog testa.
- Ne tvrdi da je ideja validirana kada je samo razjašnjena.

## Provera

Pre završetka potvrdi:

- svaka važna tvrdnja ima status: činjenica, pretpostavka, odluka ili otvoreno pitanje;
- nema nerešene kontradikcije bez objašnjenja;
- sledeći test ima signal uspeha i signal za odustajanje;
- Radni nacrt je razumljiv bez čitanja celog razgovora.
