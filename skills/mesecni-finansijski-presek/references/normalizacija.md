# Normalizacija i bazna linija

Promena stanja jednog računa nije rezultat meseca, i nije osnova za ikakvu projekciju. Ovaj fajl je o tome kako doći do broja koji se može ponoviti.

## Zašto

Mesec u kom je legao bonus izgleda kao dobar mesec. Mesec u kom je kupljen nameštaj izgleda kao loš. Nijedan od tih brojeva ne govori ništa o tome koliko novca ima svakog meseca — a to je jedini broj od kog zavisi da li plan štednje izlazi.

Primer: promena stanja +120.000, izgleda odlično. Bonus je bio 120.000. Bez bonusa je mesec bio **nula**. Plan izgrađen na +120.000 puca za dva meseca.

## Obuhvat

Pre vodopada mora biti jasno **čiji** se višak računa. Obuhvat je skup računa čiji je saldo novac za trošenje — `racuni[].obuhvat` u config-u, podrazumevano svi osim `tip: stedni`.

Zašto ne jedan račun:

| Događaj | Tekući račun | Stvarno |
|---|---|---|
| prenos 20.000 na štednju | −20.000 | ušteda, nije trošak |
| kupovina karticom 5.000 | 0 | trošak |
| uplata 10.000 na karticu | −10.000 | prenos, nije trošak |
| kupovina 100 EUR za 11.800 | −11.800 | prenos; trošak je samo razlika do zvaničnog kursa tog dana |

Višak meseca:

```
  Σ promena stanja računa u obuhvatu
+ prenosi iz obuhvata na sopstvene račune van obuhvata
− prenosi sa sopstvenih računa van obuhvata u obuhvat
```

- **Kartica u obuhvatu** (preporučeno) vodi se kao dug, negativno stanje. Kupovina povećava dug i umanjuje višak kad se desi; uplata na karticu je interni prenos.
- **Kartica van obuhvata** je dopuštena, po gotovinskom principu: kupovine ne utiču na višak dok se kartica ne plati, a **uplata na karticu je potrošnja tog meseca**, ne ušteda. Podizanje gotovine sa takve kartice je pozajmica, ne prihod. Izveštaj mora da kaže da je kartica van obuhvata — mesec sa velikom uplatom duga izgleda gore nego što je potrošnja bila.
- **Prenosi unutar obuhvata** se poništavaju. Razlika krakova (kurs, naknada) je stvaran trošak i već je u promeni stanja; prijavi je, ne koriguj.
- **Devize**: promenu svakog računa računaj u njegovoj valuti, pa je preračunaj jednim kursom (srednji kurs na poslednji dan meseca, obeležen kao izvor). Tako kursna razlika na novac koji je samo stajao ne ulazi u višak.
- **Konverzija između računa u obuhvatu** traži i zvanični kurs na **dan konverzije** (`kurs_dana`). Trošak konverzije je razlika krakova po tom kursu i ulazi u višak. Promena kursa od dana konverzije do kraja meseca je nerealizovana kursna razlika i ne ulazi. Primer: 11.800 RSD za 100 EUR, zvanični kurs tog dana 117,5, na kraju meseca 117,2. Trošak je 50, ne 80; preostalih 30 je promena kursa. Bez `kurs_dana` ta dva se ne mogu razdvojiti i obračun je nepotpun.
- **Prenos na račun koji nije u config-u** nije transfer — to je rashod, dok korisnik ne kaže da je račun njegov i ne doda ga.
- **Račun u obuhvatu bez proverenog izvoda** znači da je višak nepoznat. Ne računaj višak bez njega.

`scripts/obracun_viska.py` radi ovo i ceo vodopad; ručni obračun služi samo za proveru skripta.

## Vodopad

```
  višak meseca                 (iz obuhvata, gore)
− jednokratni prihodi          bonus, regres, refundacija, poklon, prodaja stvari
+ jednokratni troškovi         nameštaj, bela tehnika, oprema, putovanje, popravka
+ obaveze koje prestaju        rata kredita koja je zadnja, pretplata koja je ukinuta
= ponovljiv mesečni višak
− rezerva za neredovne troškove
= realno raspoloživo za štednju
```

Svaki korak obeleži kao **izvedeno** i navedi od čega. Ko čita za godinu dana mora da vidi odakle je broj došao.

Primer (sintetički): tekući +67.716,19, prenos na štednju 20.000. Višak po jednom računu bi bio 67.716,19; stvarni je **87.716,19**. Razlika je ušteda koja bi se inače vodila kao potrošnja.

## Kontrola drugim putem

```
redovni prihodi − redovni troškovi + obaveze koje prestaju = ponovljiv mesečni višak
```

