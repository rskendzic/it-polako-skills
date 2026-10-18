# Izgled serijala

Izmereno oktobra 2026. na referentnim kadrovima objavljenih klipova. Ako se reference promene, ponovo izmeri.

## Naslov

- Font: dostavljeni `title-heavy.ttf` (Arial Black). Varijanta sa `title.ttf` (Arial Bold Italic) i crnim obrisom je odbijena jer ne liči na objavljene klipove.
- Sintetički kos: tangens 0,187, oko 10,6°.
- Razmak slova: −0,074 em.
- Boja `#FBD800`, **bez obrisa**.
- Meka tamna senka dole levo: pomak oko 5% visine verzala, blago zamućena, oko 90% neprozirnosti.
- Veličina: oko 75% širine kadra za 16 znakova, na širini od 2160 px oko 162 px.
- Oko 75 do 85% širine kadra; duže redove smanji da stanu.
- Centar na 12 do 16% visine, iznad glave i ispod gornjeg interfejsa platforme.
- Dva reda samo kada hook iz scenarija ima dva dela. Inače jedan red.
- Klip ima samo dva naslovna trenutka: hook na početku i poentu. Između njih nema naslova odeljaka.

Provera pre rendera: tekst sa referentnog kadra postavi svojim stilom uz isečak reference i uporedi težinu, nagib, širinu i senku. Ako slova na referenci (O, C, G) deluju okruglije od dostavljenog fonta, prijavi to i traži font fajl. Zamenu ne biraj sam.

## Obični titlovi

- `typewriter-medium.ttf` (Courier New Bold), oko 140 px na širini od 2160 px, beli.
- Tanak taman obris i meka senka. Bez njih titl nestaje na svetloj odeći.
- Zona grudi, oko 58% visine, jedan ili dva reda do 20 znakova.
- Slova se kucaju u ritmu govora, po vremenima reči iz transkripta. Ceo red se ne pojavljuje odjednom.
- Prelome redova izračunaj unapred i crtaj slova na fiksnim pozicijama monospace fonta, da se red ne pomera dok se kuca.
- Prva reč kreće na izmerenom početku zvuka, jer prepoznavanje govora razmaže početak ranije.

## Kadriranje

- U kadru je samo gornji deo tela. Širok kadar koji pokazuje laptop ili pantalone seče se zumom od oko 1,32 do 1,6 i pomakom po visini, tako da vrh glave padne na oko 680 do 760 px na 4K, a glava je horizontalno u centru po segmentu.
- Zum drži sličnim između segmenata preko celog kadra, da oči ne skaču.
- Glava se tokom snimanja pomera. Vrh glave meri po segmentu, na primer maskom osobe na tri frejma.
- Centar titla je veći od 58% visine i od pozicije brade uvećane za 34 px i pola bloka titla. Brada je oko vrh glave + 1040 px, pomnoženo zumom.
- Zum seče od vrha kadra, pa spušta glavu. Naslov i titl postavi po glavi posle zuma.

## Umeci: podeljen ekran

- Dokument, dokaz ili dijagram koji traje duže od jedne rečenice ide u **gornji panel**, a govornik ostaje **dole**, uporedo, kao maska.
- Na 2160×3840: panel od 0 do 1800 px, taman, sa tankom žutom linijom šava.
- Snimak se spušta bez skaliranja: `crop=2160:2040:0:Y0,pad=2160:3840:0:1800`, gde je Y0 vrh glave segmenta minus 60 px. Glava tako padne odmah ispod šava, a brada ostane iznad donjeg interfejsa, na oko 77% visine.
- Titl tada ide u jednom redu, do 23 znaka na 140 px, na dnu panela, oko 1690 px.
- Ulaz i izlaz su tvrdi rezovi na granici rečenice. Rez rasporeda sme da padne i na naglašenu reč.
- Sadržaj sme da se kreće unutar panela: skrolovanje kroz stvaran fajl, marker preko tačno citiranog dela, oznake reda (na primer „KORAK 6 · RED 43”), minimapa celog fajla i [efekti umetaka](efekti.md).
- Gornji panel može da nosi i motion graphic. Tada panel ima svoju kameru i ritam po [motion graphic](motion-graphic.md), a donji kadar govornika ostaje miran.

## Naglasci

- Poenta ili ključna reč sme da napusti zonu titla, u istom izgledu kao naslov, bez običnog titla ispod. Na svetloj odeći dozvoljen je tanak taman obris.
- Reči poente iskaču na svojim vremenima. Druga rečenica zamenjuje prvu na svom početku.
- Posle naglaska vraća se osnovni sistem.
- Poenta iza govornika: maska osobe (na primer RVM MobileNetV3, ONNX, na CPU) po frejmu, a providnost poente se množi sa (1 − maska). Donji red poente postavi po medijani vrha glave iz samih maski, tako da kosa pokrije donjih oko 30% srednjih slova. Proveri da pokrivene reči ostaju čitljive dok se glava pomera.
- Male bočne kartice, na primer pravila ili šablon, stoje desno od glave i ne pokrivaju gest.

## Bezbedne zone za Reels

- Gore oko 11% visine.
- Dole oko 23% visine.
- Desna kolona ikonica od oko 45% visine naniže.

## Autentičan sadržaj

- Stvaran fajl se prikazuje stvarnim tekstom. Pretipkan tekst je dozvoljen, uz oznaku u panelu, na primer „izvorni tekst, pretipkan”.
- Svaki istaknut deo mora postojati u stvarnom fajlu. Proveri to kodom.
- Ilustracija nosi oznaku „ilustracija”.
- Odgovori koje gledalac treba sam da da ostaju prazne linije.
