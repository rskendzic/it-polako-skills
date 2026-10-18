# Transkript i rez

## Transkript

- Jedan prolaz sa vremenima po rečima, na srpskom.
- Na macOS-u: `whisperkit-cli transcribe --language sr --use-prefill-prompt --word-timestamps`.
- U Linux okruženju isti model daje lokalni faster-whisper `large-v3-turbo` (int8).
- Jezik se zadaje izričito. Auto-detekcija na srpskom ume da vrati prevod.
- Početni prompt služi samo za pismo, na primer „Pišemo srpski latinicom: č, ć, š, ž, đ.” Tekst scenarija se nikad ne daje kao prompt.
- Isečci kraći od oko 1,5 s haluciniraju („Hvala što pratite”). Ne koriste se kao dokaz.
- Audio deli na delove do oko 60 s, po tišinama. Svaki prozor fraze pusti i posebno, sa promptom i bez njega, da se otkriju spojena ponavljanja.
- Titl piše ono što je rečeno, uključujući razgovorne oblike („upustvo”, „AI-u”), ne standardni pravopis i ne scenario. Nepostojeću reč iz prepoznavanja zameni najbližom stvarnom po bodovanju i označi je.
- Pre prvog pregleda pusti prepoznavanje nad audiom reza i uporedi ga reč po reč sa titlovima. Svaka razlika je greška ili mesto za proveru.
- `transcript/recorded.md`: tabela svake fraze iz snimka sa granicama u originalu (merenim energijom), oznakom upotrebljeno, neupotrebljeno ili lažan početak, označenim rečima i njihovim rešenjem, i tabela plan naspram snimka. Vremena reči su procena prepoznavanja; napiši to.

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

Veći zbir znači verovatnije čitanje. Boduj cele rečenice, jer kratak isečak može da preokrene presudu, na primer „pitaj” prema „pitaš”. Kod izjednačenja izaberi gramatički ispravno čitanje i označi mesto za proveru uhom.

Bodovanje nije slušanje. Oba tejka mogu ubedljivo da daju pogrešno čitanje. Za ključne reči napravi isečke od 2 do 4 s u `work/<agent>/review-clips/`, zamoli korisnika da ih presluša rano, nastavi rad dok sluša i tek onda zaključaj titlove.

## Kratka reč posle pauze

Granice po tišini umeju da izbace kratku reč posle pauze. Za svaki segment skeniraj 1,2 s posle izlaza i pre ulaza u prozorima od 20 ms. Sve iznad oko −45 dB tretiraj kao govor dok bodovanje ne kaže drugačije.

## Izbor tejkova

- Kompletan tejk bez ponavljanja unutra. Neprekinut tejk ima prednost nad rezom usred rečenice. Lica i gestove proveri na listu kadrova.
- Tejkovi mogu da se razlikuju u rečima. Kada hook ili poenta citiraju rečenicu, izaberi tejk čije reči odgovaraju i isti izgovoreni oblik koristi u hooku i poenti. Ako nije jasno, pitaj.
- Rečenice iz različitih tejkova smeju da se spoje na granici rečenice, po tekstu, energiji poslednje reči i pogledu u poslednjem frejmu.

## Rez

- Rukohvati: oko 0,12 s pre početka govora i oko 0,2 s posle poslednje reči.
- Posle reza izmeri RMS prvih i poslednjih 60 ms svakog segmenta. Mora biti na nivou šuma (oko −65 do −73 dBFS), inače produži segment.
- Rečenice snimljene jedna za drugom, sa kratkom prirodnom pauzom, uzimaju se kao neprekinut opseg, bez mikro reza. Pauza duža od oko 1 s unutar liste sme da se iseče na tišini.
- Pretapanje zvuka od 12 ms na svakom rezu.
- Glasnoća: linearno pojačanje do −14 LUFS, ograničeno true peakom od −1 dBTP, bez kompresora. Ako true peak ograniči pojačanje (na primer +6,1 dB do −18,8 LUFS), prijavi dostignutu vrednost. Pojačanje računaj ponovo kad god se segmenti promene.
- Kraj je miran: poslednji kadar ili kartica drži se oko 1 do 1,5 s posle poslednje reči.
- Pauze iz scenarija, na primer 1 s pre poente, uzimaju se iz stvarnog snimka.
- Ako zvuk u originalu kasni za usnama (bežični mikrofon, oko 0,07 do 0,1 s), ostavi ga kao u originalu i prijavi.
