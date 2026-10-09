---
name: it-polako-montaza
description: Montira IT Polako talking-head klip od originalnog snimka telefona (4K HLG) do završnog fajla, sa transkriptom po rečima, izborom tejkova, naslovom i titlovima u stilu serijala, umecima kao podeljen ekran, HDR renderom i proverom. Koristi samo kada postoje originalni snimak, produkcione beleške ili scenario, vizuelne reference i fontovi serijala.
license: MIT
metadata:
  author: IT Polako
  version: "0.2.0"
  language: sr-Latn-RS
---

# IT Polako montaža

Montiraj jedan IT Polako klip od originalnog snimka do završnog fajla. Snimak je izvor istine za govor, reference su izvor istine za izgled, a završni fajl se proverava pre nego što se prijavi uspeh.

## Kada se koristi

Koristi kada postoje:

- jedan originalni snimak govornika, obično telefon, vertikalno, 4K, HLG;
- produkcione beleške ili scenario klipa;
- vizuelne reference objavljenih klipova, bar jedan kadar sa naslovom i jedan sa običnim titlom;
- font fajlovi serijala.

Ne koristi za pisanje ili popravku scenarija, za objavu ni za montažu bez originala.

Ako projekat ima sopstveni postupak montaže, na primer projektni `SKILL.md` sa odeljcima Inputs, Workflow i Verification, on ima prednost. Ovaj skill dodaje proverena pravila izgleda i izvršenja.

## Jezik i ton

- Titlovi prate izgovoreno, ne scenario.
- Izveštaj je na srpskom, latinicom i ekavicom, kratak i bez ulepšavanja.

## Postupak

1. **Ulazi.** Pročitaj zadatak, produkcione beleške, scenario, reference i fontove (`fc-scan`). Ako fajl nedostaje, prijavi tačno koji. Zapiši sha256, veličinu i vreme izmene originala. Proveri da li u istom folderu radi drugi agent (`find . -newer <fajl zadatka> -type f`). Ako radi, rad i izlaz drži u svom podfolderu (`work/<agent>/`, `output/<agent>/`) i ne presnimavaj tuđe fajlove. Fontovi po ulozi: `title-heavy.ttf` za naslov i poentu, `typewriter-medium.ttf` za titl, `title.ttf` nije za naslove.
2. **Snimak.** Pokreni `ffprobe` i zapiši rezoluciju, rotaciju, fps, kodek, prenosnu funkciju, primarne boje, Dolby Vision i `start_time` audio toka. Pre bilo kakve konverzije pitaj. Podrazumevano: isti kadar i fps, HEVC 10-bit HLG BT.2020, a Dolby Vision metapodaci se gube.
3. **Jedan transkript po rečima.** Prati [transkript i rez](references/transkript-i-rez.md). Ispravi vremena za `start_time` audio toka. Nejasne reči razreši bodovanjem kandidata nad celom rečenicom iz snimka, ne scenarijem. Titl piše izgovoreni oblik, i kada je kolokvijalan.
4. **Izbor tejkova i rez.** Za svaki tejk proveri da li je početak ponovljen, jer prepoznavanje govora spaja ponovljene fraze. Neprekinut tejk ima prednost nad rezom usred rečenice. Izmeri energiju zvuka na ivicama svakog segmenta i 1,2 s oko njih: kratka reč posle pauze ume da ostane van granice tišine. Kada naslov ili poenta citiraju rečenicu, izaberi tejk čije reči odgovaraju i isti oblik koristi u oba.
5. **Jedan tretman.** Svaki vizuelni element ima narativni posao: naslov, obični titlovi, naglasci, umeci i kraj. Naslovni izgled se javlja samo dva puta: naslov na početku i poenta. Poenta nema titl ispod sebe. Izgled prati [izgled serijala](references/izgled.md).
6. **Pregled.** Pre pregleda pokreni prepoznavanje govora nad isečenim zvukom i uporedi ga sa titlovima reč po reč. Napravi lak pregled u nižoj rezoluciji kroz HLG→SDR LUT (`scripts/hlg_boje.py lut`). Sam pogledaj ključne frejmove: naslov uz referencu, ulaz i izlaz iz umetka, poentu i poslednji frejm. Ako je korisnik dostupan, pokaži mu pregled i sačekaj potvrdu pre završnog rendera.
7. **Završni render.** Prati [HLG postupak](references/hlg.md). Ako okruženje ograničava trajanje poziva ili memoriju, radi po [ograničenom okruženju](references/ograniceno-okruzenje.md).
8. **Izveštaj.** Navedi tačnu putanju fajla, šta je kreativno urađeno, kako je postupak primenjen i šta nije provereno.

## Obavezno ponašanje

- Govor iz snimka ima prednost nad scenarijem. Titl piše ono što je rečeno, i u kolokvijalnom obliku („upustvo”), ne standardni pravopis.
- Naslov se meri na referenci i pre rendera stavlja uporedo sa njom.
- Umetak koji traje duže od jedne rečenice ide u podeljen ekran: gore umetak, dole govornik.
- Original ostaje netaknut. Rezolucija, fps i kolor namera ostaju kao u originalu, osim ako korisnik odobri drugačije.
- Stvarni dokument se prikazuje stvarnim tekstom. Ilustracija se označava kao ilustracija, a prazan šablon je vidljivo prazan.
- Bez muzike i risera, osim ako produkcione beleške traže drugačije.

## Zabranjeno ponašanje

- Ne biraj font po imenu fajla i ne zamenjuj dostavljenu porodicu drugom bez odobrenja.
- Ne veruj transkriptu da u tejku nema ponovljenih fraza.
- Ne seci po granici tišine bez provere energije posle nje.
- Ne dodaji međunaslove između naslova i poente.
- Ne tvrdi da je nešto preslušano ako nije preslušano uhom. Napiši čime je provereno.
- Ne tvrdi da je klip montiran po veštini ako postupak nije stvarno primenjen.
- Ne objavljuj klip.
- Ne briši i ne presnimavaj tuđe fajlove.

## Provera

Završeno je tek kada:

- sha256 originala je isti pre i posle;
- broj frejmova po delu i ukupno odgovara planu, a na spojevima nema duplikata ni skokova (`tblend` razlika);
- `ffprobe` finala pokazuje očekivanu rezoluciju i fps, HEVC Main10, `arib-std-b67` i `bt2020`;
- naslov stoji uporedo sa referencom i odgovara joj po težini, nagibu, širini i senci;
- prepoznavanje govora nad finalom daje sve rečenice redom i poklapa se sa titlovima reč po reč, uz napomenu da ponavljanja ne otkriva;
- glasnoća je izmerena: cilj oko −14 LUFS, true peak najviše −1 dBTP; ako true peak ograniči pojačanje, prijavljena je postignuta vrednost;
- izveštaj navodi šta nije provereno: preslušavanje uhom, prikaz na HDR ekranu, sinhronizaciju usana.
