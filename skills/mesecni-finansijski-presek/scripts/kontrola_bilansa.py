#!/usr/bin/env python3
"""
Kontrola bilansa bankovnog izvoda.

Skript potvrđuje da su pročitane SVE transakcije. Nije dovoljno da računica
zaglavlja izlazi — zaglavlje banke je skoro uvek tačno, i njegova provera
ne govori ništa o tome šta je parsiranje propustilo. Zato se zbirovi iz
zaglavlja nikad ne koriste umesto parsiranih, nego se sa njima porede.

Provere, sve obavezne za status PROSLA:

  1. lanac      jedan neprekinut lanac stanja: od početnog stanja iz
                zaglavlja, kroz svaku transakciju (stanje = prethodno ±
                iznos), do završnog stanja iz zaglavlja
  2. promet     zbir parsiranih isplata i uplata = isplate i uplate iz
                zaglavlja
  3. zaglavlje  početno − isplate + uplate = završno, sve iz zaglavlja

Lanac kreće od početnog stanja iz zaglavlja, ne od prvog pročitanog
stanja. Ako je prva transakcija ispala, ili je red početnog stanja
nečitljiv, prvi korak lanca to otkriva.

Statusi i izlazni kodovi:
  0  PROSLA      sve tri provere prošle
  1  NIJE PROSLA bar jedna provera je pala — ne radi presek
  2  greška ulaza
  3  NEPOTPUNA   kontrola nije mogla da se izvrši do kraja: nedostaje
                 zaglavlje, ili kolona stanja nije potvrđena. Ne radi
                 presek; ovo nije uspeh.

Kad kolona stanja nije potvrđena (mnogo redova se ne slaže sa svojim
iznosom), skript ne prelazi tiho u „izvod bez salda". Loše parsiranje i
izvod bez salda izgledaju isto, i ne sme se pogoditi koje je. Status je
NEPOTPUNA, a format potvrđuje čovek ili agent gledajući izvod.

Za izvod koji zaista nema kolonu stanja (tipično kartični), pokreni sa
--bez-kolone-stanja posle tog pogleda. Lanca tada nema; promet se sabira
iz redova sa datumom, po dve najdešnje kolone iznosa (isplate, uplate),
i mora se poklopiti sa zaglavljem. PROSLA tada znači: zaglavlje i promet
se slažu. Izveštaj mora reći da lanac nije bio moguć.

Ulaz je izlaz `pdftotext -layout izvod.pdf izvod.txt`. Kolone se nalaze
po horizontalnoj poziciji iznosa — kolona najdalje desno je tekuće stanje.
`-raw` gubi pozicije i sa njim ovo ne radi.

Primeri:
    python3 kontrola_bilansa.py izvod.txt \\
        --pocetno 100000 --zavrsno 167716.19 --isplate 32634.56 --uplate 100350.75
    python3 kontrola_bilansa.py izvod.txt --config finansije.config.yaml ... --json

Sa --config, format brojeva (lokalizacija.decimalni_separator) i tolerancija
(izvestaj.tolerancija) uzimaju se iz config-a. Argument na komandnoj liniji
ima prednost.
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field

# 1.234,56 / 1234,56 / -1.234,56 — zapeta kao decimalni separator
RE_ZAPETA = re.compile(r'-?\d{1,3}(?:\.\d{3})*,\d{2}|-?\d+,\d{2}')
# 1,234.56 / 1234.56 — tačka kao decimalni separator
RE_TACKA = re.compile(r'-?\d{1,3}(?:,\d{3})*\.\d{2}|-?\d+\.\d{2}')

# nedvosmisleni oblici: samo jedan od dva formata ih može proizvesti
RE_DOKAZ_ZAPETA = re.compile(r'\d\.\d{3},\d{2}')   # 1.234,56
RE_DOKAZ_TACKA = re.compile(r'\d,\d{3}\.\d{2}')    # 1,234.56

PRAG_POTVRDE_KOLONE = 0.8   # udeo redova sa stanjem koji se moraju slagati

STATUS_KOD = {'prosla': 0, 'nije_prosla': 1, 'nepotpuna': 3}
STATUS_TEKST = {
    'prosla': 'PROSLA',
    'nije_prosla': 'NIJE PROSLA — ne radi presek dok se ne razreši',
    'nepotpuna': 'NEPOTPUNA — kontrola nije izvršena do kraja; ne radi presek',
}


def otkrij_format(tekst):
    """Vrati (True ako je zapeta decimalni separator, obrazloženje).

    Pogrešno pogođen format ne prijavi grešku — tiho pročita druge brojeve
    (iz 595,710.08 izvuče 595,71). Zato se format meri: broje se oblici koje
    može proizvesti samo jedan od dva formata.
    """
    z = len(RE_DOKAZ_ZAPETA.findall(tekst))
    t = len(RE_DOKAZ_TACKA.findall(tekst))
    if z == t == 0:
        nz, nt = len(RE_ZAPETA.findall(tekst)), len(RE_TACKA.findall(tekst))
        if nz >= nt:
            return True, f'bez četvorocifrenih iznosa; 1.234,56 ({nz} vs {nt})'
        return False, f'bez četvorocifrenih iznosa; 1,234.56 ({nt} vs {nz})'
    if z >= t:
        return True, f'1.234,56 ({z} dokaza naspram {t})'
    return False, f'1,234.56 ({t} dokaza naspram {z})'


def u_broj(s, decimalna_zapeta=True):
    s = s.strip()
    if decimalna_zapeta:
        return float(s.replace('.', '').replace(',', '.'))
    return float(s.replace(',', ''))


def formatiraj(x, decimalna_zapeta=True):
    if x is None:
        return '—'
    s = f'{x:,.2f}'
    if decimalna_zapeta:
        s = s.replace(',', '\x00').replace('.', ',').replace('\x00', '.')
    return s


@dataclass
class Iznos:
    vrednost: float
    kraj: int          # kolona u kojoj se iznos završava (desno poravnanje)


@dataclass
class Red:
    broj_linije: int
    tekst: str
    iznosi: list
    stanje: float = None
    kandidati: list = field(default_factory=list)   # iznosi koji nisu stanje


def procitaj(tekst, decimalna_zapeta=True):
    rx = RE_ZAPETA if decimalna_zapeta else RE_TACKA
    redovi = []
    for i, linija in enumerate(tekst.splitlines(), 1):
        iznosi = [Iznos(u_broj(m.group(), decimalna_zapeta), m.end())
                  for m in rx.finditer(linija)]
        if iznosi:
            redovi.append(Red(i, linija, iznosi))
    return redovi


def grupisi_kolone(krajevi, razmak=4):
    grupe = []
    for k in sorted(krajevi):
        if grupe and k - grupe[-1][-1] <= razmak:
            grupe[-1].append(k)
        else:
            grupe.append([k])
    return grupe


def nadji_kolonu_stanja(redovi, prag=0.55):
    """Najdešnja kolona koja se javlja u većini redova sa više iznosa.
    Meri se kraj iznosa u liniji, jer su brojevi desno poravnati."""
    visestruki = [r for r in redovi if len(r.iznosi) >= 2]
    if not visestruki:
        return None
    grupe = grupisi_kolone([iz.kraj for r in visestruki for iz in r.iznosi])
    for g in reversed(grupe):
        if len(g) >= prag * len(visestruki):
            return sum(g) / len(g)
    return None


def dodeli_stanja(redovi, kolona, tolerancija_kolone=3):
    """Iznos u koloni stanja je stanje — i kad je jedini iznos u redu, kao
    kod reda početnog stanja ili prenosa sa prethodne strane."""
    for r in redovi:
        u_koloni = [iz for iz in r.iznosi
                    if abs(iz.kraj - kolona) <= tolerancija_kolone]
        if u_koloni:
            stanje = max(u_koloni, key=lambda iz: iz.kraj)
            r.stanje = stanje.vrednost
            r.kandidati = [iz.vrednost for iz in r.iznosi if iz is not stanje]
        else:
            r.kandidati = [iz.vrednost for iz in r.iznosi]
    return redovi


def je_zbirni(red, zaglavlje_iznosi, tolerancija):
    """Zbirni red (zaglavlje, podnožje, rekapitulacija) nosi bar dva iznosa
    iz zaglavlja. Takav red ne sme u lanac: njegov zbir uplata bi
    „objasnio" skok stanja i prikrio transakciju koja je ispala."""
    pogodaka = sum(1 for k in red.kandidati
                   if any(abs(k - z) <= tolerancija for z in zaglavlje_iznosi))
    return pogodaka >= 2


