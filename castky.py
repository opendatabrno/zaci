"""Částka na žáka z kritéria „počet dětí a žáků“ v rozpočtovém určení daní (RUD).

Vstup:  data/RRRR Informace o výši prostředků.html (stahni_data.py) – články MF, ve kterých je
        věta typu „… byla pro rok 2025 v částce 20,845 tis. Kč na žáka“.
Výstup: vystup/castka_na_zaka.csv – jeden řádek = rozpočtový rok × příjemce (obce, od 2026 i kraje)

Částka pro rozpočtový rok R se počítá z počtu dětí a žáků k 30. 9. roku R−1 (stav_zaku_k).
Volá se ze zpracuj_data.py, samostatně:
    python castky.py
"""
import html
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
VYSTUP = ROOT / "vystup"
STRANKA = ("https://mf.gov.cz/cs/rozpoctova-politika/uzemni-rozpocty/hospodareni-uzemnich-rozpoctu/"
           "financovani-materskych-a-zakladnich-skol/{rok}")

VETA = re.compile(
    r"(?:pro (?P<prijemce>obce|kraje) )?pro rok (?P<rok>\d{4}) v částce (?:cca )?(?P<castka>\d+(?:,\d+)?) tis\. Kč"
    r" na (?P<prepocteneho>jednoho přepočteného )?žáka")
STAV = re.compile(r"k\s*30\.\s*(?:září|9\.)\s*(?:resp\.\s*31\.\s*10\.\s*)?(\d{4})")


def text_stranky(cesta):
    t = cesta.read_text(encoding="utf-8")
    t = t[t.find("<h1"):]
    t = re.sub(r"<(script|style|nav|footer).*?</\1>", " ", t, flags=re.S)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t)).replace("\xa0", " ")
    return re.sub(r"\s+", " ", t)


def nacti_stranku(cesta):
    rok_stranky = int(cesta.name[:4])
    radky = []
    # každý údaj je ve větě začínající „Na základě …“
    for veta in re.split(r"(?=Na základě )", text_stranky(cesta)):
        m = VETA.search(veta)
        if not m:
            continue
        stav = STAV.search(veta)
        predbezny = bool(re.search(r"predikc|předpokládá", veta))
        radky.append({
            "rok": int(m["rok"]),
            "prijemce": m["prijemce"] or "obce",
            "castka_na_zaka_kc": round(float(m["castka"].replace(",", ".")) * 1000),
            "jednotka": "přepočtený žák" if m["prepocteneho"] else "žák",
            "stav_zaku_k": f"{stav[1]}-09-30" if stav else None,
            "udaj": "předběžný (predikce daní)" if predbezny else "skutečnost (převedené daně za rok)",
            "zdroj": STRANKA.format(rok=rok_stranky),
            "rok_stranky": rok_stranky,
        })
    return radky


def nacti_castky():
    soubory = sorted(DATA.glob("???? Informace o výši prostředků.html"))
    radky = [r for c in soubory for r in nacti_stranku(c)]
    if not radky:
        return pd.DataFrame()
    d = pd.DataFrame(radky)
    # stejný rok na více stránkách: přednost má skutečnost, pak novější stránka
    d["_skutecnost"] = d.udaj.str.startswith("skutečnost")
    d = (d.sort_values(["rok", "prijemce", "_skutecnost", "rok_stranky"])
          .drop_duplicates(["rok", "prijemce"], keep="last")
          .drop(columns=["_skutecnost", "rok_stranky"]))
    d = d.sort_values(["prijemce", "rok"], key=lambda s: s.map({"obce": 0, "kraje": 1}) if s.name == "prijemce" else s)
    obce = d.prijemce.eq("obce") & d.jednotka.eq("žák")
    d["zmena_proti_minulemu_roku"] = d.castka_na_zaka_kc.where(obce).pct_change(fill_method=None).round(4)
    return d.reset_index(drop=True)


def pocet_pro_rud(z):
    """Počet dětí a žáků, za které obec dostává peníze: pocet_rud (od 2023), dřív odhad
    = celkem bez žáků podle § 38 (vzdělávání v zahraničí) a § 34b."""
    odhad = (z.celkem - z.zs_zahranici_38.fillna(0) - z.gym_zahranici_38.fillna(0)
             - z.ms_individualni_34b.fillna(0))
    return z.pocet_rud.fillna(odhad).astype("Int64")


def main(zaci=None):
    """Uloží vystup/castka_na_zaka.csv; když dostane tabulku obcí, doplní počet žáků a objem za ČR."""
    d = nacti_castky()
    if d.empty:
        print("Částky na žáka: žádné stránky v data/, přeskočeno")
        return d
    if zaci is not None:
        # počet pro RUD: sloupec pocet_rud (od 2023), dřív celkem bez žáků podle § 38
        pocty = pocet_pro_rud(zaci).groupby(zaci.rok).sum()
        stav = d.stav_zaku_k.str[:4].astype("Int64")
        pouzit = d.prijemce.eq("obce") & d.jednotka.eq("žák")
        d["pocet_zaku_rud_cr"] = stav.map(pocty).where(pouzit).astype("Int64")
        d["objem_kc_odhad"] = (d.pocet_zaku_rud_cr * d.castka_na_zaka_kc).astype("Int64")
    VYSTUP.mkdir(exist_ok=True)
    d.to_csv(VYSTUP / "castka_na_zaka.csv", index=False, encoding="utf-8-sig")
    print(d.drop(columns=["zdroj"]).to_string(index=False))
    return d


if __name__ == "__main__":
    zaci = pd.read_csv(VYSTUP / "zaci_obce.csv") if (VYSTUP / "zaci_obce.csv").exists() else None
    main(zaci)
    sys.exit(0)
