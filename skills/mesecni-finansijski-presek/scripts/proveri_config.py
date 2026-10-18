#!/usr/bin/env python3
"""
Provera config-a za mesečni finansijski presek.

Greške zaustavljaju presek (izlazni kod 1). Upozorenja ne zaustavljaju,
ali idu na vrh izveštaja.

Proverava:
  - šemu: obavezna polja, dozvoljene vrednosti, reference izvor ↔ račun
  - privatnost: zadnje4 mora biti tačno 4 cifre; svaki niz od 8+ cifara
    bilo gde u config-u je sumnjiv (pun broj računa ili kartice)
  - zastarelost: kredit kome je prošla poslednja rata, cilj kome je
    prošao rok
  - dvosmislenost: isti trgovac u dve kategorije

Primeri:
    python3 proveri_config.py finansije.config.yaml
    python3 proveri_config.py finansije.config.yaml --danas 2026-10-10
    python3 proveri_config.py finansije.config.yaml --json

Izlazni kod: 0 bez grešaka, 1 sa greškama, 2 kad fajl ne može da se pročita.
"""

import argparse
import datetime as dt
import json
import re
import shutil
import sys


def ucitaj(putanja):
    """YAML preko PyYAML-a; JSON (podskup YAML-a) radi i bez njega.
    Putanja `-` čita config sa standardnog ulaza — za config koji živi u
    promptu zakazanog zadatka i ne sme da se upisuje u fajl."""
    if putanja == '-':
        tekst = sys.stdin.read()
    else:
        with open(putanja, encoding='utf-8') as f:
            tekst = f.read()
    try:
        import yaml
    except ImportError:
        try:
            return json.loads(tekst)
        except json.JSONDecodeError:
            raise ValueError('za YAML config je potreban PyYAML '
                             '(pip install pyyaml); JSON radi i bez njega')
    try:
        return yaml.safe_load(tekst)
    except yaml.YAMLError as e:
        raise ValueError(f'nije ispravan YAML:\n{e}')

PODRZANE_VERZIJE = {1}
TIPOVI_IZVORA = {'mejl', 'mejl_tekst', 'folder', 'rucno'}
TIPOVI_RACUNA = {'tekuci', 'devizni', 'multivalutni', 'kreditna_kartica', 'stedni'}
TIPOVI_PRIHODA = {'prihod', 'refundacija'}
RITMOVI = {'mesecno', 'sezonsko', 'neredovno'}
TIPOVI_IZLAZA = {'chat', 'markdown', 'csv', 'obsidian'}
RE_MESEC = re.compile(r'^\d{4}-(0[1-9]|1[0-2])$')
RE_DUGI_BROJ = re.compile(r'(?<!\d)\d(?:[ -]?\d){7,}(?!\d)')


class Nalazi:
    def __init__(self):
        self.greske, self.upozorenja = [], []

    def g(self, putanja, poruka):
        self.greske.append(f'{putanja}: {poruka}')

    def u(self, putanja, poruka):
        self.upozorenja.append(f'{putanja}: {poruka}')


