# Izgled serijala

Izmereno oktobra 2026. na referentnim kadrovima objavljenih klipova. Ako se reference promene, ponovo izmeri.

## Naslov

- Font: dostavljeni `title-heavy.ttf` (Arial Black). Varijanta sa `title.ttf` (Arial Bold Italic) i crnim obrisom je odbijena jer ne liči na objavljene klipove.
- Sintetički kos: tangens 0,187, oko 10,6°.
- Razmak slova: −0,074 em.
- Boja `#FBD800`, **bez obrisa**.
- Meka tamna senka dole levo: pomak oko 5% visine verzala, blago zamućena, oko 90% neprozirnosti.
- Veličina: oko 75% širine kadra za 16 znakova, na širini od 2160 px oko 162 px.
- Jedan red, centar na 15 do 16% visine, iznad glave i ispod gornjeg interfejsa platforme.

Provera pre rendera: tekst sa referentnog kadra postavi svojim stilom uz isečak reference i uporedi težinu, nagib, širinu i senku. Ako slova na referenci (O, C, G) deluju okruglije od dostavljenog fonta, prijavi to i traži font fajl. Zamenu ne biraj sam.

## Obični titlovi

- `typewriter-medium.ttf` (Courier New Bold), oko 140 px na širini od 2160 px, beli.
- Tanak taman obris i meka senka. Bez njih titl nestaje na svetloj odeći.
- Zona grudi, oko 58% visine, jedan ili dva reda do 20 znakova.
- Slova se kucaju u ritmu govora, po vremenima reči iz transkripta. Ceo red se ne pojavljuje odjednom.

## Umeci: podeljen ekran

- Dokument, dokaz ili dijagram koji traje duže od jedne rečenice ide u **gornji panel**, a govornik ostaje **dole**, uporedo, kao maska.
- Na 2160×3840: panel od 0 do 1800 px, taman, sa tankom žutom linijom šava.
- Snimak se spušta bez skaliranja, na primer `crop=2160:2040:0:480,pad=2160:3840:0:1800`. Podesi isečak tako da glava padne odmah ispod šava, a brada ostane iznad donjeg interfejsa, na oko 77% visine.
- Titl tada ide u jednom redu na dnu panela.
- Ulaz i izlaz su tvrdi rezovi na granici rečenice.

## Naglasci

- Poenta ili ključna reč sme da napusti zonu titla, u istom izgledu kao naslov. Na svetloj odeći dozvoljen je tanak taman obris.
- Posle naglaska vraća se osnovni sistem.
- Male bočne kartice, na primer pravila ili šablon, stoje desno od glave i ne pokrivaju gest.

## Bezbedne zone za Reels

- Gore oko 11% visine.
- Dole oko 23% visine.
- Desna kolona ikonica od oko 45% visine naniže.
