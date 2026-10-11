#!/usr/bin/env python3
"""
Obračun mesečnog viška i vodopad normalizacije.

Višak nije promena stanja jednog računa. Prenos sa tekućeg na štednju
smanjuje tekući, a nije potrošnja; kupovina karticom ne dira tekući, a jeste
potrošnja. Zato se višak računa nad OBUHVATOM — skupom računa čiji se
saldo smatra „novcem za trošenje" — uz korekciju za prenose koji prelaze
granicu obuhvata.

Obuhvat se zadaje u config-u po računu (`racuni[].obuhvat`). Podrazumevano
su u obuhvatu svi računi osim štednih (`tip: stedni`). Kreditna kartica je
u obuhvatu kao dug (negativno stanje), pa kupovina umanjuje višak kad se
desi, a uplata na karticu je interni prenos.

    višak meseca = Σ promena stanja računa u obuhvatu
                 + prenosi iz obuhvata na sopstvene račune van obuhvata
                 − prenosi sa sopstvenih računa van obuhvata u obuhvat

Prenosi unutar obuhvata se poništavaju sami od sebe. Razlika između dva
kraka takvog prenosa (kupovina deviza, naknada) je stvaran trošak i već je
u promeni stanja — prijavljuje se, ne koriguje.

Promena svakog računa se računa u njegovoj valuti, pa preračunava JEDNIM
kursom (zadatim u ulazu, tipično srednji kurs na poslednji dan meseca).
Tako kursna razlika na stanje koje je samo stajalo na deviznom računu ne
ulazi u višak — ona nije ni zarađena ni potrošena.

Kreditna kartica VAN obuhvata (gotovinski princip): kupovine ne utiču na
višak dok se kartica ne plati, a uplata na karticu je tada potrošnja — ne
ušteda. Podizanje gotovine sa takve kartice je pozajmica, ne prihod.

Konverzija između računa u obuhvatu (npr. RSD → EUR) traži `kurs_dana`:
zvanični kurs na dan konverzije. Trošak konverzije je razlika krakova po
tom kursu i ulazi u višak. Promena kursa od dana konverzije do kraja
meseca je nerealizovana kursna razlika i ne ulazi. Bez `kurs_dana` ta dva
se ne mogu razdvojiti, pa je obračun NEPOTPUN.

Ulaz (JSON):
{
  "kurs": {"EUR": 117.2},                     # osnovna valuta = 1
  "racuni": {"1111": {"pocetno": 100000, "zavrsno": 167716.19}, ...},
  "transferi": [{"sa": "1111", "na": "9999", "iznos_sa": 20000,
                 "iznos_na": 20000},          # krak u valuti svog računa
                {"sa": "1111", "na": "2222", "iznos_sa": 11800,
                 "iznos_na": 100, "kurs_dana": {"EUR": 117.5}}],
  "jednokratno": {
    "prihodi":  [{"opis": "bonus", "iznos": 120000}],
    "troskovi": [{"opis": "nameštaj", "iznos": 65000}],
    "prestale_obaveze": [{"opis": "poslednja rata", "iznos": 30000}]
  },
  "kontrola": {"redovni_prihodi": 100350.75, "redovni_troskovi": 31234.56}
}
Iznosi u `jednokratno` i `kontrola` su u osnovnoj valuti.

Primer:
    python3 obracun_viska.py mesec.json --config finansije.config.yaml

Izlazni kod: 0 obračun završen i kontrola drugim putem izlazi,
1 kontrola drugim putem ne izlazi, 2 greška ulaza,
3 nepotpuno (račun iz obuhvata bez stanja, nedostaje kurs, nema kontrole).
"""

import argparse
import json
import sys


def ucitaj(putanja):
    if putanja == '-':
        tekst = sys.stdin.read()
    else:
        with open(putanja, encoding='utf-8') as f:
            tekst = f.read()
    if putanja.endswith('.json'):
        return json.loads(tekst)
    try:
        import yaml
        return yaml.safe_load(tekst) or {}
    except ImportError:
        return json.loads(tekst)