def lista(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def mesec(s):
    s = str(s)
    if not RE_MESEC.match(s):
        return None
    return int(s[:4]), int(s[5:])


MIN_CIFARA_BROJ = 12   # brojevi računa i kartica imaju 13–18 cifara;
                       # iznosi u ličnom budžetu nemaju ni približno toliko


def kao_cifre(o):
    """Tekst za proveru, i za vrednosti koje YAML učita kao broj:
    `uloga: 160000012345678912` je int, a `1.6e17` float."""
    if isinstance(o, bool):
        return None
    if isinstance(o, int):
        return str(abs(o))
    if isinstance(o, float) and o == o and abs(o) != float('inf') and o.is_integer():
        return f'{abs(o):.0f}'
    return None


def proveri_privatnost(cfg, n):
    """Traži duge nizove cifara u svim ključevima i vrednostima, bilo da su
    tekst ili broj, i javlja u kom polju su — bez samog broja."""
    poruka = 'liči na pun broj računa ili kartice — upiši samo poslednje 4 cifre'

    def proveri_jedno(o, put):
        if isinstance(o, str):
            if RE_DUGI_BROJ.search(o):
                n.g(put, poruka)
            return
        cifre = kao_cifre(o)
        if cifre and len(cifre) >= MIN_CIFARA_BROJ:
            n.g(put, poruka)

    def setaj(o, put):
        if isinstance(o, dict):
            for k, v in o.items():
                kp = f'{put}.{k}' if put else str(k)
                proveri_jedno(k, f'{put or "config"} (ključ)')
                setaj(v, kp)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                setaj(v, f'{put}[{i}]')
        else:
            proveri_jedno(o, put)
    setaj(cfg, '')


def proveri(cfg, danas):
    n = Nalazi()
    if not isinstance(cfg, dict):
        n.g('config', 'nije YAML mapa')
        return n

    v = cfg.get('verzija')
    if v not in PODRZANE_VERZIJE:
        n.g('verzija', f'{v!r} nije podržana (podržano: {sorted(PODRZANE_VERZIJE)})')

    lok = cfg.get('lokalizacija') or {}
    ds = lok.get('decimalni_separator')
    if ds is not None and ds not in (',', '.'):
        n.g('lokalizacija.decimalni_separator', f'mora biti "," ili ".", ne {ds!r}')

    # — izvori —
    izvori = lista(cfg.get('izvori'))
    if not izvori:
        n.g('izvori', 'nijedan izvor — odakle stižu izvodi?')
    id_izvora = set()
    for i, iz in enumerate(izvori):
        p = f'izvori[{i}]'
        if not isinstance(iz, dict):
            n.g(p, 'mora biti mapa')
            continue
        iid = iz.get('id')
        if not iid:
            n.g(p, 'nema id')
        elif iid in id_izvora:
            n.g(p, f'id {iid!r} se ponavlja')
        id_izvora.add(iid)
        t = iz.get('tip')
        if t not in TIPOVI_IZVORA:
            n.g(p, f'tip {t!r} nije jedan od {sorted(TIPOVI_IZVORA)}')
        if t in ('mejl', 'mejl_tekst') and not lista(iz.get('posiljaoci')):
            n.g(p, 'mejl izvor bez posiljaoci')
        if t == 'folder' and not iz.get('putanja'):
            n.g(p, 'folder izvor bez putanja')
        od = iz.get('ocekivano_do')
        if od is not None and (isinstance(od, bool) or not isinstance(od, int)
                               or not 1 <= od <= 31):
            n.g(p, f'ocekivano_do mora biti dan u mesecu, 1–31, ne {od!r}')
        if t == 'rucno' and not iz.get('uputstvo'):
            n.u(p, 'ručni izvor bez uputstva — korisnik neće znati šta da pošalje')

    # — računi —
    racuni = lista(cfg.get('racuni'))
    if not racuni:
        n.g('racuni', 'nijedan račun')
    zadnje4, u_obuhvatu, korisceni_izvori = set(), 0, set()
    for i, r in enumerate(racuni):
        p = f'racuni[{i}]'
        if not isinstance(r, dict):
            n.g(p, 'mora biti mapa')
            continue
        z_raw = r.get('zadnje4', '')
        z = str(z_raw)
        if not isinstance(z_raw, str) and re.fullmatch(r'\d{1,4}', z):
            n.g(p, 'zadnje4 mora biti u navodnicima ("0123") — kao broj gubi '
                   'vodeće nule')
        elif not re.fullmatch(r'\d{4}', z):
            prikaz = f'…{z[-4:]}' if len(z) > 4 else repr(z)
            n.g(p, f'zadnje4 mora biti tačno 4 cifre u navodnicima, ne {prikaz}')
        elif z in zadnje4:
            n.g(p, f'zadnje4 {z} se ponavlja')
        zadnje4.add(z)
        for polje in ('kartica_zadnje4', 'partija_zadnje4'):
            if polje in r and (not isinstance(r[polje], str)
                               or not re.fullmatch(r'\d{4}', r[polje])):
                n.g(p, f'{polje} mora biti tačno 4 cifre u navodnicima')
        t = r.get('tip')
        if t not in TIPOVI_RACUNA:
            n.g(p, f'tip {t!r} nije jedan od {sorted(TIPOVI_RACUNA)}')
        ob = r.get('obuhvat', t != 'stedni')
        if not isinstance(ob, bool):
            n.g(p, 'obuhvat mora biti true ili false')
        iz = r.get('izvor')
        if not iz:
            if ob:
                n.g(p, 'nema izvor — račun je u obuhvatu, a bez njegovog '
                       'izvoda višak ne može da se izračuna')
        elif iz not in id_izvora:
            n.g(p, f'izvor {iz!r} ne postoji u izvori')
        korisceni_izvori.add(iz)
        if ob:
            u_obuhvatu += 1
        if 'glavni' in r:
            n.u(p, 'polje glavni se više ne koristi — višak se računa nad '
                   'obuhvatom (obuhvat: true/false)')
        if t == 'kreditna_kartica' and ob is False:
            n.u(p, 'kartica van obuhvata: kupovine ulaze u višak tek kad se '
                   'kartica plati, a uplata na nju se računa kao prenos')
        if t == 'stedni' and ob is True:
            n.u(p, 'štedni račun u obuhvatu: prenos na štednju se onda ne '
                   'vidi kao ušteda nego kao interni prenos')
        uo = r.get('uslov_odrzavanja')
        if uo is not None and not isinstance(
                (uo or {}).get('min_mesecna_potrosnja'), (int, float)):
            n.g(p, 'uslov_odrzavanja.min_mesecna_potrosnja mora biti broj')
    if racuni and u_obuhvatu == 0:
        n.g('racuni', 'nijedan račun nije u obuhvatu — višak nema osnovu')
    for iid in id_izvora - korisceni_izvori - {None}:
        n.u('izvori', f'izvor {iid!r} ne koristi nijedan račun')

    # — prihodi —
    prihodi = lista(cfg.get('prihodi'))
    if not prihodi:
        n.u('prihodi', 'nema prihoda — plata neće biti prepoznata')
    for i, pr in enumerate(prihodi):
        p = f'prihodi[{i}]'
        if not isinstance(pr, dict):
            n.g(p, 'mora biti mapa')
            continue
        if not pr.get('naziv'):
            n.g(p, 'nema naziv')
        if not lista(pr.get('prepoznaj_po')):
            n.g(p, 'nema prepoznaj_po')
        if pr.get('tip') not in TIPOVI_PRIHODA:
            n.g(p, f'tip mora biti jedan od {sorted(TIPOVI_PRIHODA)}')
        if pr.get('racun') and str(pr['racun']) not in zadnje4:
            n.g(p, f'racun {pr["racun"]!r} ne postoji u racuni')
        if any(k in pr for k in ('iznos', 'neto', 'plata')):
            n.u(p, 'iznos prihoda u config-u se ignoriše — meri se sa izvoda')

    # — kategorije —
    kat = cfg.get('kategorije') or {}
    if not isinstance(kat, dict):
        n.g('kategorije', 'mora biti mapa ime → trgovci')
        kat = {}
    gde = {}
    for ime, val in kat.items():
        p = f'kategorije.{ime}'
        if isinstance(val, dict):
            trgovci = lista(val.get('trgovci'))
            ritam = val.get('ritam')
            if ritam is not None and ritam not in RITMOVI:
                n.g(p, f'ritam mora biti jedan od {sorted(RITMOVI)}')
        else:
            trgovci = lista(val)
        if not trgovci:
            n.u(p, 'kategorija bez trgovaca')
        for t in trgovci:
            kljuc = str(t).strip().lower()
            if kljuc in gde and gde[kljuc] != ime:
                n.u(p, f'trgovac {t!r} je i u kategoriji {gde[kljuc]!r}')
            gde.setdefault(kljuc, ime)

    # — krediti —
    for i, k in enumerate(lista(cfg.get('krediti'))):
        p = f'krediti[{i}]'
        if not isinstance(k, dict):
            n.g(p, 'mora biti mapa')
            continue
        for polje in ('naziv', 'anuitet', 'poslednja_rata'):
            if polje not in k:
                n.g(p, f'nema {polje}')
        m = mesec(k.get('poslednja_rata', ''))
        if 'poslednja_rata' in k and m is None:
            n.g(p, 'poslednja_rata mora biti "YYYY-MM"')
        elif m and m < (danas.year, danas.month):
            n.u(p, f'{k.get("naziv")}: poslednja rata {k["poslednja_rata"]} je '
                   'prošla — ukloni kredit iz config-a ili ispravi datum')

    # — ciljevi —
    for i, c in enumerate(lista(cfg.get('ciljevi'))):
        p = f'ciljevi[{i}]'
        if not isinstance(c, dict):
            n.g(p, 'mora biti mapa')
            continue
        for polje in ('naziv', 'iznos', 'rok'):
            if polje not in c:
                n.g(p, f'nema {polje}')
        m = mesec(c.get('rok', ''))
        if 'rok' in c and m is None:
            n.g(p, 'rok mora biti "YYYY-MM"')
        elif m and m < (danas.year, danas.month):
            n.u(p, f'{c.get("naziv")}: rok {c["rok"]} je prošao')
        if c.get('drzi_se_na') and str(c['drzi_se_na']) not in zadnje4:
            n.g(p, f'drzi_se_na {c["drzi_se_na"]!r} ne postoji u racuni')

    # — kes, rezerva —
    kes = cfg.get('kes')
    if isinstance(kes, dict):
        for i, s in enumerate(lista(kes.get('stalne_linije'))):
            if not isinstance(s, dict) or not s.get('naziv') or \
                    not ('iznos' in s or 'formula' in s):
                n.g(f'kes.stalne_linije[{i}]', 'treba naziv i iznos ili formula')
    rez = cfg.get('rezerva')
    if isinstance(rez, dict) and not isinstance(rez.get('godisnje_procena'),
                                                (int, float)):
        n.g('rezerva.godisnje_procena', 'mora biti broj')

    # — izlaz —
    izl = cfg.get('izlaz') or {}
    t = izl.get('tip', 'chat')
    if t not in TIPOVI_IZLAZA:
        n.g('izlaz.tip', f'mora biti jedan od {sorted(TIPOVI_IZLAZA)}')
    if t in ('markdown', 'csv', 'obsidian') and not izl.get('putanja'):
        n.g('izlaz', f'tip {t} traži putanja')
    if t in ('markdown', 'obsidian'):
        mn = izl.get('mesecne_note')
        if mn and ('{YYYY}' not in mn or '{MM}' not in mn):
            n.u('izlaz.mesecne_note', 'obrazac nema {YYYY} i {MM} — note će se prepisivati')
    if t == 'csv':
        f = str(izl.get('fajl', 'finansije.csv'))
        if not f.lower().endswith('.csv'):
            n.u('izlaz.fajl', 'ne završava se na .csv')
    if t == 'chat':
        for polje in ('putanja', 'mesecne_note', 'glavni_fajl', 'fajl', 'pravila'):
            if polje in izl:
                n.u('izlaz', f'{polje} se ignoriše kad je tip chat')

    # — orkestracija —
    ork = cfg.get('orkestracija') or {}
    if ork.get('podagenti') in (True, 'da'):
        modeli = ork.get('modeli') or {}
        for uloga in ('mehanicki', 'analiticki', 'verifikacija'):
            if not modeli.get(uloga):
                n.u('orkestracija.modeli', f'nema model za {uloga} — '
                                           'podagent će naslediti roditeljski')

    proveri_privatnost(cfg, n)
    return n


POSLEDNJI_SIGURAN_DAN = 28   # postoji u svakom mesecu


def predlog_zakazivanja(cfg):
    """Dan pokretanja posle poslednjeg očekivanog izvoda.

    Do 27. u mesecu: sledeći dan, i presek zatvara prethodni mesec.
    Kad izvod stiže 28. ili kasnije, nijedan dan u istom mesecu nije
    siguran (februar ima 28 dana, a izvod od 31. bi bio promašen svakog
    meseca sa 30). Tada se pokreće 1. u sledećem mesecu, a presek zatvara
    mesec pre prethodnog — pomeraj_meseci je 2."""
    dani = [iz.get('ocekivano_do') for iz in lista(cfg.get('izvori'))
            if isinstance(iz, dict) and isinstance(iz.get('ocekivano_do'), int)
            and not isinstance(iz.get('ocekivano_do'), bool)]
    poslednji = max(dani) if dani else 7
    if poslednji < POSLEDNJI_SIGURAN_DAN:
        dan, pomeraj = poslednji + 1, 1
        opis = (f'mesečni zakazani zadatak, {dan}. u mesecu — dan posle poslednjeg '
                'očekivanog izvoda; zatvara prethodni mesec')
    else:
        dan, pomeraj = 1, 2
        opis = (f'mesečni zakazani zadatak, 1. u mesecu — izvodi stižu do '
                f'{poslednji}., pa nijedan dan istog meseca nije siguran; '
                'zatvara mesec pre prethodnog (npr. 1. novembra zatvara septembar)')
    return {'potreba': 'zakazani_zadatak', 'kriticno': False, 'dan': dan,
            'pomeraj_meseci': pomeraj,
            'vremenska_zona': (cfg.get('lokalizacija') or {}).get('vremenska_zona'),
            'opis': opis}


def potrebe(cfg):
    """Šta okruženje mora da omogući da bi presek po ovom config-u mogao
    da se izvrši. Skript ne vidi alate agenta; on samo kaže šta treba, a
    agent proverava da li to postoji. `kriticno` znači: bez ovoga nema
    preseka. Ostalo je preporuka."""
    racuni = [r for r in lista(cfg.get('racuni')) if isinstance(r, dict)]
    po_izvoru = {}
    for r in racuni:
        po_izvoru.setdefault(r.get('izvor'), []).append(str(r.get('zadnje4', '?')))
    out = []
    for iz in lista(cfg.get('izvori')):
        if not isinstance(iz, dict):
            continue
        # Samo ispravno zadnje4 se ispisuje; sve drugo je maskirano, da
        # ni pogrešno unet pun broj računa ne procuri kroz ovaj izlaz.
        rac = ['****' + (z if re.fullmatch(r'\d{4}', z) else '????')
               for z in po_izvoru.get(iz.get('id'), [])]
        t = iz.get('tip')
        if t in ('mejl', 'mejl_tekst'):
            out.append({'potreba': 'mejl', 'kriticno': True, 'izvor': iz.get('id'),
                        'posiljaoci': lista(iz.get('posiljaoci')), 'racuni': rac,
                        'opis': 'pristup mejlu za čitanje (pretraga i prilozi)'})
        elif t == 'folder':
            out.append({'potreba': 'folder', 'kriticno': True, 'izvor': iz.get('id'),
                        'putanja': iz.get('putanja'), 'racuni': rac,
                        'opis': 'pristup folderu sa izvodima'})
        elif t == 'rucno':
            out.append({'potreba': 'rucno', 'kriticno': True, 'izvor': iz.get('id'),
                        'uputstvo': iz.get('uputstvo'), 'racuni': rac,
                        'opis': 'korisnik svakog meseca prilaže izvod sam'})
    izl = cfg.get('izlaz') or {}
    if izl.get('tip', 'chat') != 'chat':
        out.append({'potreba': 'folder_zapisa', 'kriticno': False,
                    'putanja': izl.get('putanja'),
                    'opis': f'pristup folderu za zapis ({izl.get("tip")}); bez njega '
                            'izveštaj ostaje u razgovoru'})
    if not shutil.which('pdftotext'):
        out.append({'potreba': 'alat', 'kriticno': True, 'alat': 'pdftotext',
                    'opis': 'pdftotext (paket poppler-utils) za čitanje PDF izvoda'})
    out.append(predlog_zakazivanja(cfg))
    return out


def main():
    ap = argparse.ArgumentParser(description='Provera config-a za finansijski presek.')
    ap.add_argument('fajl', help='putanja do config-a, ili - za standardni ulaz')
    ap.add_argument('--danas', help='YYYY-MM-DD, za proveru zastarelosti '
                                    '(podrazumevano današnji datum)')
    ap.add_argument('--potrebe', action='store_true',
                    help='ispiši i šta okruženje mora da omogući (mejl, folder, '
                         'alati, zakazani zadatak)')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    try:
        cfg = ucitaj(a.fajl)
    except OSError as e:
        print(f'GRESKA: ne mogu da pročitam {a.fajl}: {e}', file=sys.stderr)
        return 2
    except ValueError as e:
        print(f'GRESKA: {a.fajl}: {e}', file=sys.stderr)
        return 2

    danas = dt.date.fromisoformat(a.danas) if a.danas else dt.date.today()
    n = proveri(cfg, danas)

    # Potrebe se ispisuju samo za ispravan config: neispravan može nositi
    # pun broj računa ili pogrešne reference, i ništa iz njega ne sme dalje.
    pot = potrebe(cfg) if a.potrebe and isinstance(cfg, dict) and not n.greske else None
    if a.json:
        izlaz = {'greske': n.greske, 'upozorenja': n.upozorenja,
                 'ispravan': not n.greske}
        if pot is not None:
            izlaz['potrebe'] = pot
        print(json.dumps(izlaz, ensure_ascii=False, indent=2))
    else:
        print(f'Config: {a.fajl}')
        for naslov, stavke in (('Greške', n.greske), ('Upozorenja', n.upozorenja)):
            if stavke:
                print(f'\n{naslov} ({len(stavke)}):')
                for s in stavke:
                    print(f'  - {s}')
        if a.potrebe and pot is None:
            print('\nPotrebe okruženja: nisu izračunate dok config ima greške.')
        if pot is not None:
            print('\nPotrebe okruženja:')
            for x in pot:
                oznaka = 'KRITIČNO ' if x['kriticno'] else 'preporuka'
                gde = ', '.join(x.get('racuni') or []) or x.get('putanja') or ''
                print(f'  [{oznaka}] {x["potreba"]}: {x["opis"]}'
                      + (f' — {gde}' if gde else ''))
        print()
        print('ISPRAVAN' if not n.greske else
              'NEISPRAVAN — ispravi greške pre preseka')
    return 1 if n.greske else 0


if __name__ == '__main__':
    sys.exit(main())