Redovni troškovi su svi troškovi meseca sa svih računa u obuhvatu (i karticom), bez prenosa i bez jednokratnih. Dva puta moraju dati isti broj. Ako ne daju, neka stavka je na pogrešnoj strani — najčešće je jednokratni trošak ostao među redovnim, refundacija ubrojana kao prihod, ili prenos na štednju ubrojan kao trošak.

Ovo je jedina prava provera normalizacije. Bez nje je vodopad niz pretpostavki.

## Jednokratno naspram ponavljajućeg

Najčešća greška nije u aritmetici, nego u klasifikaciji.

Pre nego što iz bilo koje kategorije izvedeš savet, razdvoj je. Keš od 110.000 može biti 90.000 jednokratnih kupovina i 20.000 mesečne navike. Savet „prepolovi keš" u tom slučaju nije samo beskoristan — promašuje pravi problem, koji je da rezerva za jednokratne troškove nije dovoljna.

Test: **da li bi se ovo pojavilo i sledeći mesec?** Kategorija sa `ritam: mesecno` u config-u je kandidat za redovno, `sezonsko` i `neredovno` za rezervu — ali test važi za svaku transakciju, ne za kategoriju. Sezonsko (grožđe u septembru, drva u oktobru) je godišnje, ne mesečno — ide u rezervu, ne u mesečne troškove.

## Rezerva za neredovne troškove

Procena se skoro uvek pokaže preniskom, jer se pravi od onoga čega se korisnik seti: more, registracija, kvarovi. Izostaje nameštaj, sezonska oprema, sitna bela tehnika, odeća.

Način da se proveri: saberi stvarne jednokratne troškove iz preseka i uporedi sa mesečnom rezervom.

Primer: rezerva je 25.000 mesečno (300.000 godišnje), a jedan jedini mesec nosi 70.000 jednokratnih troškova — nameštaj, aparat, sezonska oprema. Ako se takav mesec ponavlja svaki drugi ili treći put, procena ne pokriva ni polovinu stvarnog tempa.

Ako config ima `rezerva.godisnje_procena`, uporedi je sa zbirom jednokratnih troškova iz poslednjih `izvestaj.istorija_meseci` meseci, preračunatim na godinu.

Kad se to vidi, reci. Projekcija sa potcenjenom rezervom izgleda bolje nego što jeste, i puca na prvom kvaru.

## Prihodi

Povuci 5–7 izvoda i poređaj redovnu uplatu po mesecima. Obrazac koji tražiš:

| Mesec | Iznos (izmišljeno) |
|---|---:|
| 1 | 96.120,00 |
| 2 | 100.410,50 |
| 3 | 100.380,20 |
| 4 | 100.295,00 |
| 5 | 112.900,00 |
| 6 | 100.350,75 |

Četiri meseca u rasponu od nekoliko stotina su plata: **~100.350**. Mesec 1 je ispod, mesec 5 iznad — oba se izdvajaju i oba treba objasniti pre nego što uđu u prosek.

Prosek svih meseci bi dao ~101.700 i sakrio bi oba odstupanja. **Gledaj grozd, ne prosek.**

Ako korisnik kaže koliko mu je plata, proveri. Zapamćen broj je skoro uvek zaokružen nadole ili zastareo — razlika od 8% mesečno je dovoljna da obrne zaključak o tome da li cilj izlazi.

## Kanali prihoda

Ista firma često plaća sa više računa. Plata sa jednog, refundacije troškova sa drugog.

Refundacija nije prihod. Ona pokriva trošak koji je već bio, i oduzima se od tog troška:

```
tvoj deo putovanja = ukupno potrošeno − refundacija
```

Ako je ubrojiš u prihod, i mesec i cena putovanja su pogrešni.

## Projekcija ka cilju

```
potrebno mesečno = (cilj − već ušteđeno) / meseci koji su ostali
```

Tri stvari koje se lako prećute:

**Već ušteđeno proveri na izvodima** računa iz `ciljevi[].drzi_se_na`. Ako ga nema ni na jednom računu, ušteđeno je nula — koliko god plan tvrdio. Ostatak putnog budžeta ili sitan saldo na kartici nije štednja.

**Propušteni meseci se prelivaju.** Dva meseca bez priloga ne pomeraju rok — povećavaju mesečnu stopu na ostatak, često preko raspoloživog.

**Uporedi potrebnu stopu sa realno raspoloživim.** Ako je potrebna stopa veća, cilj ne izlazi. Reci to i ponudi alternative sa cenom svake: manji cilj (i koliko to menja ratu kredita), pomeren rok, ili veća stopa (i odakle bi došla).

Plan koji ne izlazi je bolje saznati pet meseci unapred nego mesec unapred.