def lanac(redovi, pocetno, zavrsno, tolerancija, zaglavlje_iznosi=()):
    """Jedan lanac: početno (zaglavlje) → svako pročitano stanje → završno
    (zaglavlje). Promena stanja mora odgovarati iznosu u istom redu."""
    sa_stanjem = [r for r in redovi if r.stanje is not None]
    zbirni = [r for r in sa_stanjem if je_zbirni(r, zaglavlje_iznosi, tolerancija)]
    sa_stanjem = [r for r in sa_stanjem if r not in zbirni]
    koraci, greske = 0, []
    isplate = uplate = 0.0
    prethodno = pocetno
    for r in sa_stanjem:
        if prethodno is None:
            prethodno = r.stanje
            continue
        delta = round(r.stanje - prethodno, 2)
        if abs(delta) <= tolerancija:
            prethodno = r.stanje      # ponovljeno stanje: početno, prenos
            continue
        koraci += 1
        if any(abs(abs(delta) - abs(k)) <= tolerancija for k in r.kandidati):
            if delta < 0:
                isplate += -delta
            else:
                uplate += delta
        else:
            greske.append({
                'linija': r.broj_linije,
                'prethodno_stanje': prethodno,
                'stanje': r.stanje,
                'razlika': delta,
                'iznosi_u_redu': r.kandidati,
                'tekst': r.tekst.strip()[:110],
            })
        prethodno = r.stanje
    kraj_razlika = None
    if zavrsno is not None and prethodno is not None:
        kraj_razlika = round(zavrsno - prethodno, 2)
    return {
        'redova_sa_stanjem': len(sa_stanjem),
        'zbirnih_redova_preskoceno': [r.broj_linije for r in zbirni],
        'koraka': koraci,
        'neuspelo': len(greske),
        'greske': greske,
        'parsirane_isplate': round(isplate, 2),
        'parsirane_uplate': round(uplate, 2),
        'poslednje_procitano_stanje': prethodno,
        'razlika_do_zavrsnog': kraj_razlika,
    }


