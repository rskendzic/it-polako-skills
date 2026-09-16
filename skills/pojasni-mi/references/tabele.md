# Tabele

Primeni na CSV, XLSX i druge tabelarne izvore.

## Očuvaj

- originalne nazive kolona i opseg ćelija;
- jedinice, valutu, procenat i vremenski period;
- razliku između unosa, formule i izvedenog rezultata;
- praznu vrednost, nulu i nedostajući podatak kao različita stanja;
- relacije među kolonama i listovima.

## Provere

- proveri zbir, procenat i red veličine nezavisnim proračunom;
- označi skrivene/redigovane kolone ili filtre kada su poznati;
- ne pretvaraj približnu vrednost u preciznu;
- ne nagađaj formulu iz samo jednog rezultata.

## What-if

Koristi samo proverenu formulu ili ograničeni model koji je jasno označen. U strukturiranom ulazu za renderer koristi `kind: number` sa linearnim `factor` i `offset` samo kada izvor zaista podržava taj odnos. U svim drugim slučajevima koristi `kind: choice` sa diskretnim scenarijima.
