# Rad u ograničenom okruženju

Važi kada agent radi iz izolovanog Linux okruženja povezanog sa korisnikovim računarom, sa vremenski ograničenim pozivima i malo memorije.

- Proveri koliko traje jedan poziv i da li pozadinski procesi preživljavaju kraj poziva. `nohup` i `setsid` ne pomažu ako okruženje gasi sve procese poziva. Ako ne preživljavaju, svaki dugačak posao deli se na delove koji staju u jedan poziv i mogu da se nastave: piši u `.part` fajl, pa preimenuj.
- Dobro radi skripta koja preskače završene delove i ne pokreće nov deo kada je prošlo oko 95 s poziva.
- `cd X && cmd &` šalje i `cd` u pozadinu.
- Više 4K HEVC ulaza u jednoj ffmpeg komandi lako potroši 3 GB memorije. Pokreći jedan segment po komandi, u delovima do oko 75 frejmova, i spoji ih na kraju.
- Ako alat za prenos fajlova kasni, pre pokretanja skripte proveri njen md5 na odredištu. Svaku novu verziju prenosi pod novim imenom (`gfx3.py`, `gfx9/`), jer prenos ume da zadrži stariju kopiju bez upozorenja.
- Brisanje može biti zabranjeno, a presnimavanje i preimenovanje preko postojećeg fajla rade. Sve pomoćne fajlove drži u sopstvenom radnom podfolderu, u verzionisanim folderima umesto brisanja. Zamenjene finale premesti u `work/<agent>/rejected/`, da `output/` drži jedan aktuelan final.
- Veliki modeli se skidaju sa `curl -L -C -` u više poziva (`snapshot_download` ume da zastane i ostavi `.incomplete` fajlove) i čuvaju na disku projekta, ne u malom home folderu okruženja.
- Veza sa računarom ume da padne na minut. Drži kod i u okruženju agenta da rad ne stane.
- Servisi na `127.0.0.1` korisnikovog računara, na primer WhisperKit server, nisu dostupni iz izolovanog okruženja. Zamoli korisnika da pokrene komandu i ostavi JSON u projektu, ili uz njegovu saglasnost koristi lokalnu alternativu.
- Okvirna brzina: x265 `superfast` na četiri ARM jezgra kodira oko 1,3 do 1,5 frejma u sekundi za 2160×3840, kadrove sa panelom brže. Novi deo počni samo ako je ostalo dovoljno vremena u pozivu.
- Pregled na korisnikovom računaru: lokalni fajl otvoren u pregledaču pušta video sa zvukom, a tok se prati snimcima ekrana. Dozvole za ekran ističu posle neaktivnosti, a snimak ekrana ne radi dok ekran spava. Navedi u izveštaju ako final nije viđen na računaru.
