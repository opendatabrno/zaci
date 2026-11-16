"""Stažení tabulek MF „Počty dětí a žáků ve školách zřizovaných obcemi“.

Ukládá do složky data/ pod jednotnými názvy:
    RRRR-09-30 Počty dětí a žáků.xlsx      (stav ke dni 30. 9. roku RRRR)
    RRRR Informace o výši prostředků.html  (článek MF s částkou na žáka, RRRR = rok stránky)
Už stažené soubory přeskočí (pokud nepoužiješ --prepsat).

Zdroje:
  - stránky MF „Financování mateřských a základních škol“ po letech
    https://mf.gov.cz/cs/rozpoctova-politika/uzemni-rozpocty/hospodareni-uzemnich-rozpoctu/financovani-materskych-a-zakladnich-skol/RRRR
    Tabulka se stavem k 30. 9. roku R vychází na stránce roku R+1 v článku „Počty dětí
    a žáků ve školách zřizovaných obcemi“. Známé odkazy jsou níže pevně, nové se hledají
    na stránkách posledních let automaticky, takže v dalších letech stačí skript jen spustit.
  - číselník obcí s vazbou na okresy a kraje (volby.gov.cz) -> ciselniky/

Použití:
    python stahni_data.py            # vše, co chybí
    python stahni_data.py --prepsat  # stáhnout znovu
"""
import argparse
import re
import sys
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CISELNIKY = ROOT / "ciselniky"

MF = "https://mf.gov.cz"
STRANKA = MF + "/cs/rozpoctova-politika/uzemni-rozpocty/hospodareni-uzemnich-rozpoctu/financovani-materskych-a-zakladnich-skol/{rok}"
VOLBY = "https://volby.gov.cz/opendata/ps2025/csv_od/"

# rok stavu k 30. 9. -> příloha na mf.gov.cz
ZNAME = {
    2014: "/assets/attachments/Tabulka_2014-09-30_Pocty-deti-a-zaku-ve-skolach-zrizovanych-obcemi.xlsx",
    2015: "/assets/attachments/Tabulka_2015-09-30_Pocty-deti-a-zaku-ve-skolach-zrizovanych-obcemi-k-30-9-2015_2.xlsx",
    2016: "/assets/attachments/Tabulka_2016_Pocty-deti-a-zaku-ve-skolach-zrizovanych-obcemi-k-30-9-2016.xlsx",
    2017: "/assets/attachments/Tabulka_2017_Pocty-deti-a-zaku-ve-skolach-zrizovanych-obcemi-k-30-9-2017.xlsx",
    2018: "/assets/attachments/Tabulka_2018_Pocty-deti-a-zaku-ve-skolach-zrizovanych-obcemi-k-30-09-2018.xlsx",
    2019: "/assets/attachments/Tabulka_2019_Pocty-deti-a-zaku-ve-skolach-zrizovanych-obcemi-k-30-09-2019_v02.xlsx",
    2020: "/assets/attachments/Tabulka_2020_Pocty-deti-a-zaku-ve-skolach-zrizovanych-obcemi-k-30-09-2020.xlsx",
    2021: "/assets/attachments/Tabulka_2021_Pocty-deti-a-zaku-ve-skolach-zrizovanych-obcemi-k-30-09-2021.xlsx",
    2022: "/assets/attachments/2022-09-30_Tabulka-Pocty-deti-a-zaku-ve-skolach-zrizovanych-obcemi.xlsx",
    2023: "/assets/attachments/2023-09-30_Pocty-deti-a-zaku-ve-skolach-zrizovanych-obcemi.xlsx",
    2024: "/assets/attachments/2024-09-30_Pocty-deti-a-zaku-ve-skolach-zrizovanych-obcemi.xlsx",
}
PRVNI_ROK = 2014

HLAVICKY = {"User-Agent": "Mozilla/5.0 (data-zaci)"}


def nazev_souboru(rok):
    return DATA / f"{rok}-09-30 Počty dětí a žáků.xlsx"


def uloz(url, rok, prepsat):
    cil = nazev_souboru(rok)
    if cil.exists() and not prepsat:
        print(f"  {cil.name} už existuje")
        return False
    r = requests.get(url, headers=HLAVICKY, timeout=60)
    r.raise_for_status()
    if r.content[:2] != b"PK":
        raise RuntimeError(f"{url} nevrátil soubor xlsx")
    cil.write_bytes(r.content)
    print(f"  staženo {cil.name} ({len(r.content) // 1024} kB)")
    return True