def u_obuhvatu(racun):
    if 'obuhvat' in racun:
        return bool(racun['obuhvat'])
    return racun.get('tip') != 'stedni'


def zbir(stavke):
    return round(sum(float(s.get('iznos', 0)) for s in stavke or []), 2)


def obracunaj(cfg, ulaz, tolerancija=1.0):
    osnovna = (cfg.get('lokalizacija') or {}).get('valuta_osnovna', 'RSD')
    racuni_cfg = {str(r['zadnje4']): r for r in cfg.get('racuni') or []}
    kurs = {osnovna: 1.0, **{k: float(v) for k, v in (ulaz.get('kurs') or {}).items()}}
    stanja = {str(k): v for k, v in (ulaz.get('racuni') or {}).items()}
    nepotpuno, napomene, greske = [], [], []

    def kurs_za(z4):
        valuta = racuni_cfg[z4].get('valuta', osnovna)
        if valuta not in kurs:
            nepotpuno.append(f'nema kursa za {valuta} (račun ****{z4})')
            return None
        return kurs[valuta]

    obuhvat = [z for z, r in racuni_cfg.items() if u_obuhvatu(r)]
    if not obuhvat:
        greske.append('nijedan račun nije u obuhvatu')

    promene = []
    for z4 in obuhvat:
        s = stanja.get(z4)
        if not s or s.get('pocetno') is None or s.get('zavrsno') is None:
            nepotpuno.append(f'račun ****{z4} je u obuhvatu, a nema početno i '
                             'završno stanje — izvod fali ili nije proveren')
            continue
        k = kurs_za(z4)
        if k is None:
            continue
        u_valuti = round(float(s['zavrsno']) - float(s['pocetno']), 2)
        promene.append({'racun': z4, 'valuta': racuni_cfg[z4].get('valuta', osnovna),
                        'promena_u_valuti': u_valuti,
                        'promena': round(u_valuti * k, 2)})
    for z4 in stanja:
        if z4 not in racuni_cfg:
            greske.append(f'račun ****{z4} iz ulaza ne postoji u config-u')
        elif z4 not in obuhvat:
            napomene.append(f'račun ****{z4} je van obuhvata; njegova promena '
                            'ne ulazi u višak')

    def valuta(z4):
        return racuni_cfg[z4].get('valuta', osnovna)

    def je_obaveza(z4):
        return racuni_cfg[z4].get('tip') == 'kreditna_kartica'

    korekcija, ka_van, iz_van, revalorizacija = 0.0, 0.0, 0.0, 0.0
    interni, placeno_karticom = [], []
    for i, t in enumerate(ulaz.get('transferi') or []):
        sa, na = str(t.get('sa')), str(t.get('na'))
        nepoznati = [z for z in (sa, na) if z not in racuni_cfg]
        if nepoznati:
            greske.append(f'transferi[{i}]: račun(i) {nepoznati} nisu u config-u — '
                          'prenos na tuđ račun nije transfer nego rashod')
            continue
        sa_in, na_in = sa in obuhvat, na in obuhvat
        if sa_in and not na_in:
            if t.get('iznos_sa') is None:
                greske.append(f'transferi[{i}]: nedostaje iznos_sa')
                continue
            k = kurs_za(sa)
            if k is None:
                continue
            v = round(float(t['iznos_sa']) * k, 2)
            if je_obaveza(na):
                # Kartica van obuhvata: njene kupovine ulaze u višak tek kad
                # se plate. Uplata na nju je zato potrošnja, ne ušteda.
                placeno_karticom.append({'kartica': na, 'iznos': v})
            else:
                korekcija += v
                ka_van += v
        elif na_in and not sa_in:
            if t.get('iznos_na') is None:
                greske.append(f'transferi[{i}]: nedostaje iznos_na')
                continue
            k = kurs_za(na)
            if k is None:
                continue
            # Povlačenje sa štednje nije prihod; podizanje sa kartice van
            # obuhvata je pozajmica, ni ona nije prihod.
            v = round(float(t['iznos_na']) * k, 2)
            korekcija -= v
            iz_van += v
        elif sa_in and na_in:
            if t.get('iznos_sa') is None or t.get('iznos_na') is None:
                napomene.append(f'transferi[{i}]: interni prenos bez oba kraka — '
                                'trošak konverzije nije izmeren')
                continue
            ks, kn = kurs_za(sa), kurs_za(na)
            if ks is None or kn is None:
                continue
            vs, vn = valuta(sa), valuta(na)
            if vs == vn:
                interni.append({'sa': sa, 'na': na, 'trosak': round(
                    (float(t['iznos_na']) - float(t['iznos_sa'])) * ks, 2)})
                continue
            # Konverzija: krak u stranoj valuti vrednuje se kursom DANA
            # konverzije. Razlika do kursa na kraju meseca je nerealizovana
            # kursna razlika i ne ulazi u višak.
            kd = {osnovna: 1.0, **{k: float(v) for k, v in
                                   (t.get('kurs_dana') or {}).items()}}
            fale = [v for v in (vs, vn) if v not in kd]
            if fale:
                nepotpuno.append(f'transferi[{i}]: konverzija {vs}→{vn} bez kurs_dana '
                                 f'za {fale} — trošak konverzije ne može da se '
                                 'odvoji od promene kursa')
                continue
            trosak = round(float(t['iznos_na']) * kd[vn] - float(t['iznos_sa']) * kd[vs], 2)
            reval = round(float(t['iznos_na']) * (kn - kd[vn])
                          - float(t['iznos_sa']) * (ks - kd[vs]), 2)
            revalorizacija += reval
            interni.append({'sa': sa, 'na': na, 'trosak': trosak,
                            'kursna_razlika': reval})

    for p in placeno_karticom:
        napomene.append(f'kartica ****{p["kartica"]} je van obuhvata: uplata na nju '
                        f'({p["iznos"]:.2f}) računata je kao potrošnja meseca')

    if greske:
        return {'status': 'greska', 'greske': greske}

    promena_ukupno = round(sum(p['promena'] for p in promene), 2)
    visak = round(promena_ukupno - revalorizacija + korekcija, 2)
    j = ulaz.get('jednokratno') or {}
    jp, jt, po = zbir(j.get('prihodi')), zbir(j.get('troskovi')), zbir(j.get('prestale_obaveze'))
    ponovljiv = round(visak - jp + jt + po, 2)
    rez_god = (cfg.get('rezerva') or {}).get('godisnje_procena')
    rezerva = round(float(rez_god) / 12, 2) if rez_god is not None else 0.0
    if rez_god is None:
        napomene.append('config nema rezerva.godisnje_procena — rezerva je 0')
    realno = round(ponovljiv - rezerva, 2)

    n0 = lambda x: round(x, 2) + 0.0   # bez −0,00
    vodopad = [
        ('promena stanja računa u obuhvatu', n0(promena_ukupno)),
        ('nerealizovana kursna razlika (isključena)', n0(-revalorizacija)),
        ('prenosi na sopstvene račune van obuhvata', n0(ka_van)),
        ('prenosi sa sopstvenih računa van obuhvata', n0(-iz_van)),
        ('= višak meseca', n0(visak)),
        ('jednokratni prihodi', n0(-jp)),
        ('jednokratni troškovi', n0(jt)),
        ('obaveze koje prestaju', n0(po)),
        ('= ponovljiv mesečni višak', n0(ponovljiv)),
        ('mesečna rezerva za neredovne troškove', n0(-rezerva)),
        ('= realno raspoloživo', n0(realno)),
    ]

    kontrola = None
    k = ulaz.get('kontrola')
    if k and k.get('redovni_prihodi') is not None and k.get('redovni_troskovi') is not None:
        drugi_put = round(float(k['redovni_prihodi']) - float(k['redovni_troskovi']) + po, 2)
        razlika = round(ponovljiv - drugi_put, 2)
        kontrola = {'drugi_put': drugi_put, 'razlika': razlika,
                    'poklapa': abs(razlika) <= tolerancija}
    else:
        nepotpuno.append('nema kontrole drugim putem (kontrola.redovni_prihodi '
                         'i kontrola.redovni_troskovi) — vodopad nije proveren')

    if nepotpuno:
        status = 'nepotpuno'
    elif kontrola and not kontrola['poklapa']:
        status = 'kontrola_ne_izlazi'
    else:
        status = 'ok'

    return {
        'status': status,
        'valuta': osnovna,
        'decimalna_zapeta': (cfg.get('lokalizacija') or {}).get('decimalni_separator', ',') == ',',
        'obuhvat': obuhvat,
        'promene': promene,
        'interni_prenosi': interni,
        'placeno_karticom_van_obuhvata': placeno_karticom,
        'vodopad': [{'korak': n, 'iznos': v} for n, v in vodopad],
        'kontrola': kontrola,
        'nepotpuno': nepotpuno,
        'napomene': napomene,
    }


