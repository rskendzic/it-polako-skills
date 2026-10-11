# Mesečni finansijski presek

Zatvara prethodni mesec iz vaših bankovnih izvoda. Proverava da je pročitana svaka transakcija, razvrstava potrošnju, računa koliko vam realno ostaje svakog meseca i kaže da li vam plan štednje izlazi.

Ništa ne upisuje bez vašeg odobrenja, ne šalje i ne briše mejlove, ne loguje se u banku i ne daje investicione savete.

## Kako da počnete

Napišite:

```text
Postavi mi mesečni finansijski presek.
```

Ili u Claude Code-u: `/mesecni-finansijski-presek postavi`.

Kroz kratak razgovor dobijate:

1. **Config** — vaše banke, računi (samo poslednje 4 cifre), odakle stižu izvodi i kako se prepoznaje plata.
2. **Tabelu spremnosti** — šta je spremno, šta fali i šta da uradite prvo.
3. **Prvi presek** — čim ništa kritično ne fali.
4. **Ponudu za mesečni zakazani zadatak** — tek posle prvog uspešnog preseka.

## Šta je potrebno

| Šta | Kada | Zašto |
|---|---|---|
| Pristup mejlu (npr. Gmail) | ako izvodi stižu mejlom | da se izvodi sami prikupe; samo čitanje |
| Izvod iz aplikacije banke | ako banka ne šalje mejl | prilažete ga sami, svakog meseca |
| Folder | samo ako želite trajni zapis | gde se čuvaju mesečne note ili tabela |
| Zakazani zadatak | opciono | da se presek sam pokrene svakog meseca |

Bez foldera i bez Obsidiana sve radi — izveštaj ostaje u razgovoru.

## Gde živi config

| Imate | Config je |
|---|---|
| ništa, samo razgovor | u promptu zakazanog zadatka, ili ga nalepite kad tražite presek |
| folder (lokalni, Dropbox, iCloud) | `finansije.config.yaml` u tom folderu |
| repo ili Obsidian vault | `finansije.config.yaml` u korenu |

Config nikad ne ulazi u sam skill i ne deli se. Pun broj računa u njega ne ide — provera ga odbija.

## Šta možete da pitate

- „Zatvori septembar."
- „Koliko sam potrošio na gorivo ovog meseca?"
- „Da li mi izlazi štednja za cilj do marta?"
- „Proveri mi config."

## Zapis, ako ga želite

| Izbor | Šta nastaje |
|---|---|
| samo izveštaj (podrazumevano) | ništa se ne upisuje |
| markdown | mesečna nota u folderu |
| CSV | red po mesecu, za Excel, Numbers ili Google Sheets |
| Obsidian | nota sa linkovima u vašem vault-u |