def najdi_nove(roky_stranek):
    """Projde stránky MF zadaných let a vrátí {rok stavu: url xlsx} pro tabulky počtů dětí a žáků.

    Rok stavu se bere z názvu odkazu nebo souboru („30.9.2025“, „2025-09-30“, „k-30-09-2025“).
    """
    nalezeno = {}
    for rok_stranky in roky_stranek:
        try:
            r = requests.get(STRANKA.format(rok=rok_stranky), headers=HLAVICKY, timeout=60)
        except requests.RequestException as e:
            print(f"  stránka {rok_stranky}: nedostupná ({e})")
            continue
        if r.status_code != 200:
            continue
        clanky = sorted(set(re.findall(
            rf'href="(/cs/[^"]*financovani-materskych-a-zakladnich-skol/{rok_stranky}/pocty-[^"]+)"', r.text)))
        for clanek in clanky:
            html = requests.get(MF + clanek, headers=HLAVICKY, timeout=60).text
            for url, text in re.findall(r'href="(/assets/attachments/[^"]+\.xlsx)"[^>]*>(.*?)</a>', html, re.S):
                popis = re.sub(r"<[^>]+>", " ", text) + " " + url
                m = (re.search(r"30\.\s*9\.\s*(\d{4})", popis) or re.search(r"(\d{4})-09-30", popis)
                     or re.search(r"30-0?9-(\d{4})", popis))
                if m:
                    nalezeno.setdefault(int(m.group(1)), url)
    return nalezeno


def stahni_informace(roky_stranek, prepsat):
    """Články „Informace o výši prostředků, které obce získávají z RUD …“ – částka na žáka.

    Ukládá data/RRRR Informace o výši prostředků.html (RRRR = rok stránky MF). Stránky
    posledních dvou let se stahují vždy znovu: MF v nich předběžný údaj nahrazuje skutečností.
    """
    letos = date.today().year
    for rok_stranky in roky_stranek:
        cil = DATA / f"{rok_stranky} Informace o výši prostředků.html"
        if cil.exists() and not prepsat and rok_stranky < letos - 1:
            continue
        try:
            r = requests.get(STRANKA.format(rok=rok_stranky), headers=HLAVICKY, timeout=60)
        except requests.RequestException as e:
            print(f"  stránka {rok_stranky}: nedostupná ({e})")
            continue
        if r.status_code != 200:
            continue
        clanky = sorted(set(re.findall(
            rf'href="(/cs/[^"]*financovani-materskych-a-zakladnich-skol/{rok_stranky}/informace-o-vysi-[^"]+)"', r.text)))
        if not clanky:
            continue
        html = requests.get(MF + clanky[0], headers=HLAVICKY, timeout=60)
        html.raise_for_status()
        cil.write_bytes(html.content)
        print(f"  staženo {cil.name}")


def stahni_ciselniky():
    CISELNIKY.mkdir(exist_ok=True)
    for jmeno in ("pscoco.csv", "cnumnuts.csv"):
        r = requests.get(VOLBY + jmeno, headers=HLAVICKY, timeout=60)
        r.raise_for_status()
        # volby.gov.cz posílá CRLF; v repozitáři je LF, jinak by každý běh na Linuxu hlásil změnu
        (CISELNIKY / jmeno).write_bytes(r.content.replace(b"\r\n", b"\n"))
    print("  číselníky obcí a okresů aktualizovány")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prepsat", action="store_true", help="stáhnout i soubory, které už existují")
    args = ap.parse_args()
    DATA.mkdir(exist_ok=True)

    print("Známé tabulky MF:")
    for rok, cesta in ZNAME.items():
        uloz(MF + cesta, rok, args.prepsat)

    print("Nové tabulky na stránkách MF:")
    letos = date.today().year
    nove = najdi_nove(range(max(ZNAME) + 1, letos + 2))
    nove = {r: u for r, u in nove.items() if r not in ZNAME and r >= PRVNI_ROK}
    if not nove:
        print("  nic nového")
    for rok, url in sorted(nove.items()):
        uloz(MF + url, rok, args.prepsat)

    print("Částky na žáka (Informace o výši prostředků):")
    stahni_informace(range(PRVNI_ROK + 1, letos + 2), args.prepsat)

    print("Číselníky:")
    try:
        stahni_ciselniky()
    except requests.RequestException as e:
        print(f"  pozor: číselníky se nepodařilo stáhnout ({e}), použijí se uložené")


if __name__ == "__main__":
    sys.exit(main())
