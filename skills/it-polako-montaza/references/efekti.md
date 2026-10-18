# Efekti umetaka

Odobreno oktobra 2026, posle klipa o pripremi prezentacije. Važi za umetke u gornjem panelu koje vodi govor: dokumente, dokaze, dijagrame i animacije pojmova. Nezavisan animirani svet prati [motion graphic](motion-graphic.md).

## Princip

- Jedan motivisan pokret na izgovorenu reč, pa mirno držanje.
- Kamera grafike se kreće, govornik ne.
- Svaki efekat pokazuje ideju rečenice. Nijedan nije ukras.

## Povlačenje kamere unazad

- Sadržaj panela gradi se kao jedan „svet”, na primer polje zahteva i ono što zahtev proizvede, i prikazuje kroz 2D kameru (zum i centar) sa smoothstep pokretima.
- Počni blizu zahteva, oko 1,75×, tako da polje i dalje staje u kadar. Zahtev se kuca na svojim rečima.
- Na sledećoj rečenici kamera se za oko 1 s povuče unazad i otkrije rezultat, polako se smiri i stane na rečenici koja zatvara misao.
- Kasnije rečenice koriste isti svet: priđi elementu o kome se govori (oko 1,8×), vrati se na početni kadar, pređi na drugi element.
- Vektore i fontove crtaj na trenutnom zumu da krupni kadrovi ostanu oštri. Svet odseci maskom po obliku panela.

## Ono što nedostaje

- Prazna isprekidana mesta pojavljuju se u postojećim karticama na rečima koje ih imenuju, na primer „kome pričaš?” ili „šta je drugačije?”.
- Mesto o kome se upravo govori je aktivno: žuto, deblje crtice, veća oznaka. Ostala su prigušeno bela.
- Na reči koja imenuje problem mesta požute, popune se sivim punjenjem i preko njih padne pečat sa izgovorenom frazom: težak font, beli okvir, −5°, skok veličine 1,3→1,0 za 0,15 s.

## Duži zahtev

Polje zahteva raste preko ivice kadra sivim crticama umesto reči, pa ga na reči preseče jedna žuta dijagonala.

## Izlazak iz okvira

- Za rečenicu o nečemu što napušta svoje mesto: jedna kartica se poveća oko 1,12×, okrene oko 7° i izađe kroz ivicu panela. Iz njenog ugla izraste oblačić sa tri tačke, a ostatak se priguši oko 45%.
- Kartica ide u stranu ili gore, nikad u zonu titla.
- Posle toga ide čist kadar lica preko celog ekrana.

## Zamena uloga, pa nit razgovora

- Dve oznake, TI belo i AI žuto, sa strelicom TI→AI. Na glagolu zamene mesta po suprotnim lukovima, a žuta strelica se iscrta AI→TI.
- U sledećem segmentu iste oznake se smanje u oznake niti pitanje → odgovor → sledeće pitanje. Pitanja se kucaju žuto, odgovor su prazne linije, veze su tanke.
- Nit nestaje u poslednjih 0,35 s pre poente.

## Završna kartica zahteva

Stara kratka komanda stoji iznad, precrtana žuto. Novi zahtev se kuca na svojim rečima u velikoj kartici (oko 118 px na 4K), bitan red je žut, kursor nestaje oko 0,6 s posle poslednje reči, pa sledi držanje.

## Ostalo

- Kartice koje kruže oko govornika: samo ako izgovorena lista nema bolju strukturu. Jedan korak po reči, nikad neprekidno kruženje oko glave. Povlačenje kamere obično radi bolje.
- Digitalni zum, spor prilaz na ključnoj rečenici: samo u rasporedu preko celog kadra. `zoompan` je 8-bitni, pa radi sub-pikselski isečak 10-bitnih ravni po frejmu (na primer PIL režim `F` i `resize(box=…)`) i šalji sirovi `yuv420p10le` u ffmpeg kroz FIFO.
- Stakleni izgled samo za površine (kartice, panel). Slova naslova i poente ostaju puna.
- Grafikon koji raste samo kada govor ima stvarne brojeve.
- Snimljeni kadar govornika se ne rotira, ne kruži i ne menja mu se perspektiva.

## Odbačeno

- Staklena traka grafike preko grudi, uz veliko lice: prelazi preko brade.
- Grafika u donjoj trećini: pada pod korisničko ime i opis na Reelsu, na 77 do 90% visine.
- Dodatni naslovi između hooka i poente.
