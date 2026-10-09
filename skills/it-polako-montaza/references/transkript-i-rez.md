# Transkript i rez

## Transkript

- Jedan prolaz sa vremenima po rečima, na srpskom.
- Na macOS-u: `whisperkit-cli transcribe --language sr --use-prefill-prompt --word-timestamps`.
- U Linux okruženju isti model daje lokalni faster-whisper `large-v3-turbo` (int8).
- Jezik se zadaje izričito. Auto-detekcija na srpskom ume da vrati prevod.
- Početni prompt služi samo za pismo, na primer „Pišemo srpski latinicom: č, ć, š, ž, đ.” Tekst scenarija se nikad ne daje kao prompt.
- Isečci kraći od oko 1,5 s haluciniraju („Hvala što pratite”). Ne koriste se kao dokaz.
- Vreme prve reči posle pauze prepoznavanje razmazuje unapred. Prvu reč segmenta počni od izmerenog početka govora.

## Pomak audio toka

Telefonski MOV često ima audio tok koji počinje posle slike, na primer `start_time` od 0,21 ili 0,26 s. Vrednost se razlikuje od snimka do snimka, pa se svaki put meri. WAV izvučen za transkripciju taj pomak izgubi, pa su sva vremena iz prepoznavanja i tišina ranija za isti iznos.

Dodaj pomak pre rezanja i potvrdi ga unakrsnom korelacijom isečka izdvojenog po pts (`atrim`) sa WAV-om. Bez toga rez seče kraj reči.

## Ponovljene fraze

Prepoznavanje spaja ponovljenu frazu u jednu, pa transkript ne pokazuje dupli početak tejka.

Za svaki izabrani tejk uporedi gde počinje zvuk (energija u prozorima od 20 ms) i gde počinje prva prepoznata reč. Ako zvuk kreće 0,4 s ili više ranije, početak je verovatno ponovljen. Potvrdi bodovanjem kandidata i zadrži jedan neprekinut tejk.

## Bodovanje kandidata

Zamena za preslušavanje kada je reč nejasna. Primer za faster-whisper:

```python
from math import log
from faster_whisper.audio import pad_or_trim

feat = model.feature_extractor(audio)
enc = model.encode(pad_or_trim(feat))
res = model.model.align(enc, tok.sot_sequence, [tok.encode(" " + kandidat)], feat.shape[-1])[0]
skor = sum(log(max(p, 1e-9)) for p in res.text_token_probs)
```

Veći zbir znači verovatnije čitanje. Kod izjednačenja izaberi gramatički ispravno čitanje i označi mesto za proveru uhom.

- Boduj celu rečenicu, ne samo spornu reč. Kratak isečak ume da obrne presudu, na primer „pitaj” prema „pitaš”.
- Ako prepoznavanje vrati ne-reč, na primer „piteš”, izaberi najbližu stvarnu reč po bodovanju i označi je.
- Titl piše izgovoreni oblik, i kada je kolokvijalan: „upustvo”, „AI-u”. Ne normalizuj ga u standardni pravopis.
- Tejkovi iste rečenice umeju da se razlikuju po rečima („po upustvu” prema „po uputstvima”). Kada naslov ili poenta citiraju rečenicu, izaberi tejk čije reči odgovaraju i isti oblik koristi u oba. Ako nije jasno, pitaj.

## Rez

- Rukohvati: oko 0,12 s pre početka govora i oko 0,2 s posle poslednje reči.
- Posle reza izmeri RMS prvih i poslednjih 60 ms svakog segmenta. Mora biti na nivou šuma (oko −65 do −73 dBFS), inače produži segment.
- Granica tišine ume da izbaci kratku reč posle pauze, na primer „za baš … to” sa pauzom od 0,4 s. Za svaki segment pregledaj 1,2 s posle izlazne i pre ulazne tačke u prozorima od 20 ms. Sve iznad oko −45 dBFS tretiraj kao govor dok bodovanje ne pokaže drugačije.
- Uzastopne rečenice snimljene bez prekida spoji susednim opsezima izvora, bez mikro reza u pauzi.
- Pretapanje zvuka od 12 ms na svakom rezu.
- Glasnoća: linearno pojačanje do −14 LUFS, ograničeno true peakom od −1 dBTP, bez kompresora. Ako true peak ograniči pojačanje (na primer +6,1 dB do −18,8 LUFS), prijavi postignutu vrednost.
- Pauze iz scenarija, na primer 1 s pre poente, uzimaju se iz stvarnog snimka.
- Ako zvuk u originalu kasni za usnama (bežični mikrofon, oko 0,07 do 0,1 s), ostavi ga kao u originalu i prijavi.

## Poređenje sa titlovima

Pre prvog pregleda pokreni prepoznavanje govora nad isečenim zvukom programa i uporedi ga sa rečima titla, reč po reč. Svaka razlika je greška u rezu ili mesto za proveru uhom. Isto ponovi nad finalom.