KOD = {'ok': 0, 'kontrola_ne_izlazi': 1, 'greska': 2, 'nepotpuno': 3}


def main():
    ap = argparse.ArgumentParser(description='Obračun mesečnog viška nad obuhvatom računa.')
    ap.add_argument('ulaz', help='JSON sa stanjima, kursom, transferima i jednokratnim stavkama')
    ap.add_argument('--config', required=True,
                    help='finansije.config.yaml ili .json, ili - za standardni ulaz')
    ap.add_argument('--tolerancija', type=float, default=1.0,
                    help='dopuštena razlika u kontroli drugim putem (podrazumevano 1)')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    try:
        cfg = ucitaj(a.config)
        with open(a.ulaz, encoding='utf-8') as f:
            ulaz = json.load(f)
    except Exception as e:
        print(f'GREŠKA: {e}', file=sys.stderr)
        return 2

    rez = obracunaj(cfg, ulaz, a.tolerancija)
    if a.json:
        print(json.dumps(rez, ensure_ascii=False, indent=2))
        return KOD[rez['status']]
    if rez['status'] == 'greska':
        for g in rez['greske']:
            print(f'GREŠKA: {g}', file=sys.stderr)
        return 2

    v = rez['valuta']

    def f(x):
        t = f'{x:+,.2f}'
        if rez['decimalna_zapeta']:
            t = t.replace(',', '\x00').replace('.', ',').replace('\x00', '.')
        return t
    print(f'Obuhvat: {", ".join("****" + z for z in rez["obuhvat"])}\n')
    for p in rez['promene']:
        dodatak = '' if p['valuta'] == v else f' ({f(p["promena_u_valuti"])} {p["valuta"]})'
        print(f'  ****{p["racun"]}: {f(p["promena"]):>15} {v}{dodatak}')
    for t in rez['interni_prenosi']:
        if abs(t['trosak']) >= 0.01:
            print(f'  interni prenos ****{t["sa"]} → ****{t["na"]}: trošak '
                  f'{f(t["trosak"])} {v} (u višku)')
        if abs(t.get('kursna_razlika', 0)) >= 0.01:
            print(f'    kursna razlika posle konverzije {f(t["kursna_razlika"])} {v} '
                  '(nerealizovana, van viška)')
    print()
    for s in rez['vodopad']:
        print(f'  {s["korak"]:<42} {f(s["iznos"]):>15}')
    if rez['kontrola']:
        k = rez['kontrola']
        print(f'\n  kontrola drugim putem (redovni prihodi − redovni troškovi '
              f'+ obaveze koje prestaju): {f(k["drugi_put"])}, razlika {f(k["razlika"])}')
    for n in rez['nepotpuno']:
        print(f'  [NEPOTPUNO] {n}')
    for n in rez['napomene']:
        print(f'  [napomena] {n}')
    print()
    print({'ok': 'OK', 'nepotpuno': 'NEPOTPUNO — ne izvodi zaključke',
           'kontrola_ne_izlazi': 'KONTROLA NE IZLAZI — stavka je na pogrešnoj strani'}[rez['status']])
    return KOD[rez['status']]


if __name__ == '__main__':
    sys.exit(main())