RE_DATUM = re.compile(r'\b\d{1,2}\.\s?\d{1,2}\.\s?(?:\d{4}|\d{2})\b|\b\d{4}-\d{2}-\d{2}\b')


def promet_iz_kolona(redovi, kolona_stanja):
    """Za izvod bez kolone stanja: dve najdešnje kolone iznosa su isplate i
    uplate (ili samo jedna, iznos). Broje se samo redovi sa datumom, da
    zbirni redovi iz zaglavlja i podnožja ne uđu dvaput.
    Vraća (isplate, uplate, broj_iznosa)."""
    redovi = [r for r in redovi if RE_DATUM.search(r.tekst)]
    krajevi = [iz.kraj for r in redovi for iz in r.iznosi]
    grupe = grupisi_kolone(krajevi)
    if kolona_stanja is not None:
        grupe = [g for g in grupe if abs(sum(g) / len(g) - kolona_stanja) > 3]
    if not grupe:
        return None
    centri = [sum(g) / len(g) for g in grupe[-2:]]
    isplate = uplate = 0.0
    n = 0
    for r in redovi:
        for iz in r.iznosi:
            if abs(iz.kraj - centri[0]) <= 3:
                isplate += abs(iz.vrednost)
                n += 1
            elif len(centri) > 1 and abs(iz.kraj - centri[1]) <= 3:
                uplate += abs(iz.vrednost)
                n += 1
    return round(isplate, 2), round(uplate, 2), n


