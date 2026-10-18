import copy
import datetime as dt
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "mesecni-finansijski-presek"
SCRIPTS = SKILL / "scripts"
EXAMPLES = ROOT / "examples" / "mesecni-finansijski-presek"
DANAS = dt.date(2026, 10, 10)


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def config() -> dict:
    return json.loads((EXAMPLES / "sinteticki-config.json").read_text(encoding="utf-8"))


class ProveriConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pc = load("proveri_config")

    def check(self, cfg: dict):
        return self.pc.proveri(cfg, DANAS)

    def test_synthetic_config_is_valid(self) -> None:
        n = self.check(config())
        self.assertEqual(n.greske, [])

    def test_full_account_number_is_rejected_and_not_echoed(self) -> None:
        cfg = config()
        cfg["racuni"][0]["zadnje4"] = "160000012345678912"
        n = self.check(cfg)
        self.assertTrue(n.greske)
        self.assertNotIn("160000012345678912", " ".join(n.greske))

    def test_long_digit_run_anywhere_is_flagged(self) -> None:
        cfg = config()
        cfg["racuni"][0]["uloga"] = "račun 160-0000123456789-12"
        n = self.check(cfg)
        self.assertTrue(any("pun broj" in g for g in n.greske))

    def test_unknown_source_reference_is_an_error(self) -> None:
        cfg = config()
        cfg["racuni"][0]["izvor"] = "nepostojeci"
        self.assertTrue(self.check(cfg).greske)

    def test_expired_loan_and_goal_are_warnings(self) -> None:
        cfg = config()
        cfg["krediti"] = [{"naziv": "kredit", "anuitet": 1, "poslednja_rata": "2026-09"}]
        cfg["ciljevi"] = [{"naziv": "cilj", "iznos": 1, "rok": "2026-08"}]
        n = self.check(cfg)
        self.assertEqual(n.greske, [])
        self.assertTrue(any("poslednja rata" in u for u in n.upozorenja))
        self.assertTrue(any("rok" in u for u in n.upozorenja))

    def test_merchant_in_two_categories_is_a_warning(self) -> None:
        cfg = config()
        cfg["kategorije"]["druga"] = ["market a"]
        self.assertTrue(any("market a" in u.lower() for u in self.check(cfg).upozorenja))

    def test_salary_amount_in_config_is_ignored(self) -> None:
        cfg = config()
        cfg["prihodi"][0]["iznos"] = 100000
        self.assertTrue(any("ignoriše" in u for u in self.check(cfg).upozorenja))

    def test_unsupported_version_is_an_error(self) -> None:
        cfg = copy.deepcopy(config())
        cfg["verzija"] = 2
        self.assertTrue(self.check(cfg).greske)

    def test_output_defaults_to_chat_without_any_folder(self) -> None:
        cfg = config()
        cfg.pop("izlaz", None)
        self.assertEqual(self.check(cfg).greske, [])

    def test_every_output_type_needs_only_a_path(self) -> None:
        for tip in ("markdown", "csv", "obsidian"):
            with self.subTest(tip=tip):
                cfg = config()
                cfg["izlaz"] = {"tip": tip}
                self.assertTrue(self.check(cfg).greske)
                cfg["izlaz"]["putanja"] = "/finansije"
                self.assertEqual(self.check(cfg).greske, [])

    def test_no_account_in_scope_is_an_error(self) -> None:
        cfg = config()
        for r in cfg["racuni"]:
            r["obuhvat"] = False
        self.assertTrue(any("obuhvat" in g for g in self.check(cfg).greske))

    def test_savings_account_needs_no_source(self) -> None:
        cfg = config()
        stedni = next(r for r in cfg["racuni"] if r["tip"] == "stedni")
        self.assertNotIn("izvor", stedni)
        self.assertEqual(self.check(cfg).greske, [])

    def test_numeric_account_number_is_flagged(self) -> None:
        cfg = config()
        cfg["racuni"][0]["uloga"] = 160000012345678912
        cfg["racuni"][1]["limit"] = 1.6e17
        greske = self.check(cfg).greske
        self.assertTrue(any("racuni[0].uloga" in g for g in greske))
        self.assertTrue(any("racuni[1].limit" in g for g in greske))
        self.assertNotIn("160000012345678912", " ".join(greske))

    def test_ordinary_amounts_are_not_flagged(self) -> None:
        cfg = config()
        cfg["rezerva"] = {"godisnje_procena": 12000000}
        self.assertEqual(self.check(cfg).greske, [])

    def test_unquoted_last_four_is_an_error(self) -> None:
        cfg = config()
        cfg["racuni"][0]["zadnje4"] = 1111
        self.assertTrue(any("navodnicima" in g for g in self.check(cfg).greske))

    def test_config_can_be_read_from_stdin(self) -> None:
        tekst = (EXAMPLES / "sinteticki-config.json").read_text(encoding="utf-8")
        for skript, extra in (("proveri_config.py", ["-"]),
                              ("obracun_viska.py", [str(EXAMPLES / "sinteticki-mesec.json"),
                                                    "--config", "-"]),
                              ("kontrola_bilansa.py", [str(EXAMPLES / "sinteticki-izvod.txt"),
                                                       "--config", "-", *HEADER])):
            with self.subTest(skript=skript):
                r = subprocess.run([sys.executable, str(SCRIPTS / skript), *extra],
                                   input=tekst, text=True, capture_output=True, check=False)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_needs_cover_every_source_and_scheduling(self) -> None:
        cfg = config()
        cfg["izvori"].append({"id": "app", "tip": "rucno", "uputstvo": "izvoz iz aplikacije"})
        cfg["racuni"].append({"zadnje4": "5555", "tip": "multivalutni", "izvor": "app"})
        cfg["izvori"][0]["ocekivano_do"] = 6
        cfg["izlaz"] = {"tip": "csv", "putanja": "/finansije"}
        pot = {p["potreba"]: p for p in self.pc.potrebe(cfg)}
        self.assertTrue(pot["mejl"]["kriticno"])
        self.assertIn("****1111", pot["mejl"]["racuni"])
        self.assertEqual(pot["rucno"]["racuni"], ["****5555"])
        self.assertFalse(pot["folder_zapisa"]["kriticno"])
        self.assertEqual(pot["zakazani_zadatak"]["dan"], 7)

    def test_schedule_never_runs_before_last_statement(self) -> None:
        for poslednji, dan, pomeraj in ((6, 7, 1), (27, 28, 1), (28, 1, 2),
                                        (29, 1, 2), (31, 1, 2)):
            with self.subTest(ocekivano_do=poslednji):
                cfg = config()
                cfg["izvori"][0]["ocekivano_do"] = poslednji
                z = next(p for p in self.pc.potrebe(cfg) if p["potreba"] == "zakazani_zadatak")
                self.assertEqual((z["dan"], z["pomeraj_meseci"]), (dan, pomeraj))

    def test_invalid_expected_day_is_an_error(self) -> None:
        for vrednost in (0, 32, "7", True):
            with self.subTest(vrednost=vrednost):
                cfg = config()
                cfg["izvori"][0]["ocekivano_do"] = vrednost
                self.assertTrue(any("ocekivano_do" in g for g in self.check(cfg).greske))

    def test_needs_are_not_printed_for_invalid_config(self) -> None:
        cfg = config()
        cfg["racuni"][0]["zadnje4"] = "160000012345678912"
        for extra in ([], ["--json"]):
            with self.subTest(extra=extra):
                r = subprocess.run(
                    [sys.executable, str(SCRIPTS / "proveri_config.py"), "-", "--potrebe", *extra],
                    input=json.dumps(cfg), text=True, capture_output=True, check=False)
                self.assertEqual(r.returncode, 1)
                self.assertNotIn("12345678912", r.stdout + r.stderr)
                if extra:
                    self.assertNotIn("potrebe", json.loads(r.stdout))

    def test_needs_mask_anything_but_four_digits(self) -> None:
        cfg = config()
        cfg["racuni"][0]["zadnje4"] = "160000012345678912"
        racuni = next(p for p in self.pc.potrebe(cfg) if p["potreba"] == "mejl")["racuni"]
        self.assertNotIn("12345678912", " ".join(racuni))
        self.assertIn("****????", racuni)

    def test_chat_output_needs_no_folder(self) -> None:
        cfg = config()
        cfg.pop("izlaz", None)
        self.assertNotIn("folder_zapisa", {p["potreba"] for p in self.pc.potrebe(cfg)})

    def test_bundled_yaml_examples_are_valid(self) -> None:
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML nije instaliran")
        for name in ("config.minimalni.yaml", "config.primer.yaml"):
            with self.subTest(name=name):
                cfg = yaml.safe_load((SKILL / "assets" / name).read_text(encoding="utf-8"))
                self.assertEqual(self.check(cfg).greske, [])


