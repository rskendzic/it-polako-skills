# Rad u ograničenom okruženju

Važi kada agent radi iz izolovanog Linux okruženja povezanog sa korisnikovim računarom, sa vremenski ograničenim pozivima i malo memorije.

- Proveri koliko traje jedan poziv i da li pozadinski procesi preživljavaju kraj poziva. `nohup` i `setsid` ne pomažu ako okruženje gasi sve procese poziva. Svaki dugačak posao deli se na delove koji staju u jedan poziv i mogu da se nastave: piši u `.part` fajl, pa preimenuj.
- Više 4K HEVC ulaza u jednoj ffmpeg komandi lako potroši 3 GB memorije. Pokreći jedan segment po komandi, u delovima do oko 75 frejmova, i spoji ih na kraju.
- Ako alat za prenos fajlova kasni ili tiho zadrži stariju kopiju, svaku novu verziju skripte šalji pod novim imenom i pre pokretanja proveri njen md5 na odredištu.
- Brisanje može biti zabranjeno, a prepisivanje i preimenovanje preko postojećeg fajla obično rade. Sve pomoćne fajlove drži u sopstvenom radnom podfolderu, sa verzionisanim folderima umesto brisanja.
- Servisi na `127.0.0.1` korisnikovog računara, na primer WhisperKit server, nisu dostupni iz izolovanog okruženja. Zamoli korisnika da pokrene komandu i ostavi JSON u projektu, ili uz njegovu saglasnost koristi lokalnu alternativu.
- Okvirna brzina: x265 `superfast` na četiri ARM jezgra kodira oko 1,3 do 1,5 frejma u sekundi za 2160×3840, kadrove sa panelom brže. Novi deo počni samo ako je ostalo dovoljno vremena u pozivu.
- Veliki modeli sa HuggingFace-a: `curl -L -C -` kroz više poziva. `snapshot_download` ume da zastane i ostavi `.incomplete` fajlove.
- Pregled na korisnikovom računaru: lokalni fajl otvoren u pregledaču pušta video sa zvukom, a tok se prati snimcima ekrana. Dozvole za ekran ističu posle neaktivnosti, a snimak ekrana ne radi dok ekran spava. Navedi u izveštaju ako final nije viđen na računaru.
