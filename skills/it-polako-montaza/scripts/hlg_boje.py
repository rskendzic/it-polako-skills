#!/usr/bin/env python3
"""HLG pomoćnik za IT Polako montažu, samo standardna biblioteka.

  python3 hlg_boje.py boja '#FBD800' '#FFFFFF'   # sRGB -> HLG BT.2020 kodne vrednosti (8-bit)
  python3 hlg_boje.py lut pregled.cube [--size 33] # 3D LUT HLG BT.2020 -> SDR BT.709 za pregled

Mapiranje prati ITU-R BT.2408: SDR bela (100%) = HLG 75% = 203 cd/m2 na ekranu od 1000 cd/m2.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

A, B, C = 0.17883277, 0.28466892, 0.55991073
GAMMA = 1.2
PEAK = 1000.0
REF_WHITE = 203.0
M709_TO_2020 = ((0.6274, 0.3293, 0.0433), (0.0691, 0.9195, 0.0114), (0.0164, 0.0880, 0.8956))
M2020_TO_709 = ((1.6605, -0.5876, -0.0728), (-0.1246, 1.1329, -0.0083), (-0.0182, -0.1006, 1.1187))
Y2020 = (0.2627, 0.6780, 0.0593)


def _srgb_to_linear(value: float) -> float:
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def _oetf(e: float) -> float:
    e = max(e, 0.0)
    return math.sqrt(3 * e) if e <= 1 / 12 else A * math.log(12 * e - B) + C


def _inverse_oetf(v: float) -> float:
    return v * v / 3 if v <= 0.5 else (math.exp((v - C) / A) + B) / 12


def _mul(matrix, vector):
    return tuple(sum(matrix[i][j] * vector[j] for j in range(3)) for i in range(3))


def parse_hex(text: str) -> tuple[int, int, int]:
    value = text.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Boja mora biti #RRGGBB: {text}")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def srgb_to_hlg(rgb: tuple[int, int, int], gain: float = 1.0) -> tuple[int, int, int]:
    """sRGB (0-255) -> HLG BT.2020 kodne vrednosti (0-255), SDR bela na 75% HLG signala."""
    linear = tuple(_srgb_to_linear(c / 255) for c in rgb)
    display = tuple(REF_WHITE / PEAK * gain * c for c in _mul(M709_TO_2020, linear))
    yd = sum(k * c for k, c in zip(Y2020, display))
    if yd <= 0:
        return (0, 0, 0)
    ys = yd ** (1 / GAMMA)
    scene = tuple(c / ys ** (GAMMA - 1) for c in display)
    return tuple(int(round(min(1.0, _oetf(e)) * 255)) for e in scene)  # type: ignore[return-value]


def _knee(x: float, start: float = 0.8) -> float:
    return x if x <= start else start + (1 - start) * (1 - math.exp(-(x - start) / (1 - start)))


def hlg_to_sdr(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    """HLG BT.2020 signal (0-1) -> SDR BT.709 signal (0-1), BT.1886 gama 2.4, meko koleno."""
    scene = tuple(_inverse_oetf(c) for c in rgb)
    ys = sum(k * c for k, c in zip(Y2020, scene))
    if ys <= 0:
        return (0.0, 0.0, 0.0)
    display = tuple(PEAK * ys ** (GAMMA - 1) * c / REF_WHITE for c in scene)
    linear = tuple(max(0.0, c) for c in _mul(M2020_TO_709, display))
    return tuple(_knee(c) ** (1 / 2.4) for c in linear)  # type: ignore[return-value]


def write_lut(path: Path, size: int = 33) -> None:
    lines = ['TITLE "HLG BT.2020 -> SDR BT.709 (pregled)"', f"LUT_3D_SIZE {size}"]
    step = size - 1
    for b in range(size):
        for g in range(size):
            for r in range(size):
                out = hlg_to_sdr((r / step, g / step, b / step))
                lines.append("%.6f %.6f %.6f" % out)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    boja = sub.add_parser("boja", help="sRGB hex -> HLG kodne vrednosti")
    boja.add_argument("hex", nargs="+")
    lut = sub.add_parser("lut", help="napiši HLG->SDR .cube za pregled")
    lut.add_argument("out")
    lut.add_argument("--size", type=int, default=33)
    args = parser.parse_args(argv)
    if args.cmd == "boja":
        for text in args.hex:
            print(text, srgb_to_hlg(parse_hex(text)))
    else:
        write_lut(Path(args.out), args.size)
        print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