def proveri(tekst, decimalna_zapeta, pocetno, zavrsno, isplate, uplate,
            tolerancija=0.01, bez_kolone_stanja=False):
    redovi = procitaj(tekst, decimalna_zapeta)
    if not redovi:
        raise ValueError('nijedan iznos nije pronađen. Da li je fajl '
                         'napravljen sa `pdftotext -layout`?')

    zaglavlje = {'pocetno': pocetno, 'zavrsno': zavrsno,
                 'isplate': isplate, 'uplate': uplate}
    nedostaje = [k for k, v in zaglavlje.items() if v is None]
    provere, razlozi = [], []

    def dodaj(naziv, prosla, detalj):
        provere.append({'naziv': naziv, 'prosla': prosla, 'detalj': detalj})

    # 3. zaglavlje — samo računica banke
    if not nedostaje:
        ocek = round(pocetno - isplate + uplate, 2)
        r = round(ocek - zavrsno, 2)
        dodaj('zaglavlje', abs(r) <= tolerancija,
              {'ocekivano_zavrsno': ocek, 'razlika': r})
    else:
        razlozi.append('nedostaju iznosi iz zaglavlja: ' + ', '.join(nedostaje)
                       + ' — bez njih nema nezavisne provere')

    kolona = nadji_kolonu_stanja(redovi)
    lanac_rez = None
    if kolona is not None and not bez_kolone_stanja:
        dodeli_stanja(redovi, kolona)
        lanac_rez = lanac(redovi, pocetno, zavrsno, tolerancija,
                          [v for v in (pocetno, isplate, uplate) if v is not None])
        n = lanac_rez['koraka']
        udeo = (n - lanac_rez['neuspelo']) / n if n else 0.0
        if n == 0:
            razlozi.append('nijedna transakcija nije pročitana u koloni stanja')
        else:
            if udeo < PRAG_POTVRDE_KOLONE:
                # Mnogo neslaganja: ili loše parsiranje, ili izvod bez salda.
                # Ne pogađa se koje — lanac pada, a format potvrđuje čovek.
                razlozi.append(
                    f'kolona stanja nije potvrđena: slaže se {udeo:.0%} koraka. '
                    'Ili je parsiranje loše, ili izvod nema kolonu stanja — '
                    'pogledaj izvod; ako nema saldo po redu, pokreni sa '
                    '--bez-kolone-stanja')
            # 1. lanac
            kraj_ok = (lanac_rez['razlika_do_zavrsnog'] is not None and
                       abs(lanac_rez['razlika_do_zavrsnog']) <= tolerancija)
            if pocetno is None or zavrsno is None:
                if lanac_rez['neuspelo']:
                    dodaj('lanac', False, {
                        'koraka': n, 'neuspelo': lanac_rez['neuspelo'],
                        'razlika_do_zavrsnog': None})
                razlozi.append('lanac nije usidren: treba --pocetno i --zavrsno')
            else:
                dodaj('lanac', lanac_rez['neuspelo'] == 0 and kraj_ok, {
                    'koraka': n, 'neuspelo': lanac_rez['neuspelo'],
                    'razlika_do_zavrsnog': lanac_rez['razlika_do_zavrsnog']})
            # 2. promet
            pi, pu = lanac_rez['parsirane_isplate'], lanac_rez['parsirane_uplate']
            if isplate is not None and uplate is not None:
                ri, ru = round(pi - isplate, 2), round(pu - uplate, 2)
                dodaj('promet', abs(ri) <= tolerancija and abs(ru) <= tolerancija,
                      {'parsirane_isplate': pi, 'parsirane_uplate': pu,
                       'razlika_isplate': ri, 'razlika_uplate': ru})
    else:
        if not bez_kolone_stanja:
            razlozi.append('kolona stanja nije pronađena — pogledaj izvod; ako '
                           'nema saldo po redu, pokreni sa --bez-kolone-stanja')
        else:
            p = promet_iz_kolona(redovi, None)   # potvrđeno: kolone stanja nema
            if p is None:
                razlozi.append('kolone isplata i uplata nisu pronađene')
            elif isplate is None or uplate is None:
                razlozi.append('za izvod bez stanja treba --isplate i --uplate')
            else:
                pi, pu, n = p
                ri, ru = round(pi - isplate, 2), round(pu - uplate, 2)
                dodaj('promet', abs(ri) <= tolerancija and abs(ru) <= tolerancija,
                      {'parsirane_isplate': pi, 'parsirane_uplate': pu,
                       'razlika_isplate': ri, 'razlika_uplate': ru,
                       'iznosa': n})
            if p is not None:
                razlozi_lanac = ('lanac nije moguć: izvod nema kolonu stanja; '
                                 'potpunost potvrđuje samo promet')
                provere.append({'naziv': 'lanac', 'prosla': None,
                                'detalj': razlozi_lanac})

    pale = [p for p in provere if p['prosla'] is False]
    if pale:
        status = 'nije_prosla'
    elif razlozi:
        status = 'nepotpuna'
    elif bez_kolone_stanja and all(
            p['prosla'] for p in provere if p['naziv'] != 'lanac'):
        status = 'prosla'
    elif {p['naziv'] for p in provere if p['prosla']} >= {'lanac', 'promet', 'zaglavlje'}:
        status = 'prosla'
    else:
        status = 'nepotpuna'
        razlozi.append('nisu izvršene sve tri provere')

    return {
        'status': status,
        'prosla': status == 'prosla',
        'provere': provere,
        'razlozi_nepotpune': razlozi,
        'zaglavlje': zaglavlje,
        'kolona_stanja': kolona,
        'lanac': lanac_rez,
        'bez_kolone_stanja': bez_kolone_stanja,
    }