HEADER = ("--pocetno", "100000", "--zavrsno", "167716.19",
          "--isplate", "32634.56", "--uplate", "100350.75")
KARTICA = ("--pocetno", "-10000", "--zavrsno", "-7699.50",
           "--isplate", "7699.50", "--uplate", "10000")


def bez_linija(path: Path, *fragmenti: str) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    return "\n".join(l for l in lines if not any(f in l for f in fragmenti)) + "\n"


class KontrolaBilansaTests(unittest.TestCase):
    def run_check(self, source, *extra: str):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "izvod.txt"
            path.write_text(source if isinstance(source, str)
                            else source.read_text(encoding="utf-8"), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "kontrola_bilansa.py"), str(path),
                 "--config", str(EXAMPLES / "sinteticki-config.json"), "--json", *extra],
                text=True, capture_output=True, check=False,
            )
        data = json.loads(result.stdout) if result.stdout.strip() else None
        return result.returncode, data

    def provera(self, data, naziv):
        return next(p for p in data["provere"] if p["naziv"] == naziv)

    def test_synthetic_statement_passes_all_three_checks(self) -> None:
        code, data = self.run_check(EXAMPLES / "sinteticki-izvod.txt", *HEADER)
        self.assertEqual(code, 0, data)
        self.assertEqual(data["status"], "prosla")
        self.assertEqual({p["naziv"] for p in data["provere"] if p["prosla"]},
                         {"lanac", "promet", "zaglavlje"})

    def test_header_totals_never_replace_parsed_totals(self) -> None:
        # Zaglavlje je interno konzistentno, a parsirani promet nije isti.
        code, data = self.run_check(
            EXAMPLES / "sinteticki-izvod.txt",
            "--pocetno", "100000", "--zavrsno", "167716.19",
            "--isplate", "37634.56", "--uplate", "105350.75")
        self.assertEqual(code, 1)
        self.assertTrue(self.provera(data, "zaglavlje")["prosla"])
        self.assertFalse(self.provera(data, "promet")["prosla"])

    def test_dropped_first_transaction_and_opening_row_fails(self) -> None:
        src = bez_linija(EXAMPLES / "sinteticki-izvod.txt", "MARKET A")
        src = "\n".join(l for l in src.splitlines() if l.strip() != "100.000,00") + "\n"
        code, data = self.run_check(src, *HEADER)
        self.assertEqual(code, 1)
        self.assertFalse(self.provera(data, "lanac")["prosla"])

    def test_dropped_last_transaction_is_not_bridged_by_footer(self) -> None:
        code, data = self.run_check(
            bez_linija(EXAMPLES / "sinteticki-izvod.txt", "PRIMER DOO"), *HEADER)
        self.assertEqual(code, 1)
        lanac = self.provera(data, "lanac")
        self.assertFalse(lanac["prosla"])
        self.assertAlmostEqual(lanac["detalj"]["razlika_do_zavrsnog"], 100350.75, places=2)

    def test_opening_balance_row_with_single_amount_is_read(self) -> None:
        _, data = self.run_check(EXAMPLES / "sinteticki-izvod.txt", *HEADER)
        stanja = data["lanac"]["redova_sa_stanjem"]
        self.assertEqual(stanja, 6)   # početno + 5 transakcija; podnožje van lanca
        self.assertEqual(len(data["lanac"]["zbirnih_redova_preskoceno"]), 1)

    def test_missing_header_is_incomplete_not_success(self) -> None:
        code, data = self.run_check(EXAMPLES / "sinteticki-izvod.txt")
        self.assertEqual(code, 3)
        self.assertEqual(data["status"], "nepotpuna")
        self.assertFalse(data["prosla"])

    def test_unconfirmed_balance_column_never_passes(self) -> None:
        # Kartični izvod bez kolone stanja, bez potvrde formata.
        code, data = self.run_check(EXAMPLES / "sinteticki-izvod-kartica.txt", *KARTICA)
        self.assertEqual(code, 3)
        self.assertTrue(self.provera(data, "zaglavlje")["prosla"])
        self.assertEqual(data["status"], "nepotpuna")

    def test_badly_parsed_statement_does_not_become_no_balance(self) -> None:
        # Pomeren saldo u svakom drugom redu: mnogo neslaganja.
        lines = (EXAMPLES / "sinteticki-izvod.txt").read_text(encoding="utf-8").splitlines()
        lose = "\n".join(l.replace("     9", "      9").replace("     7", "      7")
                         .replace(",44", ",45") if l[:1] in "24" else l
                         for l in lines) + "\n"
        code, data = self.run_check(lose, *HEADER)
        self.assertNotEqual(code, 0)
        self.assertFalse(data["prosla"])
        self.assertFalse(data["bez_kolone_stanja"])

    def test_confirmed_no_balance_statement_checks_turnover(self) -> None:
        code, data = self.run_check(EXAMPLES / "sinteticki-izvod-kartica.txt",
                                    *KARTICA, "--bez-kolone-stanja")
        self.assertEqual(code, 0, data)
        self.assertIsNone(self.provera(data, "lanac")["prosla"])
        code, data = self.run_check(
            bez_linija(EXAMPLES / "sinteticki-izvod-kartica.txt", "STREAMING"),
            *KARTICA, "--bez-kolone-stanja")
        self.assertEqual(code, 1)
        self.assertFalse(self.provera(data, "promet")["prosla"])

    def test_wrong_closing_balance_fails(self) -> None:
        code, data = self.run_check(
            EXAMPLES / "sinteticki-izvod.txt",
            "--pocetno", "100000", "--zavrsno", "167000",
            "--isplate", "32634.56", "--uplate", "100350.75")
        self.assertEqual(code, 1)
        self.assertAlmostEqual(self.provera(data, "zaglavlje")["detalj"]["razlika"],
                               716.19, places=2)


class ObracunViskaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ov = load("obracun_viska")
        self.cfg = config()
        self.mesec = json.loads((EXAMPLES / "sinteticki-mesec.json").read_text(encoding="utf-8"))

    def korak(self, rez, naziv):
        return next(s["iznos"] for s in rez["vodopad"] if s["korak"] == naziv)

    def test_transfer_to_savings_is_not_spending(self) -> None:
        rez = self.ov.obracunaj(self.cfg, self.mesec)
        self.assertEqual(rez["status"], "ok", rez)
        self.assertAlmostEqual(self.korak(rez, "promena stanja računa u obuhvatu"), 67716.19)
        self.assertAlmostEqual(self.korak(rez, "= višak meseca"), 87716.19)
        self.assertAlmostEqual(rez["kontrola"]["razlika"], 0.0)

    def test_withdrawal_from_savings_is_not_income(self) -> None:
        m = copy.deepcopy(self.mesec)
        m["racuni"]["1111"]["zavrsno"] += 30000
        m["transferi"].append({"sa": "9999", "na": "1111", "iznos_sa": 30000, "iznos_na": 30000})
        rez = self.ov.obracunaj(self.cfg, m)
        self.assertAlmostEqual(self.korak(rez, "= višak meseca"), 87716.19)

    def konverzija(self, kurs_dana):
        m = copy.deepcopy(self.mesec)
        m["racuni"]["1111"]["zavrsno"] -= 11800
        m["racuni"]["2222"]["zavrsno"] += 100
        t = {"sa": "1111", "na": "2222", "iznos_sa": 11800, "iznos_na": 100}
        if kurs_dana is not None:
            t["kurs_dana"] = {"EUR": kurs_dana}
        m["transferi"].append(t)
        return m

    def test_internal_conversion_cost_is_spending(self) -> None:
        m = self.konverzija(117.2)
        m["kontrola"]["redovni_troskovi"] += 80
        rez = self.ov.obracunaj(self.cfg, m)
        self.assertEqual(rez["status"], "ok", rez)
        self.assertAlmostEqual(self.korak(rez, "= višak meseca"), 87716.19 - 80)
        self.assertAlmostEqual(rez["interni_prenosi"][0]["trosak"], -80.0)

    def test_rate_move_after_conversion_is_not_spending(self) -> None:
        # Kupljeno po 117,5 (zvanični kurs tog dana), na kraju meseca 117,2.
        # Trošak konverzije je 50; 30 je nerealizovana kursna razlika.
        m = self.konverzija(117.5)
        m["kontrola"]["redovni_troskovi"] += 50
        rez = self.ov.obracunaj(self.cfg, m)
        self.assertEqual(rez["status"], "ok", rez)
        self.assertAlmostEqual(rez["interni_prenosi"][0]["trosak"], -50.0)
        self.assertAlmostEqual(rez["interni_prenosi"][0]["kursna_razlika"], -30.0)
        self.assertAlmostEqual(self.korak(rez, "= višak meseca"), 87716.19 - 50)

    def test_conversion_without_day_rate_is_incomplete(self) -> None:
        rez = self.ov.obracunaj(self.cfg, self.konverzija(None))
        self.assertEqual(rez["status"], "nepotpuno")

    def test_card_outside_scope_payment_is_spending(self) -> None:
        cfg = copy.deepcopy(self.cfg)
        cfg["racuni"] = [r for r in cfg["racuni"] if r["zadnje4"] != "2222"]
        cfg["racuni"].append({"zadnje4": "4444", "tip": "kreditna_kartica",
                              "obuhvat": False, "izvor": "banka"})
        m = {"racuni": {"1111": {"pocetno": 10000, "zavrsno": 5000}},
             "transferi": [{"sa": "1111", "na": "4444", "iznos_sa": 5000}],
             "kontrola": {"redovni_prihodi": 0, "redovni_troskovi": 5000}}
        rez = self.ov.obracunaj(cfg, m)
        self.assertEqual(rez["status"], "ok", rez)
        self.assertAlmostEqual(self.korak(rez, "= višak meseca"), -5000.0)
        self.assertEqual(rez["placeno_karticom_van_obuhvata"][0]["kartica"], "4444")

    def test_card_inside_scope_payment_is_internal(self) -> None:
        cfg = copy.deepcopy(self.cfg)
        cfg["racuni"] = [r for r in cfg["racuni"] if r["zadnje4"] != "2222"]
        cfg["racuni"].append({"zadnje4": "4444", "tip": "kreditna_kartica",
                              "izvor": "banka"})
        # Kupovine 5.000 karticom, pa uplata 5.000 na karticu.
        m = {"racuni": {"1111": {"pocetno": 10000, "zavrsno": 5000},
                        "4444": {"pocetno": 0, "zavrsno": 0}},
             "transferi": [{"sa": "1111", "na": "4444", "iznos_sa": 5000, "iznos_na": 5000}],
             "kontrola": {"redovni_prihodi": 0, "redovni_troskovi": 5000}}
        rez = self.ov.obracunaj(cfg, m)
        self.assertEqual(rez["status"], "ok", rez)
        self.assertAlmostEqual(self.korak(rez, "= višak meseca"), -5000.0)

    def test_fx_revaluation_of_idle_balance_is_ignored(self) -> None:
        m = copy.deepcopy(self.mesec)
        m["kurs"]["EUR"] = 200.0       # drugačiji kurs, stanje nepromenjeno
        rez = self.ov.obracunaj(self.cfg, m)
        self.assertAlmostEqual(self.korak(rez, "= višak meseca"), 87716.19)

    def test_account_in_scope_without_balance_is_incomplete(self) -> None:
        m = copy.deepcopy(self.mesec)
        del m["racuni"]["2222"]
        self.assertEqual(self.ov.obracunaj(self.cfg, m)["status"], "nepotpuno")

    def test_missing_cross_check_is_incomplete(self) -> None:
        m = copy.deepcopy(self.mesec)
        del m["kontrola"]
        self.assertEqual(self.ov.obracunaj(self.cfg, m)["status"], "nepotpuno")

    def test_cross_check_mismatch_is_reported(self) -> None:
        m = copy.deepcopy(self.mesec)
        m["kontrola"]["redovni_troskovi"] += 20000   # štednja ubrojana kao trošak
        self.assertEqual(self.ov.obracunaj(self.cfg, m)["status"], "kontrola_ne_izlazi")

    def test_transfer_to_unknown_account_is_an_error(self) -> None:
        m = copy.deepcopy(self.mesec)
        m["transferi"].append({"sa": "1111", "na": "8888", "iznos_sa": 1000})
        self.assertEqual(self.ov.obracunaj(self.cfg, m)["status"], "greska")


