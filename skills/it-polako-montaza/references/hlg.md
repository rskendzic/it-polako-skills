# HLG postupak

Cilj: kodne vrednosti originalnog HLG BT.2020 snimka ostaju netaknute, a grafika se mapira u HLG prostor.

## Boje grafike

- Grafika se crta u sRGB, a boje se pretvaraju u HLG BT.2020 kodne vrednosti po BT.2408: SDR 100% odgovara HLG 75%, odnosno 203 cd/m² na ekranu od 1000 cd/m².
- `python3 scripts/hlg_boje.py boja '#FBD800' '#FFFFFF'`
- Bela daje 191/255, `#FBD800` daje (185, 176, 65), crna ostaje 0.
- Boje palete pretvori jednom i crtaj direktno tim vrednostima, bez pretvaranja piksel po piksel u svakom frejmu.

## Kompozicija u ffmpeg-u

- Grafika ulazi kao RGBA, iz fajla ili kao sirovi tok kroz pipe.
- Filter: `scale=out_color_matrix=bt2020:out_range=tv,format=yuva420p10le`, pa `overlay=format=yuv420p10`.
- Provera: bela površina mora dati Y = 720, a `#FBD800` oko 655 (10-bit, ograničen opseg).

## Kodiranje

```text
-c:v libx265 -pix_fmt yuv420p10le -preset superfast -crf 14
-x265-params colorprim=bt2020:transfer=arib-std-b67:colormatrix=bt2020nc:range=limited
-color_primaries bt2020 -color_trc arib-std-b67 -colorspace bt2020nc -color_range tv
-tag:v hvc1 -frames:v N
```

- `-frames:v N` ide uvek. Overlay ume da ispusti jedan frejm viška na kraju, a posle spajanja delova to pomera zvuk.
- Svaki deo traži početni frejm po stvarnom pts-u iz liste paketa, jer prosečan fps telefona nije tačno 30 (na primer 30,003). Zvuk se seče po istom pts-u.
- Delovi se spajaju concat demuxer-om uz `-c copy`. Sa `bframes=0` sirovi HEVC delovi mogu i da se nadovežu i muxuju uz `-r 30`. Sa B-frejmovima sirovo nadovezivanje počinje negativnim pts-om, a frejmovi nestaju iza edit liste.
- Mux: AAC 256k i `-movflags +faststart+write_colr`.

## Pregled

- Pregled je u 1080×1920, kroz LUT HLG→SDR: `python3 scripts/hlg_boje.py lut pregled.cube`.
- Lanac: `zscale=w=1080:h=1920,format=gbrp16le,lut3d=pregled.cube,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709,zscale=m=bt709:r=limited,format=yuv420p`.
- Podrazumevano `zscale`/`tonemap` mapiranje HLG-a zatamni grafiku. Po njemu se ne sudi o bojama.
- SDR prolaz pregleda je spor (oko 2 minuta za 50 s klipa na četiri ARM jezgra) i ide u zaseban poziv.