def ucitaj_config(putanja):
    if putanja == '-':
        tekst = sys.stdin.read()
    else:
        with open(putanja, encoding='utf-8') as f:
            tekst = f.read()
    try:
        import yaml
        return yaml.safe_load(tekst) or {}
    except ImportError:
        return json.loads(tekst)   # JSON radi i bez PyYAML-a


def main():
    ap = argparse.ArgumentParser(
        description='Kontrola bilansa bankovnog izvoda (pdftotext -layout izlaz).')
    ap.add_argument('fajl', help='tekstualni izvod iz `pdftotext -layout`')
    ap.add_argument('--pocetno', type=float, help='početno stanje, iz zaglavlja')
    ap.add_argument('--zavrsno', type=float, help='završno stanje, iz zaglavlja')
    ap.add_argument('--isplate', type=float, help='ukupne isplate, iz zaglavlja')
    ap.add_argument('--uplate', type=float, help='ukupne uplate, iz zaglavlja')
    ap.add_argument('--bez-kolone-stanja', action='store_true',
                    help='izvod nema saldo po redu (potvrđeno pogledom na izvod)')
    ap.add_argument('--tolerancija', type=float, default=None,
                    help='dopuštena razlika u jedinicama valute (podrazumevano 0.01)')
    ap.add_argument('--config', help='finansije.config.yaml (ili - za standardni '
                                     'ulaz) — format brojeva i tolerancija')
    ap.add_argument('--decimalna-zapeta', choices=['da', 'ne', 'auto'],
                    default=None,
                    help='da: 1.234,56 | ne: 1,234.56 | auto: otkrij iz fajla')
    ap.add_argument('--json', action='store_true', help='izlaz kao JSON')
    a = ap.parse_args()

    if a.config:
        try:
            cfg = ucitaj_config(a.config)
        except Exception as e:
            print(f'GREŠKA: ne mogu da pročitam config {a.config}: {e}',
                  file=sys.stderr)
            return 2
        ds = (cfg.get('lokalizacija') or {}).get('decimalni_separator')
        if a.decimalna_zapeta is None and ds in (',', '.'):
            a.decimalna_zapeta = 'da' if ds == ',' else 'ne'
        tol = (cfg.get('izvestaj') or {}).get('tolerancija')
        if a.tolerancija is None and isinstance(tol, (int, float)):
            a.tolerancija = float(tol)
    tolerancija = 0.01 if a.tolerancija is None else a.tolerancija

    try:
        with open(a.fajl, encoding='utf-8', errors='replace') as f:
            tekst = f.read()
    except OSError as e:
        print(f'GREŠKA: ne mogu da pročitam {a.fajl}: {e}', file=sys.stderr)
        return 2

    obrazlozenje = None
    if a.decimalna_zapeta in (None, 'auto'):
        dz, obrazlozenje = otkrij_format(tekst)
    else:
        dz = a.decimalna_zapeta == 'da'

    try:
        rez = proveri(tekst, dz, a.pocetno, a.zavrsno, a.isplate, a.uplate,
                      tolerancija, a.bez_kolone_stanja)
    except ValueError as e:
        print(f'GREŠKA: {e}', file=sys.stderr)
        return 2
    rez['format_brojeva'] = 'zapeta' if dz else 'tacka'

    if a.json:
        print(json.dumps(rez, ensure_ascii=False, indent=2))
        return STATUS_KOD[rez['status']]

    f = lambda x: formatiraj(x, dz)
    print(f'Fajl: {a.fajl}')
    if obrazlozenje:
        print(f'Format brojeva: {obrazlozenje}')
    l = rez['lanac']
    if l:
        print(f'Redova sa stanjem: {l["redova_sa_stanjem"]}, koraka lanca: {l["koraka"]}')
        if l['zbirnih_redova_preskoceno']:
            print(f'Zbirni redovi van lanca (linije): {l["zbirnih_redova_preskoceno"]}')
    print()
    for p in rez['provere']:
        oznaka = {True: 'OK  ', False: 'PALA', None: '—   '}[p['prosla']]
        d = p['detalj']
        if p['naziv'] == 'zaglavlje':
            opis = (f'početno − isplate + uplate = {f(d["ocekivano_zavrsno"])}, '
                    f'razlika {f(d["razlika"])}')
        elif p['naziv'] == 'lanac' and isinstance(d, dict):
            opis = (f'{d["koraka"]} koraka, neuspelo {d["neuspelo"]}, '
                    f'do završnog stanja fali {f(d["razlika_do_zavrsnog"])}')
        elif p['naziv'] == 'promet':
            opis = (f'parsirano isplate {f(d["parsirane_isplate"])} '
                    f'(razlika {f(d["razlika_isplate"])}), uplate '
                    f'{f(d["parsirane_uplate"])} (razlika {f(d["razlika_uplate"])})')
        else:
            opis = str(d)
        print(f'  [{oznaka}] {p["naziv"]}: {opis}')
    if l and l['greske']:
        print('\n  Koraci koji se ne slažu:')
        for g in l['greske'][:25]:
            print(f'    linija {g["linija"]}: {f(g["prethodno_stanje"])} -> '
                  f'{f(g["stanje"])}, razlika {f(g["razlika"])}, '
                  f'iznosi u redu {[f(k) for k in g["iznosi_u_redu"]]}')
            print(f'      {g["tekst"]}')
        if len(l['greske']) > 25:
            print(f'    ... i još {len(l["greske"]) - 25}')
    for r in rez['razlozi_nepotpune']:
        print(f'  [NEPOTPUNA] {r}')
    print()
    print(STATUS_TEKST[rez['status']])
    return STATUS_KOD[rez['status']]


if __name__ == '__main__':
    sys.exit(main())