class SkillContractTests(unittest.TestCase):
    def test_skill_keeps_non_negotiable_rules(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for fragment in (
            "poslednje 4 cifre",
            "Ne upisuj bez izričitog odobrenja",
            "Bez nadzora",
            "proveri_config.py",
            "kontrola_bilansa.py",
            "obracun_viska.py",
            "NEPOTPUNA",
            "obuhvat",
            "putanju do direktorijuma ovog skilla",
            "Ne pretpostavljaj da korisnik ima vault",
            "--potrebe",
            "Spremnost",
            "Zakazani zadatak",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)

    def test_csv_contract_guards_against_formulas(self) -> None:
        text = (SKILL / "assets" / "sablon-izvestaja.md").read_text(encoding="utf-8")
        self.assertIn("Zaštita od formula", text)
        for znak in ("`=`", "`+`", "`-`", "`@`"):
            self.assertIn(znak, text)

    def test_user_readme_explains_setup(self) -> None:
        text = (SKILL / "README.md").read_text(encoding="utf-8")
        for fragment in ("postavi", "Šta je potrebno", "Gde živi config",
                         "ne loguje se u banku"):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)

    def test_bundled_files_contain_no_real_account_data(self) -> None:
        pc = load("proveri_config")
        for path in SKILL.rglob("*"):
            if path.suffix not in {".md", ".yaml"}:
                continue
            with self.subTest(path=path.name):
                self.assertIsNone(pc.RE_DUGI_BROJ.search(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
