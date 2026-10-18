# HLG postupak

Cilj: kodne vrednosti originalnog HLG BT.2020 snimka ostaju netaknute, a grafika se mapira u HLG prostor.

## Boje grafike

- Grafika se crta u sRGB, a boje se pretvaraju u HLG BT.2020 kodne vrednosti po BT.2408: SDR 100% odgovara HLG 75%, odnosno 203 cd/m² na ekranu od 1000 cd/m².
- `python3 scripts/hlg_boje.py boja '#FBD800' '#FFFFFF'`
- Bela daje 191/255, `#FBD800` daje (185, 176, 65), crna ostaje 0.
- Paletu pretvori jednom i crtaj direktno u tim vrednostima, bez pretvaranja piksela po frejmu.
- Svaki element (tekst, okvir, linija) slaže se `alpha_composite` malog isečka. Crtanje direktno po polu-providnom sloju probija oreole na ivicama.

## Kompozicija u ffmpeg-u

- Grafika ulazi kao RGBA, iz fajla ili kao sirovi tok kroz pipe.
- Filter: `scale=out_color_matrix=bt2020:out_range=tv,format=yuva420p10le`, pa `overlay=format=yuv420p10:eof_action=repeat`.
- Posle poslednjeg frejma grafike pošalji još jedan rezervni frejm. Sa `eof_action=pass` i tačno n frejmova poslednji frejm svakog dela izađe bez grafike.
- Provera: bela površina mora dati Y = 720, a `#FBD800` oko 655 (10-bit, ograničen opseg).

## Kodiranje

```text
-c:v libx265 -pix_fmt yuv420p10le -preset superfast -crf 14
-x265-params colorprim=bt2020:transfer=arib-std-b67:colormatrix=bt2020nc:range=limited
-color_primaries bt2020 -color_trc arib-std-b67 -colorspace bt2020nc -color_range tv
-tag:v hvc1 -frames:v N
```

- `-frames:v N` ide uvek. Overlay ume da ispusti jedan frejm viška na kraju, a posle spajanja delova to pomera zvuk.
- Svaki deo se traži po stvarnom pts-u videa iz liste paketa (prosečan fps je oko 30,003, ne 30), minus 5 ms, a zvuk se seče po istom pts-u. Segment kome se raspored menja usred rečenice renderuje se kao odvojeni delovi.
- Sa `bframes=0` u `-x265-params` annex-B delovi se spajaju sa `cat` i muksuju sa `-r 30`. Sa B-frejmovima sirovo spajanje počinje negativnim pts-om i gubi frejmove, pa tada ide kontejner po delu i concat demuxer uz `-c copy`.
- Annex-B deo može da se skrati bez gubitka (`-c copy -frames:v n-1 -f hevc`) i dopuni renderom jednog frejma. Nepromenjeni segmenti mogu da se koriste između verzija, posle brojanja frejmova.
- Ne spuštaj kvalitet ispod oko 20 Mb/s pre ponovnog kodiranja na platformi.
- Mux: AAC 256k i `-movflags +faststart+write_colr`.

## Pregled

- Pregled je u 1080×1920, kroz LUT HLG→SDR: `python3 scripts/hlg_boje.py lut pregled.cube`.
- Lanac: `zscale=w=1080:h=1920,format=gbrp16le,lut3d=pregled.cube,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709,zscale=m=bt709:r=limited,format=yuv420p`.
- Pregled ide u jednom prolazu sa istom grafikom, x264 sa `-bf 0`.
- Pre prvog pregleda složi grafiku preko SDR frejmova svakog rasporeda i pogledaj list ključnih trenutaka.
- Podrazumevano `zscale`/`tonemap` mapiranje HLG-a zatamni grafiku. Po njemu se ne sudi o bojama.
