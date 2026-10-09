# Rad u ograničenom okruženju

Važi kada agent radi iz izolovanog Linux okruženja povezanog sa korisnikovim računarom, sa vremenski ograničenim pozivima i malo memorije.

- Proveri koliko traje jedan poziv i da li pozadinski procesi preživljavaju kraj poziva. Ako ne preživljavaju, svaki dugačak posao deli se na delove koji staju u jedan poziv i mogu da se nastave: piši u `.part` fajl, pa preimenuj.
- Više 4K HEVC ulaza u jednoj ffmpeg komandi lako potroši 3 GB memorije. Pokreći jedan segment po komandi, u delovima do oko 75 frejmova, i spoji ih na kraju.
- Ako alat za prenos fajlova kasni, pre pokretanja skripte proveri njen md5 na odredištu.
- Brisanje može biti zabranjeno. Sve pomoćne fajlove drži u sopstvenom radnom podfolderu.
- Servisi na `127.0.0.1` korisnikovog računara, na primer WhisperKit server, nisu dostupni iz izolovanog okruženja. Zamoli korisnika da pokrene komandu i ostavi JSON u projektu, ili uz njegovu saglasnost koristi lokalnu alternativu.
- Okvirna brzina: x265 `superfast` na četiri ARM jezgra kodira oko 1,3 frejma u sekundi za 2160×3840.
